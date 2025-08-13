from flask import Flask, request, jsonify, send_file, render_template,make_response
import os, re
import tempfile
import zipfile
import shutil
from bs4 import BeautifulSoup
import re
import json
import requests
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
import time
app = Flask(__name__)

# Static config
# BASE_DIR = '/home/jan-israel/dev/webflow_magic/app'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"BASE_DIR: {BASE_DIR}")
STARTER_THEME = os.path.join(BASE_DIR, 'WebflowStarter')
ASSET_FOLDERS = ['css', 'js', 'images', 'videos', 'fonts', 'media', 'documents', 'cms']

@app.route('/')
def index():
    return render_template('index.html')


def fetch_webflow_cms(api_token, site_id):
    """Fetch all CMS collections and items from Webflow API"""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "accept": "application/json", 
        "accept-version": "2.0.0"
    }
    
    
    try:
        # 1. Get all collections
        collections_url = f"https://api.webflow.com/v2/sites/{site_id}/collections"
        collections_res = requests.get(collections_url, headers=headers)
        collections_res.raise_for_status()
        collections = collections_res.json().get("collections", [])
        
        if not collections:
            print("No collections found in this site")
            return None
            
        # 2. Fetch items for each collection
        def fetch_collection_items(collection):
            items_url = f"https://api.webflow.com/v2/collections/{collection['id']}/items"
            items_res = requests.get(items_url, headers=headers)
            items_res.raise_for_status()
            
            return {
                "id": collection["id"],
                "name": collection["displayName"],
                "slug": collection["slug"],
                "fields": [
                    {
                        "id": field["id"],
                        "name": field["displayName"],
                        "slug": field["slug"],
                        "type": field["type"]
                    } 
                    for field in collection.get("fieldDefinitions", [])  # Changed from 'fields'
                ],
                "items": items_res.json().get("items", [])
            }
        
        # 3. Process collections
        cms_data = []
        for collection in collections:
            try:
                cms_data.append(fetch_collection_items(collection))
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"Failed to fetch {collection['displayName']}: {str(e)}")
            
        return cms_data
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"Error fetching CMS data: {str(e)}")
    
    return None


