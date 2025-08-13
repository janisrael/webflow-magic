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


def process_html_files_safe(temp_dir, output_theme):
    """
    Safely process HTML files to avoid PHP syntax errors
    """
    processed_files = []
    
    for filename in os.listdir(temp_dir):
        if not filename.endswith('.html'):
            continue

        try:
            filepath = os.path.join(temp_dir, filename)
            print(f"Processing: {filename}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Remove problematic scripts and links that might cause PHP conflicts
            for tag in soup.find_all(['script', 'link']):
                src_or_href = tag.get('src') or tag.get('href') or ''
                if any(lib in src_or_href.lower() for lib in ['jquery', 'splide']):
                    tag.decompose()

            # Clean up any potentially problematic content
            clean_html_content(soup)

            # Add CDN resources
            head = soup.find('head')
            if head:
                cdn_jquery = soup.new_tag('script', src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js')
                splide_css = soup.new_tag('link', rel='stylesheet', href='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css')
                splide_js = soup.new_tag('script', src='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js')
                head.insert(0, cdn_jquery)
                head.append(splide_css)
                head.append(splide_js)

            # Add WordPress PHP includes
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

            # Convert to string and fix asset paths
            html_str = str(soup)
            html_str = fix_asset_paths_safe(html_str)

            # Generate safe output filename
            out_filename = generate_safe_filename(filename)
            out_path = os.path.join(output_theme, out_filename)

            # Write the file safely
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html_str)
            
            processed_files.append({
                'original': filename,
                'output': out_filename,
                'path': out_path
            })
            
            print(f"Created: {out_filename}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            # Create a basic fallback file
            create_fallback_page(filename, output_theme)
            continue
    
    return processed_files


def clean_html_content(soup):
    """
    Clean HTML content to prevent PHP syntax errors
    """
    # Remove or escape potentially problematic content
    for tag in soup.find_all():
        # Clean attributes that might cause issues
        if tag.attrs:
            for attr_name, attr_value in list(tag.attrs.items()):
                if isinstance(attr_value, str):
                    # Remove or escape problematic characters
                    attr_value = attr_value.replace('<?', '&lt;?')
                    attr_value = attr_value.replace('?>', '?&gt;')
                    tag.attrs[attr_name] = attr_value
        
        # Clean text content
        if tag.string:
            text = str(tag.string)
            # Escape PHP tags in content
            text = text.replace('<?', '&lt;?')
            text = text.replace('?>', '?&gt;')
            tag.string.replace_with(text)


def generate_safe_filename(filename):
    """
    Generate safe PHP filename from HTML filename
    """
    base_name = os.path.splitext(filename)[0]
    
    # Clean the filename
    safe_name = base_name.lower()
    safe_name = re.sub(r'[^a-z0-9\-_]', '-', safe_name)  # Replace special chars with hyphens
    safe_name = re.sub(r'-+', '-', safe_name)  # Remove multiple hyphens
    safe_name = safe_name.strip('-')  # Remove leading/trailing hyphens
    
    # Generate PHP filename
    if filename.lower() == 'index.html':
        return 'index.php'
    else:
        return f"page-{safe_name}.php"


def create_fallback_page(original_filename, output_theme):
    """
    Create a basic fallback page if processing fails
    """
    try:
        base_name = os.path.splitext(original_filename)[0]
        safe_filename = generate_safe_filename(original_filename)
        
        fallback_content = f"""<?php get_header(); ?>

<main id="main" class="site-main">
    <div class="container">
        <div class="error-notice">
            <h1>Page Processing Error</h1>
            <p>There was an issue processing the original Webflow page: <strong>{original_filename}</strong></p>
            <p>This is a fallback page. Please check the original HTML file for syntax issues.</p>
            <p><a href="<?php echo home_url(); ?>">Back to Home</a></p>
        </div>
    </div>
</main>

<style>
.error-notice {{
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 5px;
    padding: 20px;
    margin: 20px 0;
}}
.error-notice h1 {{
    color: #856404;
    margin-top: 0;
}}
</style>

<?php get_footer(); ?>"""
        
        fallback_path = os.path.join(output_theme, safe_filename)
        with open(fallback_path, 'w', encoding='utf-8') as f:
            f.write(fallback_content)
        
        print(f"Created fallback for {original_filename} to {safe_filename}")
        
    except Exception as e:
        print(f"Failed to create fallback for {original_filename}: {e}")


def fix_asset_paths_safe(html):
    """
    Safer version of fix_asset_paths that avoids PHP syntax errors
    """
    try:
        # Fix asset folder paths
        pattern = re.compile(r'(src|href)="[^"]*((?:' + '|'.join(ASSET_FOLDERS) + r')/([^"/\?#]+))(\?[^\"]*)?"')

        def replacer(match):
            try:
                attr, folder_path, raw_filename = match.group(1), match.group(2), match.group(3)
                folder = folder_path.split('/')[0]
                parts = raw_filename.split('.')
                if len(parts) > 2 and re.fullmatch(r'[a-f0-9]{8,}', parts[-2]):
                    raw_filename = '.'.join(parts[:-2] + parts[-1:])
                return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{raw_filename}"'
            except Exception:
                return match.group(0)  # Return original if replacement fails

        html = pattern.sub(replacer, html)

        # Fix srcset attributes
        def srcset_replacer(match):
            try:
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
            except Exception:
                return match.group(0)

        html = re.sub(r'srcset="([^"]+)"', srcset_replacer, html)

        # Fix custom data attributes
        def custom_data_attr_replacer(match):
            try:
                attr, path = match.groups()
                folder = path.split('/')[0]
                filename = os.path.basename(path)
                if folder in ASSET_FOLDERS:
                    return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{filename}"'
                return match.group(0)
            except Exception:
                return match.group(0)

        html = re.sub(r'(data-poster-url|data-video-urls)="([^"]+)"', custom_data_attr_replacer, html)

        # Fix internal page links safely
        def internal_link_replacer(match):
            try:
                href_value = match.group(1)
                if href_value.lower() == 'index.html':
                    return 'href="<?php echo home_url(\'/\'); ?>"'
                else:
                    page_slug = os.path.splitext(os.path.basename(href_value))[0]
                    # Clean the slug
                    page_slug = re.sub(r'[^a-z0-9\-_]', '-', page_slug.lower())
                    page_slug = re.sub(r'-+', '-', page_slug).strip('-')
                    return f'href="<?php echo home_url(\'/{page_slug}/\'); ?>"'
            except Exception:
                return match.group(0)

        html = re.sub(r'href="([^"]+\.html)"', internal_link_replacer, html)

        # Fix CSS url() references
        def style_url_replacer(match):
            try:
                path = match.group(1)
                folder = path.split('/')[0]
                filename = os.path.basename(path)
                if folder in ASSET_FOLDERS:
                    return f'url(<?php echo get_template_directory_uri(); ?>/{folder}/{filename})'
                return match.group(0)
            except Exception:
                return match.group(0)

        html = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', style_url_replacer, html)

        # Replace CDN links
        html = re.sub(r'<link href="[^"]*splide.min.css[^"]*"[^>]*>',
                      '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css">', html)
        html = re.sub(r'<script src="[^"]*splide.min.js[^"]*"></script>',
                      '<script src="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js"></script>', html)

        return html

    except Exception as e:
        print(f"Error in fix_asset_paths_safe: {e}")
        return html  # Return original HTML if processing fails


def extract_webflow_pages(webflow_temp_dir):
    """
    Extract all pages from Webflow export and prepare data for WordPress page creation
    """
    pages_data = []
    
    for filename in os.listdir(webflow_temp_dir):
        if not filename.endswith('.html'):
            continue
            
        filepath = os.path.join(webflow_temp_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            # Extract page information
            page_title = ""
            page_slug = ""
            meta_description = ""
            
            # Get title from <title> tag or <h1>
            title_tag = soup.find('title')
            if title_tag:
                page_title = title_tag.get_text().strip()
            else:
                h1_tag = soup.find('h1')
                if h1_tag:
                    page_title = h1_tag.get_text().strip()
                else:
                    page_title = os.path.splitext(filename)[0].replace('-', ' ').title()
            
            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                meta_description = meta_desc.get('content', '')
            
            # Generate slug from filename
            base_name = os.path.splitext(filename)[0].lower().replace(' ', '-')
            page_slug = base_name if base_name != 'index' else 'home'
            
            # Determine template file name
            template_name = 'index.php' if filename == 'index.html' else f"page-{base_name}.php"
            
            # Check if this should be the front page
            is_front_page = filename.lower() == 'index.html'
            
            pages_data.append({
                'filename': filename,
                'title': page_title,
                'slug': page_slug,
                'template': template_name,
                'meta_description': meta_description,
                'is_front_page': is_front_page,
                'content': f'<!-- Content will be loaded from {template_name} -->'
            })
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    return pages_data


def generate_page_creator_plugin_from_template(pages_data, theme_name):
    """
    Generate page creator plugin from template file
    """
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-page-creator.php')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
        print("Please create templates/webflow-page-creator.php")
        return None
    
    # Prepare the JSON data with safe escaping
    pages_json = json.dumps(pages_data, ensure_ascii=True, separators=(',', ':'))
    pages_json = pages_json.replace('\\', '\\\\').replace("'", "\\'")
    
    # Replace placeholders in template
    plugin_code = template.replace('{{PLUGIN_NAME}}', f'{theme_name} Auto Page Creator')
    plugin_code = plugin_code.replace('{{PAGES_JSON}}', pages_json)
    
    return plugin_code


def create_page_creator_plugin_files_template(output_theme, theme_name, pages_data):
    """
    Create the auto-page creator plugin files using template approach
    """
    # Create plugin directory
    plugin_dir = os.path.join(output_theme, 'includes', 'plugins', 'webflow-page-creator')
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Debug pages data before processing
    print(f"Processing {len(pages_data)} pages for creation:")
    for i, page in enumerate(pages_data[:3]):  # Show first 3 for debugging
        print(f"   {i+1}. {page.get('title', 'No title')} ({page.get('slug', 'No slug')})")
    if len(pages_data) > 3:
        print(f"   ... and {len(pages_data) - 3} more pages")
    
    # Generate plugin code from template
    plugin_code = generate_page_creator_plugin_from_template(pages_data, theme_name)
    
    if not plugin_code:
        print("Failed to generate page creator plugin from template")
        return None
    
    # Save the main plugin file
    plugin_file_path = os.path.join(plugin_dir, 'webflow-page-creator.php')
    with open(plugin_file_path, 'w', encoding='utf-8') as f:
        f.write(plugin_code)
    
    # Create plugin readme
    readme_content = f"""=== {theme_name} Auto Page Creator ===
Contributors: webflow-converter
Tags: pages, auto-create, webflow, automation
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0

== Description ==
Automatically creates WordPress pages for all your converted Webflow pages.

== Installation ==
Auto-installs when you activate your theme.

== Usage ==
Pages are created automatically on theme activation.
Check Tools > Webflow Pages for status.

== Changelog ==
= 1.0.0 =
* Initial release"""

    readme_path = os.path.join(plugin_dir, 'readme.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Create the ZIP archive
    page_creator_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-page-creator.zip')
    
    with zipfile.ZipFile(page_creator_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(plugin_file_path, 'webflow-page-creator/webflow-page-creator.php')
        zipf.write(readme_path, 'webflow-page-creator/readme.txt')
    
    print(f"Created Page Creator plugin from template: {page_creator_zip_path}")
    
    # Debug output for pages
    print(f"Pages to be created:")
    for page in pages_data:
        print(f"   - {page['title']} ({page['slug']}) -> {page.get('template', 'default template')}")
    
    return page_creator_zip_path


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
        if os.path.exists(screenshot_dest):
            os.remove(screenshot_dest)
        screenshot_file.save(screenshot_dest)
        print(f"Custom screenshot uploaded and saved at: {screenshot_dest}")
        print(f"Screenshot file size: {os.path.getsize(screenshot_dest)} bytes")
    else:
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
    
    # Extract Webflow pages data for auto-creation
    pages_data = extract_webflow_pages(temp_dir)
    print(f"Detected {len(pages_data)} pages for auto-creation: {[p['title'] for p in pages_data]}")
    
    # Copy assets
    for folder in ASSET_FOLDERS:
        src = os.path.join(temp_dir, folder)
        dest = os.path.join(output_theme, folder)
        if os.path.exists(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
    
    # SAFE HTML PROCESSING (prevents PHP syntax errors)
    processed_files = process_html_files_safe(temp_dir, output_theme)
    print(f"Processed {len(processed_files)} HTML files successfully")
    
    # Update pages_data to include only successfully processed files
    if processed_files:
        processed_filenames = [f['original'] for f in processed_files]
        pages_data = [page for page in pages_data if page.get('filename') in processed_filenames]
        print(f"{len(pages_data)} pages ready for WordPress creation")

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

    # CREATE CMS IMPORTER PLUGIN (if CMS data exists)
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
        readme_content = f"""=== {theme_name} CMS Importer ===
Contributors: webflow-to-wp
Tags: webflow, import, cms, migration, auto-import
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0

== Description ==
Automatically imports Webflow CMS content into WordPress.

== Installation ==
Auto-installs when you activate your theme.

== Usage ==
CMS import runs automatically on plugin activation.

== Requirements ==
* Advanced Custom Fields (recommended)
* WordPress 5.0 or newer
* PHP 7.4 or newer

== Changelog ==
= 1.0.0 =
* Initial release"""
        
        readme_path = os.path.join(plugin_dir, 'readme.txt')
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        # 3. Create the ZIP archive
        importer_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-importer.zip')
        
        with zipfile.ZipFile(importer_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(plugin_file_path, 'webflow-importer/webflow-importer.php')
            zipf.write(readme_path, 'webflow-importer/readme.txt')
        
        print(f"Created CMS importer: {importer_zip_path}")
        
        # Verify collections data for debugging
        print(f"CMS Collections to import: {len(cms_data)}")
        for collection in cms_data:
            collection_name = collection.get('name', collection.get('slug', 'Unknown'))
            item_count = len(collection.get('items', []))
            print(f"   - {collection_name}: {item_count} items")
    else:
        print("No CMS data found - skipping CMS importer creation")

    # CREATE AUTO PAGE CREATOR PLUGIN (Template-based)
    if pages_data:
        page_creator_zip = create_page_creator_plugin_files_template(output_theme, theme_name, pages_data)
        if page_creator_zip:
            print(f"Created Template-based Page Creator plugin: {page_creator_zip}")
        else:
            print("Failed to create Page Creator plugin - check template file exists")
    else:
        print("No pages data found - skipping Page Creator plugin")
    
    # CREATE AUTO-RESPONSE EMAIL PLUGIN (Always create, auto-installs)
    auto_response_zip = create_auto_response_plugin_files(output_theme, theme_name)
    if auto_response_zip:
        print(f"Created Auto-Response Email plugin: {auto_response_zip}")
    else:
        print("Failed to create Auto-Response Email plugin")
    
    # UPDATE FUNCTIONS.PHP FOR AUTO-INSTALLATION (Updated to include page creator)
    update_functions_php_for_auto_plugin_install_with_pages(
        output_theme, 
        theme_name, 
        cms_data is not None, 
        len(pages_data) > 0 if pages_data else False
    )

    # Create installation guides
    create_plugin_installation_guide_auto_install_with_pages(
        output_theme, 
        theme_name, 
        cms_data is not None, 
        len(pages_data) > 0 if pages_data else False
    )

    # Final theme packaging
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


# Updated installation guide to include auto page creation
def create_plugin_installation_guide_auto_install_with_pages(output_theme, theme_name, has_cms, has_pages):
    """
    Create updated installation guide for auto-installing plugins including page creator
    """
    
    installation_guide = f"""
# {theme_name} - AUTO-INSTALL Setup Guide

## AUTOMATIC PLUGIN INSTALLATION + PAGE CREATION

Your theme includes 3 AUTO-INSTALLING PLUGINS that set up everything automatically when you activate the theme!

### What Happens Automatically:

1. Theme Activation - All plugins install automatically
2. WordPress Pages - Created automatically from Webflow pages  
3. Auto-Response Mailer - Starts working immediately  
4. CMS Content - Imported automatically (if applicable)
5. Email Templates - Pre-configured and ready
6. Form Detection - All contact forms work instantly

## Included Auto-Installing Plugins

### Auto Page Creator (ALWAYS INCLUDED)
Status: AUTO-INSTALLS & CREATES PAGES
Purpose: Automatically creates WordPress pages for all Webflow pages

What You Get:
- All Webflow pages become WordPress pages instantly
- Correct page templates assigned automatically
- Front page (index.html) set up automatically
- SEO-friendly URLs and meta descriptions
- Zero manual page creation needed

### Auto-Response Email Mailer (ALWAYS INCLUDED)
Status: AUTO-INSTALLS & ACTIVATES
Purpose: Sends beautiful response emails to ALL contact form submissions

What You Get:
- Instant auto-response emails (no setup needed)
- Professional email templates  
- Works with ANY contact form automatically
- Visual email designer for customization
- Logo and branding support

Customization: Go to Settings > Auto-Response Mailer (optional)

"""

    if has_cms:
        installation_guide += f"""### {theme_name} CMS Importer (CMS THEMES)
Status: AUTO-INSTALLS & RUNS IMPORT
Purpose: Imports all Webflow CMS content automatically

What You Get:
- All CMS collections imported as custom post types
- Dynamic content replaces static Webflow content  
- Advanced Custom Fields integration
- Progress tracking and error reporting

Requirement: Advanced Custom Fields plugin (install first)

"""

    installation_guide += """
## SUPER QUICK SETUP (2 Minutes)

### Step 1: Upload & Activate Theme (30 seconds)
Appearance > Themes > Add New > Upload Theme
Upload your theme ZIP
Click "Activate"

### Step 2: Everything Auto-Installs (60 seconds)  
Auto Page Creator - Creates all WordPress pages automatically
Auto-Response Mailer - Installs automatically
CMS Importer - Installs automatically (if CMS theme)
Success notice appears in admin

### Step 3: Verify Pages Created (30 seconds)
Go to Pages > All Pages
See all your Webflow pages now in WordPress!
Check Tools > Webflow Pages for status

### Step 4: Test Auto-Response (30 seconds)
Go to Settings > Auto-Response Mailer
Click "Send Test Email"  
Enter your email
Check your inbox!

### Step 5: Done!
Your complete WordPress site is ready with:
- All pages created automatically
- Contact forms sending professional auto-responses
- CMS content imported (if applicable)

## ZERO-CONFIGURATION FEATURES

### Automatic Page Creation
WordPress pages created automatically:
- index.html - Home page (set as front page)
- about.html - About page (/about/)
- contact.html - Contact page (/contact/)
- services.html - Services page (/services/)
- Any-page.html - WordPress page (/any-page/)

### Smart Template Assignment
- about.html uses page-about.php template
- contact.html uses page-contact.php template  
- Automatic template matching for all pages

### SEO Preservation
- Page titles preserved from Webflow
- Meta descriptions maintained
- Clean, SEO-friendly URLs

### Contact Form Auto-Detection
Works automatically with:
- Contact Form 7 - No setup needed
- Gravity Forms - No setup needed  
- Formidable Forms - No setup needed
- Custom HTML Forms - No setup needed
- Any form with email field - No setup needed

## You're All Set!

Your Webflow theme is now a complete WordPress website with:
- All pages created automatically - No manual page creation needed
- Instant auto-response emails for ALL contact forms
- Professional email templates with your branding  
- Zero configuration - works immediately
- CMS content imported (if applicable)
- WordPress best practices implemented

Result: A fully functional WordPress website that mirrors your Webflow design with enhanced functionality!

Theme converted by Webflow to WordPress Converter with Auto Page Creation
"""

    # Save the updated installation guide
    guide_path = os.path.join(output_theme, 'AUTO-INSTALL-GUIDE.md')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(installation_guide)
    
    # Create simple setup card
    setup_card = f"""
{theme_name} - INSTANT SETUP
===============================

STEP 1: Activate Theme (30 sec)
   Upload ZIP - Activate - Done!

STEP 2: Everything Auto-Installs (60 sec)  
   WordPress pages created automatically
   Auto-Response Mailer installed
   CMS Importer installed (if CMS)

STEP 3: Verify (30 sec)
   Pages > All Pages - See all your pages!
   Settings > Auto-Response Mailer - Test email

RESULT: Complete WordPress site ready!

TOTAL TIME: 2 MINUTES

For details, see AUTO-INSTALL-GUIDE.md
"""
    
    setup_card_path = os.path.join(output_theme, 'INSTANT-SETUP.txt')
    with open(setup_card_path, 'w', encoding='utf-8') as f:
        f.write(setup_card)
    
    print(f"Created auto-install guides (with page creation):")
    print(f"  - {guide_path}")
    print(f"  - {setup_card_path}")
    
    return guide_path


def generate_plugin_from_template(collections, theme_name):
    """Generates the importer plugin from template file with progress tracking"""
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-importer.php')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
        return generate_basic_cms_plugin(collections, theme_name)
    
    # Prepare the JSON data with proper escaping
    collections_json = json.dumps(collections, ensure_ascii=False)
    collections_json = collections_json.replace('\\', '\\\\')
    collections_json = collections_json.replace("'", "\\'")
    collections_json = collections_json.replace('"', '\\"')
    
    # Replace placeholders
    plugin_code = template.replace('{{PLUGIN_NAME}}', f'{theme_name} CMS Importer')
    plugin_code = plugin_code.replace('{{COLLECTIONS_JSON}}', collections_json)
    
    return plugin_code


def generate_basic_cms_plugin(collections, theme_name):
    """
    Fallback: Generate basic CMS plugin if template doesn't exist
    """
    collections_json = json.dumps(collections, ensure_ascii=True, separators=(',', ':'))
    collections_json = collections_json.replace('\\', '\\\\').replace("'", "\\'")
    
    # Basic plugin without template - minimal working version
    plugin_code = f"""<?php
/**
 * Plugin Name: {theme_name} CMS Importer
 * Description: Imports Webflow CMS content into WordPress
 * Version: 1.0.0
 */

if (!defined('ABSPATH')) exit;

class WebflowCMSImporter {{
    private $collections_data;
    
    public function __construct() {{
        $this->collections_data = json_decode('{collections_json}', true);
        add_action('admin_menu', array($this, 'add_admin_menu'));
        register_activation_hook(__FILE__, array($this, 'activate_plugin'));
    }}
    
    public function activate_plugin() {{
        update_option('webflow_cms_auto_import_needed', true);
        update_option('webflow_cms_collections_data', $this->collections_data);
    }}
    
    public function add_admin_menu() {{
        add_management_page('Webflow Import', 'Webflow Import', 'manage_options', 'webflow-import', array($this, 'admin_page'));
    }}
    
    public function admin_page() {{
        echo '<div class="wrap"><h1>Webflow CMS Importer</h1>';
        echo '<p>CMS collections ready for import.</p>';
        echo '<button onclick="alert(\'Import functionality needs full template\')">Import Now</button>';
        echo '</div>';
    }}
}}

new WebflowCMSImporter();
?>"""
    
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


def generate_auto_response_plugin_from_template(theme_name):
    """
    Generate auto-response email plugin from template file
    """
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-auto-mailer.php')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
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
        print("Failed to generate auto-response plugin")
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
Sends beautiful, customizable response emails to contact form submissions.

== Installation ==
Auto-installs when you activate your theme.

== Usage ==
Configure through Settings > Auto-Response Mailer.

== Changelog ==
= 1.0.0 =
* Initial release"""

    readme_path = os.path.join(plugin_dir, 'readme.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Create the ZIP archive
    mailer_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-auto-mailer.zip')
    
    with zipfile.ZipFile(mailer_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(plugin_file_path, 'webflow-auto-mailer/webflow-auto-mailer.php')
        zipf.write(readme_path, 'webflow-auto-mailer/readme.txt')
    
    print(f"Created Auto-Response Email plugin from template: {mailer_zip_path}")
    return mailer_zip_path


def update_functions_php_for_auto_plugin_install_with_pages(output_theme, theme_name, has_cms=False, has_pages=True):
    """
    Updated version that includes auto page creator plugin
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
    $page_creator_installed = is_plugin_active('webflow-page-creator/webflow-page-creator.php');
    
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
    
    {f'''// Auto Page Creator (always install)
    if (!$page_creator_installed && file_exists(get_template_directory() . '/includes/plugins/webflow-page-creator.zip')) {{
        $plugins_to_install[] = array(
            'name' => '{theme_name} Page Creator',
            'zip' => get_template_directory() . '/includes/plugins/webflow-page-creator.zip',
            'folder' => 'webflow-page-creator',
            'main_file' => 'webflow-page-creator/webflow-page-creator.php'
        );
    }}''' if has_pages else '// No page creator needed'}
    
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
        echo '<p><strong>Theme Activated Successfully!</strong></p>';
        echo '<p>Auto-Response Email plugin installed and activated</p>';
        {f"echo '<p>Auto Page Creator plugin installed and activated</p>';" if has_pages else ''}
        {f"echo '<p>CMS Importer plugin installed and activated</p>';" if has_cms else ''}
        echo '<p><a href="' . admin_url('options-general.php?page=webflow-auto-mailer') . '" class="button button-primary">Configure Auto-Response Emails</a></p>';
        {f"echo '<p><a href=\"' . admin_url('tools.php?page=webflow-pages') . '\" class=\"button\">View Created Pages</a></p>';" if has_pages else ''}
        echo '</div>';
        delete_transient('theme_plugins_installed');
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
        
        print("Updated functions.php with auto-plugin installation (including page creator)")
    
    return True


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

    html = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', style_url_replacer, html)

    html = re.sub(r'<link href="[^"]*splide.min.css[^"]*"[^>]*>',
                  '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css">', html)
    html = re.sub(r'<script src="[^"]*splide.min.js[^"]*"></script>',
                  '<script src="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js"></script>', html)

    return html


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5022, debug=True)