@app.route('/convert', methods=['POST'])
def convert():
    theme_name = request.form.get('theme_name', 'converted-theme')
    webflow_zip = request.files.get('webflow_zip')
    screenshot_file = request.files.get("screenshot")
    include_cms = True
    api_token = request.form.get('api_token', 'a0c4e41f662c0fa945996569e7e9ded64e0c6fd66bca66176e020e2df3910a6a')
    site_id = request.form.get('site_id')
    
    print(f"tokennnn {include_cms} {api_token} {site_id}")
    print(f"Received screenshot_file: {screenshot_file}")
    if not webflow_zip:
        return jsonify({"error": "Missing Webflow ZIP"}), 400

    theme_name = secure_filename(theme_name)
    temp_base = tempfile.mkdtemp()
    zip_path = os.path.join(temp_base, theme_name + ".zip")
    temp_dir = os.path.join(temp_base, 'webflow-temp')
    output_theme = os.path.join(temp_base, theme_name)

    if os.path.exists(output_theme):
        shutil.rmtree(output_theme)

    os.makedirs(output_theme, exist_ok=True)

    # FIRST: Copy the starter theme
    shutil.copytree(STARTER_THEME, output_theme, dirs_exist_ok=True)
    
    # THEN: Handle screenshot upload (this will overwrite any existing screenshot from starter theme)
    screenshot_dest = os.path.join(output_theme, "screenshot.png")  
    
    if screenshot_file and screenshot_file.filename != "":
        # Remove existing screenshot from starter theme if it exists
        if os.path.exists(screenshot_dest):
            os.remove(screenshot_dest)
        screenshot_file.save(screenshot_dest)
        print(f"Custom screenshot uploaded and saved at: {screenshot_dest}")
        print(f"Screenshot file size: {os.path.getsize(screenshot_dest)} bytes")
    else:
        # Only use default if no screenshot was uploaded and none exists
        if not os.path.exists(screenshot_dest):
            default_thumbnail = os.path.join(BASE_DIR, "assets", "screenshot.png")
            if os.path.exists(default_thumbnail):
                print(f"Using default thumbnail: {default_thumbnail}")
                shutil.copy2(default_thumbnail, screenshot_dest)
                print(f"Default thumbnail saved at: {screenshot_dest}")
            else:
                print("Default thumbnail not found!")
        else:
            print("Using screenshot from starter theme")

    # Process Webflow ZIP
    zip_path = os.path.join(temp_base, secure_filename(webflow_zip.filename))
    webflow_zip.save(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Copy assets
    for folder in ASSET_FOLDERS:
        src = os.path.join(temp_dir, folder)
        dest = os.path.join(output_theme, folder)
        if os.path.exists(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
    
    # Process HTML files
    for filename in os.listdir(temp_dir):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(temp_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        for tag in soup.find_all(['script', 'link']):
            src_or_href = tag.get('src') or tag.get('href') or ''
            if any(lib in src_or_href.lower() for lib in ['jquery', 'splide']):
                tag.decompose()

        head = soup.find('head')
        if head:
            cdn_jquery = soup.new_tag('script', src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js')
            splide_css = soup.new_tag('link', rel='stylesheet', href='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css')
            splide_js = soup.new_tag('script', src='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js')
            head.insert(0, cdn_jquery)
            head.append(splide_css)
            head.append(splide_js)

        body = soup.find('body')
        if body:
            original = list(body.contents)
            body.clear()
            body.append(BeautifulSoup('<?php get_header(); ?>', 'html.parser'))
            for item in original:
                body.append(item)
            body.append(BeautifulSoup('<?php get_footer(); ?>', 'html.parser'))
        else:
            soup.insert(0, BeautifulSoup('<?php get_header(); ?>', 'html.parser'))
            soup.append(BeautifulSoup('<?php get_footer(); ?>', 'html.parser'))

        html_str = fix_asset_paths(str(soup))
        out_filename = 'index.php' if filename == 'index.html' else f"page-{os.path.splitext(filename)[0].lower().replace(' ', '-')}.php"
        out_path = os.path.join(output_theme, out_filename)

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html_str)

    components_css_path = os.path.join(output_theme, 'css', 'components.css')
    override_css = '\n.w-section {\n  display: none !important;\n}\n'
    if os.path.exists(components_css_path):
        with open(components_css_path, 'r+', encoding='utf-8') as f:
            existing_css = f.read()
            if '.w-section' not in existing_css:
                f.write(override_css)
    else:
        os.makedirs(os.path.dirname(components_css_path), exist_ok=True)
        with open(components_css_path, 'w', encoding='utf-8') as f:
            f.write(override_css)

    update_style_css_with_theme_name(output_theme, theme_name)

    # Process CMS if requested
    cms_data = None

    if include_cms and api_token and site_id:
        cms_data = fetch_webflow_cms(api_token, site_id)
    else:
        cms_data = extract_webflow_collections(temp_dir)

    if cms_data:
        # Save raw CMS data
        cms_dir = os.path.join(output_theme, 'cms-data')
        os.makedirs(cms_dir, exist_ok=True)
        with open(os.path.join(cms_dir, 'collections.json'), 'w') as f:
            json.dump(cms_data, f, indent=2)
        
        # Create plugin directories
        plugin_dir = os.path.join(output_theme, 'includes', 'plugins', 'webflow-importer')
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Generate plugin files
        plugin_code = generate_plugin_from_template(cms_data, theme_name)
        
        # 1. Save the main plugin file
        plugin_file_path = os.path.join(plugin_dir, 'webflow-importer.php')
        with open(plugin_file_path, 'w', encoding='utf-8') as f:
            f.write(plugin_code)
        
        # 2. Create readme.txt
        readme_content = f"""=== {theme_name} Importer ===
            Contributors: webflow-to-wp
            Tags: webflow, import, cms, migration
            Requires at least: 5.0
            Tested up to: 6.0
            Stable tag: 1.0.0

            == Description ==
            This plugin imports Webflow CMS content into WordPress with progress tracking.

            == Installation ==
            1. Install and activate Advanced Custom Fields
            2. Upload this plugin via WordPress admin
            3. The import will run automatically
            4. Check admin notices for results"""
        
        readme_path = os.path.join(plugin_dir, 'readme.txt')
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        # 3. Create the ZIP archive
        importer_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-importer.zip')
        
        with zipfile.ZipFile(importer_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files with proper relative paths
            zipf.write(plugin_file_path, 'webflow-importer/webflow-importer.php')
            zipf.write(readme_path, 'webflow-importer/readme.txt')
            
            # If you have additional files (like readme.txt), add them like this:
            # readme_path = os.path.join(plugin_dir, 'readme.txt')
            # if os.path.exists(readme_path):
            #     zipf.write(readme_path, 'webflow-importer/readme.txt')
        
        if not os.path.exists(importer_zip_path):
            raise Exception(f"Failed to create ZIP at {importer_zip_path}")
        
        print(f"Successfully created:")
        print(f"Created plugin at: {plugin_dir}")
        print(f"Created ZIP archive at: {importer_zip_path}")

        # Optional: Verify the ZIP was created
        if os.path.exists(importer_zip_path):
            print("ZIP verification: Success")
        else:
            print("ZIP verification: Failed")
        
        # Update readme with progress info
        with open(os.path.join(plugin_dir, 'readme.txt'), 'w') as f:
            f.write(f"=== {theme_name} Importer ===\n")
            f.write("This plugin imports Webflow CMS content into WordPress.\n\n")
            f.write("Features:\n")
            f.write("- Automatic import on activation\n")
            f.write("- Progress tracking during import\n")
            f.write("- Detailed success/error reporting\n\n")
            f.write("Requirements:\n")
            f.write("1. Advanced Custom Fields PRO (recommended) or ACF Free\n")
            f.write("2. WordPress 5.0 or newer\n\n")
            f.write("Installation:\n")
            f.write("1. Install and activate Advanced Custom Fields\n")
            f.write("2. Upload and activate this plugin\n")
            f.write("3. The import will run automatically\n")
            f.write("4. Check admin notices for import results\n\n")
            f.write("Troubleshooting:\n")
            f.write("- If import doesn't run automatically, go to Tools > Webflow Import\n")
            f.write("- Check error logs if you see any issues\n")

        print(f"Created separate importer zip at: {importer_zip_path}")
 
    # 🆕 CREATE AUTO-RESPONSE EMAIL PLUGIN (Always create, auto-installs)
    auto_response_zip = create_auto_response_plugin_files(output_theme, theme_name)
    
    # 🆕 UPDATE FUNCTIONS.PHP FOR AUTO-INSTALLATION  
    update_functions_php_for_auto_plugin_install(output_theme, theme_name, cms_data is not None)

    # Create installation guides
    create_plugin_installation_guide_auto_install(output_theme, theme_name, cms_data is not None)


    final_zip_path = os.path.join(temp_base, theme_name + ".zip")
    shutil.make_archive(final_zip_path.replace(".zip", ""), "zip", output_theme)

    response = make_response(send_file(
        final_zip_path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=theme_name + ".zip"
    ))
    response.headers["X-Temp-Zip-Path"] = final_zip_path

    return response

def create_plugin_installation_guide(output_theme, theme_name, has_cms):
    """
    Create installation guide for all included plugins
    """
    
    installation_guide = f"""
# {theme_name} - Installation Guide

## 📦 Included Plugins

Your converted theme includes the following plugins in the `includes/plugins/` directory:

### 1. 🔄 Webflow Auto-Response Mailer (ALWAYS INCLUDED)
**File:** `webflow-auto-mailer.zip`
**Purpose:** Automatically sends beautiful response emails to contact form submissions

**Features:**
- ✅ Visual email designer with color customization
- ✅ Dynamic variables ({{name}}, {{email}}, {{message}}, etc.)
- ✅ Works with Contact Form 7, Gravity Forms, Formidable Forms
- ✅ Detects custom HTML forms automatically
- ✅ Responsive email templates
- ✅ Test email functionality
- ✅ Logo and branding support

**Installation:**
1. Go to `Plugins > Add New > Upload Plugin`
2. Upload `includes/plugins/webflow-auto-mailer.zip`
3. Activate the plugin
4. Go to `Settings > Auto-Response Mailer` to customize

**Configuration:**
- Customize email subject, header, body, and footer
- Add your logo URL
- Choose colors for header and CTA button
- Use dynamic variables for personalization
- Send test emails to preview

"""

    if has_cms:
        installation_guide += f"""### 2. 📊 {theme_name} CMS Importer (CMS THEMES ONLY)
**File:** `webflow-importer.zip`
**Purpose:** Imports all Webflow CMS collections and creates WordPress custom post types

**Features:**
- ✅ Automatic import on activation
- ✅ Progress tracking
- ✅ Custom post type creation
- ✅ Advanced Custom Fields integration
- ✅ Error handling and reporting

**Installation:**
1. **FIRST:** Install and activate "Advanced Custom Fields" plugin
2. Go to `Plugins > Add New > Upload Plugin`
3. Upload `includes/plugins/webflow-importer.zip`
4. Activate the plugin
5. Import runs automatically - check admin notices for results

**Requirements:**
- Advanced Custom Fields (ACF) plugin
- WordPress 5.0+
- PHP 7.4+

"""

    installation_guide += """
## 🚀 Quick Setup Steps

### Step 1: Theme Installation
1. Upload the theme ZIP to `Appearance > Themes > Add New > Upload Theme`
2. Activate the theme

### Step 2: Plugin Installation
1. **Install Advanced Custom Fields** (if using CMS features)
2. **Install Auto-Response Mailer** (for contact forms)
3. **Install CMS Importer** (if your theme has CMS content)

### Step 3: Configuration
1. **Auto-Response Mailer:**
   - Go to `Settings > Auto-Response Mailer`
   - Customize your email template
   - Test with a sample email

2. **CMS Content:**
   - Check `Tools > Webflow Import` for import status
   - View imported content in the admin menu

### Step 4: Customize
1. Set up menus in `Appearance > Menus`
2. Configure widgets in `Appearance > Widgets`
3. Upload your logo in `Appearance > Customize`

## 🎯 Form Auto-Response Setup

The Auto-Response Mailer works automatically with:

### Contact Form 7
- Install Contact Form 7 plugin
- Create forms normally
- Auto-responses sent automatically

### Gravity Forms
- Install Gravity Forms plugin
- Create forms normally
- Auto-responses sent automatically

### Custom HTML Forms
- No additional setup needed
- Plugin detects email fields automatically
- Works with forms containing:
  - `input[type="email"]`
  - `input[name*="email"]`
  - `input[id*="email"]`

### Form Field Detection
The plugin automatically detects these fields:
- **Email:** email, your-email, user_email, contact_email
- **Name:** name, your-name, user_name, first_name, full_name
- **Message:** message, your-message, comments, inquiry
- **Phone:** phone, telephone, contact_number, your-phone

## 🎨 Email Template Customization

### Available Variables:
- `{{name}}` - Customer's name
- `{{email}}` - Customer's email
- `{{message}}` - Form message
- `{{phone}}` - Phone number
- `{{site_name}}` - Your website name
- `{{year}}` - Current year

### Design Options:
- Header color and text
- Logo URL
- Email body (WYSIWYG editor)
- Call-to-action button
- Footer text
- Custom colors

## 🔧 Troubleshooting

### Auto-Response Not Working?
1. Check if plugin is activated
2. Verify email is enabled in `Settings > Auto-Response Mailer`
3. Test email functionality
4. Check form field names match detected patterns

### CMS Import Issues?
1. Ensure ACF plugin is installed
2. Check `Tools > Webflow Import` for status
3. Look for admin notices after activation
4. Verify JSON data in `cms-data/collections.json`

### Email Not Sending?
1. Check WordPress email configuration
2. Install SMTP plugin if needed
3. Test with different email addresses
4. Check spam folders

## 📞 Support

This theme was automatically converted from Webflow. For technical support:
1. Check WordPress logs for errors
2. Verify plugin compatibility
3. Test in a staging environment first

## 🎉 You're All Set!

Your Webflow theme is now a fully functional WordPress theme with:
- ✅ Responsive design preserved
- ✅ CMS content imported (if applicable)
- ✅ Auto-response emails configured
- ✅ WordPress best practices implemented

Enjoy your new WordPress theme! 🚀
"""

    # Save the installation guide
    guide_path = os.path.join(output_theme, 'INSTALLATION-GUIDE.md')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(installation_guide)
    
    # Also create a simple text version
    simple_guide = f"""
{theme_name} - Quick Setup
=========================

1. INSTALL THEME:
   - Upload theme ZIP to WordPress
   - Activate theme

2. INSTALL PLUGINS:
   - Upload includes/plugins/webflow-auto-mailer.zip
   - Upload includes/plugins/webflow-importer.zip (if CMS theme)
   - Install Advanced Custom Fields plugin first (for CMS)

3. CONFIGURE:
   - Go to Settings > Auto-Response Mailer
   - Customize email templates
   - Test email functionality

4. DONE!
   Your contact forms now send auto-response emails!

For detailed instructions, see INSTALLATION-GUIDE.md
"""
    
    simple_guide_path = os.path.join(output_theme, 'QUICK-SETUP.txt')
    with open(simple_guide_path, 'w', encoding='utf-8') as f:
        f.write(simple_guide)
    
    print(f"📚 Created installation guides:")
    print(f"  - {guide_path}")
    print(f"  - {simple_guide_path}")
    
    return guide_path


def generate_plugin_from_template(collections, theme_name):
    """Generates the importer plugin from template file with progress tracking"""
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-importer.php')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Prepare the JSON data with proper escaping
    collections_json = json.dumps(collections, ensure_ascii=False)
    collections_json = collections_json.replace('\\', '\\\\')
    collections_json = collections_json.replace("'", "\\'")
    collections_json = collections_json.replace('"', '\\"')
    
    # Add auto-import configuration
    auto_import_config = """
    // Auto-import configuration
    define('WF_IMPORT_AUTO_RUN', true);
    define('WF_IMPORT_DEBUG', true);
    """
    
    # Progress tracking and admin notices code
    progress_code = """
    // Progress tracking and admin notices
    add_action('admin_notices', 'webflow_importer_admin_notices');
    function webflow_importer_admin_notices() {
        if ($results = get_transient('webflow_import_results')) {
            echo '<div class="notice notice-'.($results['error'] ? 'error' : 'success').'">';
            if ($results['error']) {
                echo "<p>Import error: ".esc_html($results['message'])."</p>";
            } else {
                foreach ($results['counts'] as $cpt => $count) {
                    echo "<p>Imported $count items to $cpt</p>";
                }
                echo "<p>Total time: ".number_format($results['time'], 2)."s</p>";
            }
            echo '</div>';
            delete_transient('webflow_import_results');
        }
        
        if ($progress = get_transient('webflow_import_progress')) {
            $percent = round(($progress['current'] / $progress['total']) * 100);
            echo '<div class="notice notice-info">';
            echo '<p><strong>Import Progress:</strong> '.$percent.'% complete</p>';
            echo '<div class="progress-bar" style="background:#f1f1f1;height:20px;width:100%">';
            echo '<div style="background:#2271b1;height:100%;width:'.$percent.'%"></div>';
            echo '</div>';
            echo '</div>';
        }
    }
    """
    
    # Import function with progress tracking
    import_function = """
    function webflow_run_auto_import() {
        $start_time = microtime(true);
        $results = ['counts' => [], 'error' => false, 'time' => 0];
        
        try {
            $collections = json_decode('{{COLLECTIONS_JSON}}', true);
            $total = count($collections);
            
            foreach ($collections as $index => $collection) {
                set_transient('webflow_import_progress', [
                    'current' => $index + 1,
                    'total' => $total,
                    'collection' => $collection['slug']
                ], 300);
                
                // Your existing import logic here
                $count = webflow_import_collection($collection);
                
                $results['counts'][$collection['slug']] = $count;
            }
            
            $results['time'] = microtime(true) - $start_time;
            set_transient('webflow_import_results', $results, 60);
            
        } catch (Exception $e) {
            set_transient('webflow_import_results', [
                'error' => true,
                'message' => $e->getMessage(),
                'time' => microtime(true) - $start_time
            ], 60);
        }
        
        delete_transient('webflow_import_progress');
        return $results;
    }
    """
    
    # Activation hook
    activation_code = """
    // Add auto-import trigger
    register_activation_hook(__FILE__, function() {
        update_option('webflow_do_auto_import', true);
    });
    
    add_action('admin_init', function() {
        if (get_option('webflow_do_auto_import')) {
            delete_option('webflow_do_auto_import');
            webflow_run_auto_import();
        }
    });
    """
    
    # Replace placeholders
    plugin_code = template.replace('{{PLUGIN_NAME}}', f'{theme_name} Importer')
    plugin_code = plugin_code.replace('{{COLLECTIONS_JSON}}', collections_json)
    plugin_code = plugin_code.replace('// {{AUTO_IMPORT_CONFIG}}', auto_import_config)
    plugin_code = plugin_code.replace('// {{PROGRESS_TRACKING}}', progress_code)
    plugin_code = plugin_code.replace('// {{IMPORT_FUNCTION}}', import_function)
    plugin_code = plugin_code.replace('// {{ACTIVATION_HOOK}}', activation_code)
    
    return plugin_code


def extract_webflow_collections(webflow_dir):
    """Extracts collection data from Webflow export"""
    collections = []
    cms_dir = os.path.join(webflow_dir, 'cms')
    
    if os.path.exists(cms_dir):
        for collection_file in os.listdir(cms_dir):
            if collection_file.endswith('.json'):
                with open(os.path.join(cms_dir, collection_file), 'r') as f:
                    try:
                        data = json.load(f)
                        collections.append({
                            'name': data.get('name', 'Unnamed'),
                            'slug': data.get('slug', 'unnamed'),
                            'fields': extract_fields(data)
                        })
                    except json.JSONDecodeError:
                        continue
    return collections

def generate_auto_response_email_plugin(theme_name):
    """
    Generate auto-response email plugin with design capabilities
    """
    
    plugin_code = """<?php
/**
 * Plugin Name: {theme_name} Auto-Response Mailer
 * Description: Automatically sends beautiful response emails to contact form submissions with design customization
 * Version: 1.0.0
 * Author: Webflow to WP Converter
 */

// Prevent direct access
if (!defined('ABSPATH')) exit;

class WebflowAutoResponseMailer {{
    
    private $plugin_name = 'webflow_auto_mailer';
    
    public function __construct() {{
        add_action('init', array($this, 'init'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('wp_ajax_save_email_template', array($this, 'save_email_template'));
        add_action('wp_ajax_test_email', array($this, 'test_email'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_action('wp_footer', array($this, 'add_form_interceptor'));
        register_activation_hook(__FILE__, array($this, 'activate_plugin'));
    }}
    
    public function init() {{
        // Hook into various form plugins
        add_action('wpcf7_mail_sent', array($this, 'handle_cf7_submission')); // Contact Form 7
        add_action('gform_after_submission', array($this, 'handle_gravity_submission'), 10, 2); // Gravity Forms
        add_action('frm_after_create_entry', array($this, 'handle_formidable_submission'), 30, 2); // Formidable
        
        // Custom form handler for HTML forms
        add_action('wp_ajax_webflow_form_submit', array($this, 'handle_custom_form'));
        add_action('wp_ajax_nopriv_webflow_form_submit', array($this, 'handle_custom_form'));
    }}
    
    public function activate_plugin() {{
        // Set default email template
        $default_template = array(
            'subject' => 'Thank you for contacting us!',
            'header_color' => '#2271b1',
            'header_text' => 'Thank You!',
            'body' => 'Hi {{name}},<br><br>Thank you for reaching out to us. We have received your message and will get back to you within 24 hours.<br><br>Your message:<br><em>{{message}}</em><br><br>Best regards,<br>{{site_name}} Team',
            'footer_text' => '© {{year}} {{site_name}}. All rights reserved.',
            'button_color' => '#2271b1',
            'button_text' => 'Visit Our Website',
            'button_url' => home_url(),
            'logo_url' => get_site_icon_url()
        );
        
        update_option('webflow_email_template', $default_template);
        update_option('webflow_mailer_enabled', true);
    }}
    
    public function add_admin_menu() {{
        add_options_page(
            'Auto-Response Mailer',
            'Auto-Response Mailer', 
            'manage_options',
            'webflow-auto-mailer',
            array($this, 'admin_page')
        );
    }}
    
    public function admin_page() {{
        $template = get_option('webflow_email_template', array());
        $enabled = get_option('webflow_mailer_enabled', true);
        ?>
        <div class="wrap">
            <h1>Auto-Response Email Designer</h1>
            
            <form method="post" action="options.php">
                <?php settings_fields('webflow_mailer_settings'); ?>
                
                <table class="form-table">
                    <tr>
                        <th scope="row">Enable Auto-Response</th>
                        <td>
                            <label>
                                <input type="checkbox" name="webflow_mailer_enabled" value="1" <?php checked($enabled, 1); ?>>
                                Send auto-response emails
                            </label>
                        </td>
                    </tr>
                </table>
                
                <h2>Email Design</h2>
                
                <div class="email-designer">
                    <div class="design-controls">
                        <table class="form-table">
                            <tr>
                                <th scope="row">Subject Line</th>
                                <td>
                                    <input type="text" name="email_subject" class="regular-text" 
                                           value="<?php echo esc_attr($template['subject'] ?? ''); ?>" 
                                           placeholder="Thank you for contacting us!">
                                    <p class="description">Use {{name}}, {{email}}, {{message}}, {{site_name}} for dynamic content</p>
                                </td>
                            </tr>
                            
                            <tr>
                                <th scope="row">Header Settings</th>
                                <td>
                                    <p>
                                        <label>Header Color: </label>
                                        <input type="color" name="header_color" value="<?php echo esc_attr($template['header_color'] ?? '#2271b1'); ?>">
                                    </p>
                                    <p>
                                        <label>Header Text: </label>
                                        <input type="text" name="header_text" class="regular-text" 
                                               value="<?php echo esc_attr($template['header_text'] ?? ''); ?>" 
                                               placeholder="Thank You!">
                                    </p>
                                    <p>
                                        <label>Logo URL: </label>
                                        <input type="url" name="logo_url" class="regular-text" 
                                               value="<?php echo esc_attr($template['logo_url'] ?? ''); ?>" 
                                               placeholder="https://yoursite.com/logo.png">
                                    </p>
                                </td>
                            </tr>
                            
                            <tr>
                                <th scope="row">Email Body</th>
                                <td>
                                    <?php 
                                    wp_editor(
                                        $template['body'] ?? '', 
                                        'email_body',
                                        array(
                                            'textarea_name' => 'email_body',
                                            'textarea_rows' => 10,
                                            'media_buttons' => false,
                                            'teeny' => true
                                        )
                                    );
                                    ?>
                                    <p class="description">Available variables: {{name}}, {{email}}, {{message}}, {{phone}}, {{site_name}}, {{year}}</p>
                                </td>
                            </tr>
                            
                            <tr>
                                <th scope="row">Call-to-Action Button</th>
                                <td>
                                    <p>
                                        <label>Button Text: </label>
                                        <input type="text" name="button_text" class="regular-text" 
                                               value="<?php echo esc_attr($template['button_text'] ?? ''); ?>" 
                                               placeholder="Visit Our Website">
                                    </p>
                                    <p>
                                        <label>Button URL: </label>
                                        <input type="url" name="button_url" class="regular-text" 
                                               value="<?php echo esc_attr($template['button_url'] ?? ''); ?>" 
                                               placeholder="<?php echo home_url(); ?>">
                                    </p>
                                    <p>
                                        <label>Button Color: </label>
                                        <input type="color" name="button_color" value="<?php echo esc_attr($template['button_color'] ?? '#2271b1'); ?>">
                                    </p>
                                </td>
                            </tr>
                            
                            <tr>
                                <th scope="row">Footer</th>
                                <td>
                                    <input type="text" name="footer_text" class="regular-text" 
                                           value="<?php echo esc_attr($template['footer_text'] ?? ''); ?>" 
                                           placeholder="© {{year}} {{site_name}}. All rights reserved.">
                                </td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="email-preview">
                        <h3>Email Preview</h3>
                        <div id="email-preview-container">
                            <?php echo $this->generate_email_preview($template); ?>
                        </div>
                        
                        <p>
                            <button type="button" class="button" id="refresh-preview">Refresh Preview</button>
                            <button type="button" class="button" id="send-test-email">Send Test Email</button>
                        </p>
                    </div>
                </div>
                
                <?php submit_button('Save Email Template'); ?>
            </form>
        </div>
        
        <style>
        .email-designer {{
            display: flex;
            gap: 30px;
            margin-top: 20px;
        }}
        .design-controls {{
            flex: 1;
        }}
        .email-preview {{
            flex: 1;
            background: #f9f9f9;
            padding: 20px;
            border: 1px solid #ddd;
        }}
        #email-preview-container {{
            background: white;
            padding: 20px;
            border: 1px solid #ccc;
            max-height: 500px;
            overflow-y: auto;
        }}
        </style>
        
        <script>
        jQuery(document).ready(function($) {{
            $('#refresh-preview').click(function() {{
                // Collect form data and update preview
                var formData = {{
                    'action': 'preview_email_template',
                    'subject': $('[name="email_subject"]').val(),
                    'header_color': $('[name="header_color"]').val(),
                    'header_text': $('[name="header_text"]').val(),
                    'body': $('#email_body').val(),
                    'button_text': $('[name="button_text"]').val(),
                    'button_url': $('[name="button_url"]').val(),
                    'button_color': $('[name="button_color"]').val(),
                    'footer_text': $('[name="footer_text"]').val(),
                    'logo_url': $('[name="logo_url"]').val()
                }};
                
                $.post(ajaxurl, formData, function(response) {{
                    $('#email-preview-container').html(response);
                }});
            }});
            
            $('#send-test-email').click(function() {{
                var email = prompt('Enter email address for test:');
                if (email) {{
                    var formData = {{
                        'action': 'test_email',
                        'email': email,
                        'subject': $('[name="email_subject"]').val(),
                        'header_color': $('[name="header_color"]').val(),
                        'header_text': $('[name="header_text"]').val(),
                        'body': $('#email_body').val(),
                        'button_text': $('[name="button_text"]').val(),
                        'button_url': $('[name="button_url"]').val(),
                        'button_color': $('[name="button_color"]').val(),
                        'footer_text': $('[name="footer_text"]').val(),
                        'logo_url': $('[name="logo_url"]').val()
                    }};
                    
                    $.post(ajaxurl, formData, function(response) {{
                        alert('Test email sent!');
                    }});
                }}
            }});
        }});
        </script>
        <?php
    }}
    
    public function generate_email_preview($template) {{
        $preview_data = array(
            'name' => 'John Doe',
            'email' => 'john@example.com',
            'message' => 'This is a sample message from the contact form.',
            'phone' => '+1 (555) 123-4567',
            'site_name' => get_bloginfo('name'),
            'year' => date('Y')
        );
        
        return $this->generate_email_html($template, $preview_data);
    }}
    
    public function generate_email_html($template, $data) {{
        $html = '
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>' . esc_html($template['subject'] ?? '') . '</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .email-container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                .email-header {{ background-color: ' . esc_attr($template['header_color'] ?? '#2271b1') . '; color: white; padding: 30px; text-align: center; }}
                .email-logo {{ max-width: 150px; height: auto; margin-bottom: 10px; }}
                .email-body {{ padding: 30px; line-height: 1.6; color: #333; }}
                .cta-button {{ display: inline-block; background-color: ' . esc_attr($template['button_color'] ?? '#2271b1') . '; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .email-footer {{ background-color: #f8f8f8; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">';
        
        if (!empty($template['logo_url'])) {{
            $html .= '<img src="' . esc_url($template['logo_url']) . '" alt="Logo" class="email-logo"><br>';
        }}
        
        $html .= '<h1>' . esc_html($template['header_text'] ?? 'Thank You!') . '</h1>
                </div>
                
                <div class="email-body">
                    ' . $this->replace_variables($template['body'] ?? '', $data) . '
                    
                    ' . (!empty($template['button_text']) ? 
                        '<p><a href="' . esc_url($template['button_url'] ?? '') . '" class="cta-button">' . esc_html($template['button_text']) . '</a></p>' 
                        : '') . '
                </div>
                
                <div class="email-footer">
                    ' . $this->replace_variables($template['footer_text'] ?? '', $data) . '
                </div>
            </div>
        </body>
        </html>';
        
        return $html;
    }}
    
    public function replace_variables($content, $data) {{
        $replacements = array(
            '{{name}}' => $data['name'] ?? '',
            '{{email}}' => $data['email'] ?? '',
            '{{message}}' => $data['message'] ?? '',
            '{{phone}}' => $data['phone'] ?? '',
            '{{site_name}}' => get_bloginfo('name'),
            '{{year}}' => date('Y')
        );
        
        return str_replace(array_keys($replacements), array_values($replacements), $content);
    }}
    
    public function enqueue_scripts() {{
        wp_enqueue_script('jquery');
        wp_localize_script('jquery', 'webflow_mailer', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('webflow_mailer_nonce')
        ));
    }}
    
    public function add_form_interceptor() {{
        if (!get_option('webflow_mailer_enabled', true)) return;
        ?>
        <script>
        jQuery(document).ready(function($) {{
            // Intercept all form submissions
            $('form').on('submit', function(e) {{
                var form = $(this);
                var emailField = form.find('input[type="email"], input[name*="email"], input[id*="email"]').first();
                var nameField = form.find('input[name*="name"], input[id*="name"], input[type="text"]').first();
                var messageField = form.find('textarea, input[name*="message"], input[id*="message"]').first();
                var phoneField = form.find('input[type="tel"], input[name*="phone"], input[id*="phone"]').first();
                
                if (emailField.length) {{
                    // Send auto-response email
                    $.post(webflow_mailer.ajax_url, {{
                        action: 'webflow_form_submit',
                        email: emailField.val(),
                        name: nameField.val() || 'Valued Customer',
                        message: messageField.val() || 'Thank you for your submission',
                        phone: phoneField.val() || '',
                        nonce: webflow_mailer.nonce
                    }});
                }}
            }});
        }});
        </script>
        <?php
    }}
    
    // Form handlers for different plugins
    public function handle_cf7_submission($contact_form) {{
        $submission = WPCF7_Submission::get_instance();
        if ($submission) {{
            $data = $submission->get_posted_data();
            $this->send_auto_response($data);
        }}
    }}
    
    public function handle_gravity_submission($entry, $form) {{
        $this->send_auto_response($entry);
    }}
    
    public function handle_formidable_submission($entry_id, $form_id) {{
        $entry = FrmEntry::getOne($entry_id);
        $this->send_auto_response($entry);
    }}
    
    public function handle_custom_form() {{
        check_ajax_referer('webflow_mailer_nonce', 'nonce');
        
        $data = array(
            'email' => sanitize_email($_POST['email']),
            'name' => sanitize_text_field($_POST['name']),
            'message' => sanitize_textarea_field($_POST['message']),
            'phone' => sanitize_text_field($_POST['phone'])
        );
        
        $this->send_auto_response($data);
        wp_die();
    }}
    
    public function send_auto_response($form_data) {{
        if (!get_option('webflow_mailer_enabled', true)) return;
        
        // Extract email from various possible field names
        $email = '';
        $possible_email_fields = array('email', 'your-email', 'user_email', 'form_email', 'contact_email');
        foreach ($possible_email_fields as $field) {{
            if (!empty($form_data[$field])) {{
                $email = $form_data[$field];
                break;
            }}
        }}
        
        if (!$email || !is_email($email)) return;
        
        // Extract other data
        $name = '';
        $possible_name_fields = array('name', 'your-name', 'user_name', 'first_name', 'full_name', 'contact_name');
        foreach ($possible_name_fields as $field) {{
            if (!empty($form_data[$field])) {{
                $name = $form_data[$field];
                break;
            }}
        }}
        
        $message = '';
        $possible_message_fields = array('message', 'your-message', 'comments', 'comment', 'inquiry', 'details');
        foreach ($possible_message_fields as $field) {{
            if (!empty($form_data[$field])) {{
                $message = $form_data[$field];
                break;
            }}
        }}
        
        $phone = '';
        $possible_phone_fields = array('phone', 'telephone', 'contact_number', 'your-phone');
        foreach ($possible_phone_fields as $field) {{
            if (!empty($form_data[$field])) {{
                $phone = $form_data[$field];
                break;
            }}
        }}
        
        $template = get_option('webflow_email_template', array());
        $email_data = array(
            'name' => $name ?: 'Valued Customer',
            'email' => $email,
            'message' => $message,
            'phone' => $phone,
            'site_name' => get_bloginfo('name'),
            'year' => date('Y')
        );
        
        $subject = $this->replace_variables($template['subject'] ?? 'Thank you for contacting us!', $email_data);
        $html_body = $this->generate_email_html($template, $email_data);
        
        $headers = array(
            'Content-Type: text/html; charset=UTF-8',
            'From: ' . get_bloginfo('name') . ' <' . get_option('admin_email') . '>'
        );
        
        wp_mail($email, $subject, $html_body, $headers);
    }}
    
    public function test_email() {{
        check_ajax_referer('webflow_mailer_nonce', 'nonce');
        
        $email = sanitize_email($_POST['email']);
        if (!$email) wp_die('Invalid email');
        
        $template = array(
            'subject' => sanitize_text_field($_POST['subject']),
            'header_color' => sanitize_hex_color($_POST['header_color']),
            'header_text' => sanitize_text_field($_POST['header_text']),
            'body' => wp_kses_post($_POST['body']),
            'button_text' => sanitize_text_field($_POST['button_text']),
            'button_url' => esc_url_raw($_POST['button_url']),
            'button_color' => sanitize_hex_color($_POST['button_color']),
            'footer_text' => sanitize_text_field($_POST['footer_text']),
            'logo_url' => esc_url_raw($_POST['logo_url'])
        );
        
        $test_data = array(
            'name' => 'Test User',
            'email' => $email,
            'message' => 'This is a test email from your auto-response system.',
            'phone' => '+1 (555) 123-4567',
            'site_name' => get_bloginfo('name'),
            'year' => date('Y')
        );
        
        $subject = $this->replace_variables($template['subject'], $test_data);
        $html_body = $this->generate_email_html($template, $test_data);
        
        $headers = array(
            'Content-Type: text/html; charset=UTF-8',
            'From: ' . get_bloginfo('name') . ' <' . get_option('admin_email') . '>'
        );
        
        wp_mail($email, $subject, $html_body, $headers);
        wp_die('Test email sent');
    }}
}}

// Initialize the plugin
new WebflowAutoResponseMailer();

// Register settings
add_action('admin_init', function() {{
    register_setting('webflow_mailer_settings', 'webflow_mailer_enabled');
    register_setting('webflow_mailer_settings', 'webflow_email_template');
}});
?>""".format(theme_name=theme_name)
    
    return plugin_code

def generate_auto_response_plugin_from_template(theme_name):
    """
    Generate auto-response email plugin from template file
    """
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-auto-mailer.php')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"❌ Template file not found: {template_path}")
        print("Please create templates/webflow-auto-mailer.php")
        return None
    
    # Replace placeholders
    plugin_code = template.replace('{{PLUGIN_NAME}}', f'{theme_name} Auto-Response Mailer')
    
    return plugin_code


def create_auto_response_plugin_files(output_theme, theme_name):
    """
    Create the auto-response email plugin files using template
    """
    # Create plugin directory
    plugin_dir = os.path.join(output_theme, 'includes', 'plugins', 'webflow-auto-mailer')
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Generate plugin code from template
    plugin_code = generate_auto_response_plugin_from_template(theme_name)
    
    if not plugin_code:
        print("❌ Failed to generate auto-response plugin")
        return None
    
    # Save the main plugin file
    plugin_file_path = os.path.join(plugin_dir, 'webflow-auto-mailer.php')
    with open(plugin_file_path, 'w', encoding='utf-8') as f:
        f.write(plugin_code)
    
    # Create plugin readme
    readme_content = f"""=== {theme_name} Auto-Response Mailer ===
Contributors: webflow-converter
Tags: email, auto-response, contact-form, mailer, automatic
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0

== Description ==
🚀 AUTOMATICALLY INSTALLS WITH YOUR THEME! 🚀

Sends beautiful, customizable response emails to contact form submissions with zero configuration needed.

✨ KEY FEATURES:
* 🎨 Visual email designer with live preview
* 🔄 Auto-detects ALL contact forms (no setup required)
* 📱 Responsive email templates
* 🎯 Dynamic content variables (name, email, message, etc.)
* 🔌 Works with Contact Form 7, Gravity Forms, Formidable, and custom HTML forms
* 📧 Test email functionality
* 🖼️ Logo and branding support
* ⚡ Instant activation - works immediately

🛠️ AUTO-DETECTION:
The plugin automatically finds and responds to any form with email fields:
- input[type="email"]
- input[name*="email"] 
- input[id*="email"]

📊 COMPATIBLE FORMS:
✅ Contact Form 7
✅ Gravity Forms  
✅ Formidable Forms
✅ Custom HTML forms
✅ WPForms
✅ Ninja Forms
✅ Any form with email field

🎨 CUSTOMIZATION:
* Header colors and text
* Email body with WYSIWYG editor
* Call-to-action buttons
* Footer customization
* Logo integration
* Dynamic variables

== Installation ==
✅ AUTO-INSTALLS when you activate your theme!

Manual installation:
1. Upload and activate this plugin
2. Go to Settings > Auto-Response Mailer
3. Customize your email template (optional)
4. That's it! All forms now send auto-responses

== Usage ==
🎯 ZERO CONFIGURATION NEEDED!

The plugin works automatically. To customize:
1. Go to Settings > Auto-Response Mailer
2. Design your email template
3. Use dynamic variables:
   - {{{{name}}}} - Customer's name
   - {{{{email}}}} - Customer's email
   - {{{{message}}}} - Form message
   - {{{{phone}}}} - Phone number
   - {{{{site_name}}}} - Your site name
   - {{{{year}}}} - Current year

== Frequently Asked Questions ==

= Does this work with my contact form? =
Yes! The plugin auto-detects any form with email fields. Works with all major form plugins and custom HTML forms.

= Do I need to configure anything? =
No! It works automatically. Customization is optional through Settings > Auto-Response Mailer.

= Can I customize the email design? =
Absolutely! Full visual designer with colors, logo, buttons, and custom content.

= Will this slow down my site? =
No. The plugin is lightweight and only activates during form submissions.

== Changelog ==
= 1.0.0 =
* 🚀 Initial release with auto-installation
* 🎨 Visual email designer
* 🔄 Multi-form plugin support  
* 📱 Responsive email templates
* ⚡ Auto-detection of contact forms
* 🎯 Zero-configuration setup"""

    readme_path = os.path.join(plugin_dir, 'readme.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Create the ZIP archive
    mailer_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-auto-mailer.zip')
    
    with zipfile.ZipFile(mailer_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(plugin_file_path, 'webflow-auto-mailer/webflow-auto-mailer.php')
        zipf.write(readme_path, 'webflow-auto-mailer/readme.txt')
    
    print(f"✅ Created Auto-Response Email plugin from template: {mailer_zip_path}")
    return mailer_zip_path

# Updated convert function integration
def integrate_auto_install_plugins_in_convert():
    """
    Integration code for your convert() function
    """
    integration_code = """
    # After CMS plugin creation, add auto-response plugin:
    
    if cms_data:
        # [Your existing CMS plugin creation code here]
        print(f"Created CMS importer plugin at: {importer_zip_path}")

    # 🆕 CREATE AUTO-RESPONSE EMAIL PLUGIN (Always create, auto-installs)
    auto_response_zip = create_auto_response_plugin_files(output_theme, theme_name)
    
    # 🆕 UPDATE FUNCTIONS.PHP FOR AUTO-INSTALLATION
    update_functions_php_for_auto_plugin_install(output_theme, theme_name, cms_data is not None)

    # Create installation guides
    create_plugin_installation_guide(output_theme, theme_name, cms_data is not None)

    # Finalize WordPress theme
    finalize_wordpress_theme(output_theme, theme_name)
    """
    return integration_code



def update_functions_php_for_auto_plugin_install(output_theme, theme_name, has_cms=False):
    """
    Update functions.php to auto-install both plugins when theme is activated
    """
    functions_php_path = os.path.join(output_theme, 'functions.php')
    
    theme_slug = theme_name.lower().replace(' ', '_').replace('-', '_')
    
    # Add auto-plugin installation code to functions.php
    auto_install_code = f"""

// Auto-install theme plugins on activation
function {theme_slug}_auto_install_plugins() {{
    // Check if plugins are already installed
    $auto_mailer_installed = is_plugin_active('webflow-auto-mailer/webflow-auto-mailer.php');
    $cms_importer_installed = is_plugin_active('webflow-importer/webflow-importer.php');
    
    $plugins_to_install = array();
    
    // Auto-Response Mailer (always install)
    if (!$auto_mailer_installed) {{
        $plugins_to_install[] = array(
            'name' => '{theme_name} Auto-Response Mailer',
            'zip' => get_template_directory() . '/includes/plugins/webflow-auto-mailer.zip',
            'folder' => 'webflow-auto-mailer',
            'main_file' => 'webflow-auto-mailer/webflow-auto-mailer.php'
        );
    }}
    
    {f'''// CMS Importer (if CMS theme)
    if (!$cms_importer_installed && file_exists(get_template_directory() . '/includes/plugins/webflow-importer.zip')) {{
        $plugins_to_install[] = array(
            'name' => '{theme_name} CMS Importer',
            'zip' => get_template_directory() . '/includes/plugins/webflow-importer.zip',
            'folder' => 'webflow-importer',
            'main_file' => 'webflow-importer/webflow-importer.php'
        );
    }}''' if has_cms else '// No CMS plugin needed'}
    
    // Install plugins
    if (!empty($plugins_to_install)) {{
        require_once ABSPATH . 'wp-admin/includes/file.php';
        require_once ABSPATH . 'wp-admin/includes/misc.php';
        require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
        
        foreach ($plugins_to_install as $plugin) {{
            if (file_exists($plugin['zip'])) {{
                // Install plugin
                $upgrader = new Plugin_Upgrader();
                $result = $upgrader->install($plugin['zip']);
                
                if (!is_wp_error($result)) {{
                    // Activate plugin
                    activate_plugin($plugin['main_file']);
                    
                    // Add success notice
                    set_transient('theme_plugins_installed', true, 60);
                }}
            }}
        }}
    }}
}}

// Auto-install on theme activation
add_action('after_switch_theme', '{theme_slug}_auto_install_plugins');

// Show installation notice
add_action('admin_notices', function() {{
    if (get_transient('theme_plugins_installed')) {{
        echo '<div class="notice notice-success is-dismissible">';
        echo '<p><strong>🎉 Theme Activated Successfully!</strong></p>';
        echo '<p>✅ Auto-Response Email plugin installed and activated</p>';
        {f"echo '<p>✅ CMS Importer plugin installed and activated</p>';" if has_cms else ''}
        echo '<p><a href="' . admin_url('options-general.php?page=webflow-auto-mailer') . '" class="button button-primary">Configure Auto-Response Emails →</a></p>';
        echo '</div>';
        delete_transient('theme_plugins_installed');
    }}
}});

// Add theme support for auto-installing plugins
add_action('admin_init', function() {{
    // Check if we need to show plugin installation links
    if (!is_plugin_active('webflow-auto-mailer/webflow-auto-mailer.php')) {{
        add_action('admin_notices', function() {{
            echo '<div class="notice notice-warning">';
            echo '<p><strong>Install Required Plugins:</strong> ';
            echo '<a href="' . admin_url('plugin-install.php?tab=upload') . '">Upload plugins manually</a> ';
            echo 'from the includes/plugins/ folder in your theme.</p>';
            echo '</div>';
        }});
    }}
}});"""
    
    # Append to existing functions.php
    if os.path.exists(functions_php_path):
        with open(functions_php_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Remove the closing ?> if it exists and add our code
        if existing_content.strip().endswith('?>'):
            existing_content = existing_content.strip()[:-2]
        
        updated_content = existing_content + auto_install_code + "\n?>"
        
        with open(functions_php_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ Updated functions.php with auto-plugin installation code")
    
    return True

    
# Updated installation guide for auto-install
def create_plugin_installation_guide_auto_install(output_theme, theme_name, has_cms):
    """
    Create updated installation guide for auto-installing plugins
    """
    
    installation_guide = f"""
# {theme_name} - AUTO-INSTALL Setup Guide

## 🚀 AUTOMATIC PLUGIN INSTALLATION

Your theme includes **AUTO-INSTALLING PLUGINS** that set up automatically when you activate the theme!

### ✅ What Happens Automatically:

1. **Theme Activation** → Plugins install automatically
2. **Auto-Response Mailer** → Starts working immediately  
3. **Email Templates** → Pre-configured and ready
4. **Form Detection** → All contact forms work instantly

## 📦 Included Auto-Installing Plugins

### 🔄 Auto-Response Email Mailer (ALWAYS INCLUDED)
**Status:** ✅ AUTO-INSTALLS & ACTIVATES
**Purpose:** Sends beautiful response emails to ALL contact form submissions

**What You Get:**
- ✅ Instant auto-response emails (no setup needed)
- ✅ Professional email templates  
- ✅ Works with ANY contact form automatically
- ✅ Visual email designer for customization
- ✅ Logo and branding support

**Customization:** Go to `Settings > Auto-Response Mailer` (optional)

"""

    if has_cms:
        installation_guide += f"""### 📊 {theme_name} CMS Importer (CMS THEMES)
**Status:** ✅ AUTO-INSTALLS & RUNS IMPORT
**Purpose:** Imports all Webflow CMS content automatically

**What You Get:**
- ✅ All CMS collections imported as custom post types
- ✅ Dynamic content replaces static Webflow content  
- ✅ Advanced Custom Fields integration
- ✅ Progress tracking and error reporting

**Requirement:** Advanced Custom Fields plugin (install first)

"""

    installation_guide += """
## ⚡ SUPER QUICK SETUP (2 Minutes)

### Step 1: Upload & Activate Theme (30 seconds)
```
Appearance > Themes > Add New > Upload Theme
→ Upload your theme ZIP
→ Click "Activate"
```

### Step 2: Plugins Auto-Install (30 seconds)  
```
✅ Auto-Response Mailer → Installs automatically
✅ CMS Importer → Installs automatically (if CMS theme)
✅ Success notice appears in admin
```

### Step 3: Test Auto-Response (1 minute)
```
→ Go to Settings > Auto-Response Mailer
→ Click "Send Test Email"  
→ Enter your email
→ Check your inbox! 📧
```

### Step 4: Done! ✅
Your contact forms now send professional auto-response emails automatically!

## 🎯 ZERO-CONFIGURATION FEATURES

### ✅ Contact Form Auto-Detection
Works automatically with:
- **Contact Form 7** - No setup needed
- **Gravity Forms** - No setup needed  
- **Formidable Forms** - No setup needed
- **Custom HTML Forms** - No setup needed
- **WPForms** - No setup needed
- **Any form with email field** - No setup needed

### ✅ Email Field Detection
Automatically finds email fields:
- `input[type="email"]`
- `input[name*="email"]`
- `input[id*="email"]`

### ✅ Data Extraction  
Automatically extracts:
- **Names:** name, your-name, first_name, full_name
- **Messages:** message, your-message, comments, inquiry  
- **Phone:** phone, telephone, contact_number

## 🎨 CUSTOMIZE YOUR EMAILS (Optional)

### Access Designer:
`Settings > Auto-Response Mailer`

### Available Options:
- 🎨 **Header Colors** - Match your brand
- 🖼️ **Logo Upload** - Add your logo  
- ✍️ **Custom Content** - WYSIWYG editor
- 🔘 **CTA Buttons** - Call-to-action buttons
- 📝 **Dynamic Variables** - Personalize emails

### Dynamic Variables:
```
{{name}} - Customer's name
{{email}} - Customer's email  
{{message}} - Form message
{{phone}} - Phone number
{{site_name}} - Your website name
{{year}} - Current year
```

## 🔧 Manual Installation (If Auto-Install Fails)

### Auto-Response Mailer:
1. Go to `Plugins > Add New > Upload Plugin`
2. Upload `includes/plugins/webflow-auto-mailer.zip`
3. Activate plugin
4. Go to `Settings > Auto-Response Mailer`

### CMS Importer (CMS themes only):
1. Install **Advanced Custom Fields** first
2. Upload `includes/plugins/webflow-importer.zip`  
3. Activate plugin
4. Import runs automatically

## 🎉 SUCCESS INDICATORS

### ✅ Everything Working:
- Green success notice after theme activation
- `Settings > Auto-Response Mailer` menu appears
- Test email delivers to your inbox
- Contact form submissions send auto-responses

### 🔍 Troubleshooting:
- **No auto-responses?** Check `Settings > Auto-Response Mailer` is enabled
- **No success notice?** Manually install plugins from `includes/plugins/`
- **Emails not sending?** Test WordPress email with SMTP plugin

## 🚀 You're All Set!

Your Webflow theme is now a **professional WordPress theme** with:
- ✅ **Instant auto-response emails** for ALL contact forms
- ✅ **Professional email templates** with your branding  
- ✅ **Zero configuration** - works immediately
- ✅ **CMS content imported** (if applicable)
- ✅ **WordPress best practices** implemented

**Result:** Every contact form submission now gets a beautiful, professional auto-response email! 🎯

---
*Theme converted by Webflow to WordPress Converter*
"""

    # Save the updated installation guide
    guide_path = os.path.join(output_theme, 'AUTO-INSTALL-GUIDE.md')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(installation_guide)
    
    # Create simple setup card
    setup_card = f"""
🚀 {theme_name} - INSTANT SETUP
===============================

✅ STEP 1: Activate Theme (30 sec)
   Upload ZIP → Activate → Done!

✅ STEP 2: Plugins Auto-Install (30 sec)  
   Auto-Response Mailer → Installs automatically
   CMS Importer → Installs automatically (if CMS)

✅ STEP 3: Test Email (1 min)
   Settings > Auto-Response Mailer → Send Test Email

✅ RESULT: Professional auto-response emails! 📧

TOTAL TIME: 2 MINUTES ⚡

For details, see AUTO-INSTALL-GUIDE.md
"""
    
    setup_card_path = os.path.join(output_theme, 'INSTANT-SETUP.txt')
    with open(setup_card_path, 'w', encoding='utf-8') as f:
        f.write(setup_card)
    
    print(f"📚 Created auto-install guides:")
    print(f"  - {guide_path}")
    print(f"  - {setup_card_path}")
    
    return guide_path


def add_auto_response_to_convert_function():
    """
    Add this to your convert() function after creating the CMS plugin
    """
    code_snippet = """
    # Create Auto-Response Email Plugin
    auto_response_zip = create_auto_response_plugin_files(output_theme, theme_name)
    print(f"Created Auto-Response Email plugin: {auto_response_zip}")
    """
    return code_snippet

    
def extract_fields(collection_data):
    """Extracts field definitions from collection data"""
    fields = []
    for field in collection_data.get('fields', []):
        fields.append({
            'name': field.get('name', 'Unnamed'),
            'slug': field.get('slug', 'unnamed'),
            'type': map_field_type(field.get('type', 'text'))
        })
    return fields

def map_field_type(webflow_type):
    """Maps Webflow field types to ACF field types"""
    mapping = {
        'text': 'text',
        'textarea': 'textarea',
        'richtext': 'wysiwyg',
        'image': 'image',
        'file': 'file',
        'number': 'number',
        'date': 'date_picker',
        'switch': 'true_false',
        'option': 'select'
    }
    return mapping.get(webflow_type, 'text')



    
def update_style_css_with_theme_name(output_theme, theme_name):
    """
    Update style.css with proper WordPress theme header and make it deletable
    """
    style_css_path = os.path.join(output_theme, 'style.css')
    
    # Create proper WordPress theme header
    wordpress_theme_header = f"""/*
Theme Name: {theme_name}
Description: Converted from Webflow to WordPress theme with CMS integration
Version: 1.0.0
Author: Webflow to WP Converter
Author URI: https://yoursite.com
License: GPL v2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html
Text Domain: {theme_name.lower().replace(' ', '-')}
Tags: webflow, responsive, cms, custom-post-types
Requires at least: 5.0
Tested up to: 6.4
Requires PHP: 7.4

This theme was automatically converted from Webflow.
Includes CMS content and Advanced Custom Fields integration.
*/

"""

    if os.path.exists(style_css_path):
        with open(style_css_path, 'r', encoding='utf-8') as f:
            existing_css = f.read()

        # Remove old theme header if exists
        updated_css_content = re.sub(
            r'\/\*[\s\S]*?\*\/',
            '',
            existing_css,
            count=1  # Only remove the first comment block
        ).strip()

        # Add new WordPress theme header
        final_css_content = wordpress_theme_header + "\n" + updated_css_content

        with open(style_css_path, 'w', encoding='utf-8') as f:
            f.write(final_css_content)
        print("style.css updated with proper WordPress theme header.")

    else:
        # Create style.css if it doesn't exist
        with open(style_css_path, 'w', encoding='utf-8') as f:
            f.write(wordpress_theme_header)
        print(f"Created style.css with WordPress theme header at {style_css_path}")

    # Create additional files needed for theme deletion
    create_theme_management_files(output_theme, theme_name)

def create_theme_management_files(output_theme, theme_name):
    """
    Create additional files needed for proper WordPress theme management
    """
    
    # 1. Create functions.php if it doesn't exist
    functions_php_path = os.path.join(output_theme, 'functions.php')
    if not os.path.exists(functions_php_path):
        functions_content = f"""<?php
/**
 * {theme_name} Functions and Definitions
 */

// Prevent direct access
if (!defined('ABSPATH')) exit;

// Theme setup
function {theme_name.lower().replace(' ', '_').replace('-', '_')}_setup() {{
    // Add theme support for various features
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    add_theme_support('html5', array('search-form', 'comment-form', 'comment-list', 'gallery', 'caption'));
    add_theme_support('custom-logo');
    
    // Register navigation menus
    register_nav_menus(array(
        'primary' => __('Primary Menu', '{theme_name.lower().replace(' ', '-')}'),
        'footer' => __('Footer Menu', '{theme_name.lower().replace(' ', '-')}'),
    ));
}}
add_action('after_setup_theme', '{theme_name.lower().replace(' ', '_').replace('-', '_')}_setup');

// Enqueue styles and scripts
function {theme_name.lower().replace(' ', '_').replace('-', '_')}_scripts() {{
    // Main stylesheet
    wp_enqueue_style('{theme_name.lower().replace(' ', '-')}-style', get_stylesheet_uri(), array(), '1.0.0');
    
    // Webflow CSS files
    if (file_exists(get_template_directory() . '/css/normalize.css')) {{
        wp_enqueue_style('{theme_name.lower().replace(' ', '-')}-normalize', get_template_directory_uri() . '/css/normalize.css', array(), '1.0.0');
    }}
    if (file_exists(get_template_directory() . '/css/webflow.css')) {{
        wp_enqueue_style('{theme_name.lower().replace(' ', '-')}-webflow', get_template_directory_uri() . '/css/webflow.css', array(), '1.0.0');
    }}
    if (file_exists(get_template_directory() . '/css/components.css')) {{
        wp_enqueue_style('{theme_name.lower().replace(' ', '-')}-components', get_template_directory_uri() . '/css/components.css', array(), '1.0.0');
    }}
    
    // Webflow JS files
    if (file_exists(get_template_directory() . '/js/webflow.js')) {{
        wp_enqueue_script('{theme_name.lower().replace(' ', '-')}-webflow-js', get_template_directory_uri() . '/js/webflow.js', array('jquery'), '1.0.0', true);
    }}
}}
add_action('wp_enqueue_scripts', '{theme_name.lower().replace(' ', '_').replace('-', '_')}_scripts');

// Widget areas
function {theme_name.lower().replace(' ', '_').replace('-', '_')}_widgets_init() {{
    register_sidebar(array(
        'name'          => __('Sidebar', '{theme_name.lower().replace(' ', '-')}'),
        'id'            => 'sidebar-1',
        'description'   => __('Add widgets here.', '{theme_name.lower().replace(' ', '-')}'),
        'before_widget' => '<section id="%1$s" class="widget %2$s">',
        'after_widget'  => '</section>',
        'before_title'  => '<h2 class="widget-title">',
        'after_title'   => '</h2>',
    ));
}}
add_action('widgets_init', '{theme_name.lower().replace(' ', '_').replace('-', '_')}_widgets_init');

// Add ACF support notice
function {theme_name.lower().replace(' ', '_').replace('-', '_')}_acf_notice() {{
    if (!class_exists('ACF') && current_user_can('activate_plugins')) {{
        echo '<div class="notice notice-warning"><p>';
        echo sprintf(
            __('This theme requires Advanced Custom Fields plugin for full functionality. <a href="%s">Install ACF</a>', '{theme_name.lower().replace(' ', '-')}'),
            admin_url('plugin-install.php?s=Advanced+Custom+Fields&tab=search&type=term')
        );
        echo '</p></div>';
    }}
}}
add_action('admin_notices', '{theme_name.lower().replace(' ', '_').replace('-', '_')}_acf_notice');

// Theme cleanup on switch
function {theme_name.lower().replace(' ', '_').replace('-', '_')}_cleanup() {{
    // Clean up any theme-specific options or data
    delete_option('{theme_name.lower().replace(' ', '-')}_settings');
    
    // Flush rewrite rules
    flush_rewrite_rules();
}}
add_action('switch_theme', '{theme_name.lower().replace(' ', '_').replace('-', '_')}_cleanup');
?>"""
        
        with open(functions_php_path, 'w', encoding='utf-8') as f:
            f.write(functions_content)
        print("Created functions.php for proper theme functionality")

    # 2. Create index.php fallback if it doesn't exist
    index_php_path = os.path.join(output_theme, 'index.php')
    if not os.path.exists(index_php_path):
        index_content = f"""<?php
/**
 * The main template file for {theme_name}
 */

get_header(); ?>

<main id="main" class="site-main">
    <div class="container">
        <?php if (have_posts()) : ?>
            <?php while (have_posts()) : the_post(); ?>
                <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                    <header class="entry-header">
                        <h1 class="entry-title"><?php the_title(); ?></h1>
                    </header>
                    
                    <div class="entry-content">
                        <?php the_content(); ?>
                    </div>
                </article>
            <?php endwhile; ?>
        <?php else : ?>
            <p><?php _e('No content found.', '{theme_name.lower().replace(' ', '-')}'); ?></p>
        <?php endif; ?>
    </div>
</main>

<?php get_footer(); ?>"""
        
        with open(index_php_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print("Created index.php fallback template")

    # 3. Create header.php if it doesn't exist
    header_php_path = os.path.join(output_theme, 'header.php')
    if not os.path.exists(header_php_path):
        header_content = f"""<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">
    <header id="masthead" class="site-header">
        <div class="site-branding">
            <?php
            if (has_custom_logo()) {{
                the_custom_logo();
            }} else {{
                ?>
                <h1 class="site-title"><a href="<?php echo esc_url(home_url('/')); ?>" rel="home"><?php bloginfo('name'); ?></a></h1>
                <?php
            }}
            ?>
        </div>
        
        <nav id="site-navigation" class="main-navigation">
            <?php
            wp_nav_menu(array(
                'theme_location' => 'primary',
                'menu_id'        => 'primary-menu',
                'fallback_cb'    => false,
            ));
            ?>
        </nav>
    </header>"""
        
        with open(header_php_path, 'w', encoding='utf-8') as f:
            f.write(header_content)
        print("Created header.php template")

    # 4. Create footer.php if it doesn't exist
    footer_php_path = os.path.join(output_theme, 'footer.php')
    if not os.path.exists(footer_php_path):
        footer_content = f"""    <footer id="colophon" class="site-footer">
        <div class="site-info">
            <p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?>. <?php _e('Converted from Webflow.', '{theme_name.lower().replace(' ', '-')}'); ?></p>
        </div>
    </footer>
</div><!-- #page -->

<?php wp_footer(); ?>
</body>
</html>"""
        
        with open(footer_php_path, 'w', encoding='utf-8') as f:
            f.write(footer_content)
        print("Created footer.php template")

    # 5. Create README.txt for theme information
    readme_path = os.path.join(output_theme, 'README.txt')
    readme_content = f"""=== {theme_name} ===

Contributors: webflow-converter
Tags: webflow, responsive, cms, custom-post-types
Requires at least: 5.0
Tested up to: 6.4
Requires PHP: 7.4
License: GPL v2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

== Description ==

This theme was automatically converted from Webflow to WordPress.

Features:
* Responsive design
* CMS content integration
* Advanced Custom Fields support
* Custom post types for Webflow collections
* Original Webflow styling preserved

== Installation ==

1. Upload the theme files to the `/wp-content/themes/{theme_name.lower().replace(' ', '-')}` directory
2. Activate the theme through the 'Appearance' screen in WordPress
3. Install and activate Advanced Custom Fields plugin
4. Upload and activate the included Webflow Importer plugin
5. Your CMS content will be automatically imported

== Requirements ==

* Advanced Custom Fields plugin (recommended)
* WordPress 5.0 or higher
* PHP 7.4 or higher

== Support ==

This theme was automatically generated. For support with the conversion process, 
please contact the theme converter administrator.

== Changelog ==

= 1.0.0 =
* Initial release
* Converted from Webflow
* CMS integration added"""

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("Created README.txt for theme documentation")

    # 6. Make sure proper file permissions are set
    try:
        # Set proper permissions for PHP files
        php_files = ['index.php', 'functions.php', 'header.php', 'footer.php']
        for php_file in php_files:
            file_path = os.path.join(output_theme, php_file)
            if os.path.exists(file_path):
                os.chmod(file_path, 0o644)
        
        # Set permissions for the theme directory
        os.chmod(output_theme, 0o755)
        print("Set proper file permissions for WordPress theme")
    except Exception as e:
        print(f"Could not set file permissions: {e}")



# Also add this to your convert function after the theme copy
def finalize_wordpress_theme(output_theme, theme_name):
    """
    Finalize the WordPress theme for proper installation and deletion
    """
    
    # Ensure all necessary WordPress theme files exist
    required_files = {
        'style.css': 'Main stylesheet with theme header',
        'index.php': 'Main template file', 
        'functions.php': 'Theme functions',
        'screenshot.png': 'Theme preview image'
    }
    
    missing_files = []
    for file_name, description in required_files.items():
        file_path = os.path.join(output_theme, file_name)
        if not os.path.exists(file_path):
            missing_files.append(f"{file_name} ({description})")
    
    if missing_files:
        print(f"Warning: Missing required theme files: {', '.join(missing_files)}")
    else:
        print("All required WordPress theme files present")
    
    # Create a proper theme.json file for modern WordPress themes
    theme_json_path = os.path.join(output_theme, 'theme.json')
    theme_json_content = {{
        "version": 2,
        "settings": {{
            "appearanceTools": True,
            "layout": {{
                "contentSize": "1200px",
                "wideSize": "1400px"
            }},
            "typography": {{
                "fontFamilies": [
                    {{
                        "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen-Sans, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif",
                        "name": "System Font",
                        "slug": "system-font"
                    }}
                ]
            }}
        }},
        "templateParts": [],
        "customTemplates": []
    }}
    
    with open(theme_json_path, 'w', encoding='utf-8') as f:
        json.dump(theme_json_content, f, indent=2)
    print("Created theme.json for modern WordPress compatibility")
    
    print(f" Theme '{theme_name}' is now properly configured for WordPress installation and deletion")

    
@app.route("/delete_temp_zip", methods=["POST"])
def delete_temp_zip():
    data = request.get_json()
    zip_path = data.get("zip_path")
    if zip_path and os.path.exists(zip_path):
        os.remove(zip_path)
        return jsonify({"message": "Temporary ZIP deleted."})
    return jsonify({"error": "ZIP file not found."}), 404



def fix_asset_paths(html):
    pattern = re.compile(r'(src|href)="[^"]*((?:' + '|'.join(ASSET_FOLDERS) + r')/([^"/\?#]+))(\?[^\"]*)?"')

    def replacer(match):
        attr, folder_path, raw_filename = match.group(1), match.group(2), match.group(3)
        folder = folder_path.split('/')[0]
        parts = raw_filename.split('.')
        if len(parts) > 2 and re.fullmatch(r'[a-f0-9]{8,}', parts[-2]):
            raw_filename = '.'.join(parts[:-2] + parts[-1:])
        return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{raw_filename}"'

    html = pattern.sub(replacer, html)

    def srcset_replacer(match):
        parts = [p.strip() for p in match.group(1).split(',')]
        new_parts = []
        for part in parts:
            url, size = part.rsplit(' ', 1) if ' ' in part else (part, '')
            folder = url.split('/')[0]
            filename = os.path.basename(url)
            segments = filename.split('.')
            if len(segments) > 2 and re.fullmatch(r'[a-f0-9]{8,}', segments[-2]):
                filename = '.'.join(segments[:-2] + segments[-1:])
            if folder in ASSET_FOLDERS:
                new_url = f'<?php echo get_template_directory_uri(); ?>/{folder}/{filename}'
                new_parts.append(f'{new_url} {size}'.strip())
            else:
                new_parts.append(part)
        return f'srcset="{", ".join(new_parts)}"'

    html = re.sub(r'srcset="([^"]+)"', srcset_replacer, html)

    def custom_data_attr_replacer(match):
        attr, path = match.groups()
        folder = path.split('/')[0]
        filename = os.path.basename(path)
        if folder in ASSET_FOLDERS:
            return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{filename}"'
        return match.group(0)

    html = re.sub(r'(data-poster-url|data-video-urls)="([^"]+)"', custom_data_attr_replacer, html)

    def style_url_replacer(match):
        path = match.group(1)
        folder = path.split('/')[0]
        filename = os.path.basename(path)
        if folder in ASSET_FOLDERS:
            return f'url(<?php echo get_template_directory_uri(); ?>/{folder}/{filename})'
        return match.group(0)

    html = re.sub(
        r'href="([^"]+\.html)"',
        lambda m: 'href="<?php echo site_url(\'/\'); ?>"' if os.path.basename(m.group(1)).lower() == 'index.html'
        else f'href="<?php echo site_url(\'/{os.path.splitext(os.path.basename(m.group(1)))[0]}\'); ?>"',
        html
    )

    # html = re.sub(r'href="([^"]+\.html)"', lambda m: f'href="<?php echo site_url(\'/{os.path.splitext(os.path.basename(m.group(1)))[0]}\'); ?>"', html)
    html = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', style_url_replacer, html)

    html = re.sub(r'<link href="[^"]*splide.min.css[^"]*"[^>]*>',
                  '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css">', html)
    html = re.sub(r'<script src="[^"]*splide.min.js[^"]*"></script>',
                  '<script src="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js"></script>', html)

    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5022, debug=True)
