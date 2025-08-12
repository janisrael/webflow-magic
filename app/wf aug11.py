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
    include_cms = request.form.get('enable_cms') == 'on'
    api_token = request.form.get('api_token', 'a0c4e41f662c0fa945996569e7e9ded64e0c6fd66bca66176e020e2df3910a6a')
    site_id = request.form.get('site_id')
    custom_selectors = request.form.get('custom_selectors', '')  # Get custom selectors
    
    print(f"CMS enabled: {include_cms}, API Token: {api_token}, Site ID: {site_id}")
    print(f"Custom selectors: {custom_selectors}")
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
    
    # THEN: Handle screenshot upload
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
    
    # Copy assets
    for folder in ASSET_FOLDERS:
        src = os.path.join(temp_dir, folder)
        dest = os.path.join(output_theme, folder)
        if os.path.exists(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)

    # Process CMS if requested (BEFORE HTML processing so we have CMS data available)
    cms_data = None
    if include_cms and api_token and site_id:
        cms_data = fetch_webflow_cms(api_token, site_id)
    else:
        cms_data = extract_webflow_collections(temp_dir)

    # Process HTML files with CMS injection
    for filename in os.listdir(temp_dir):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(temp_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Remove old jQuery/Splide
        for tag in soup.find_all(['script', 'link']):
            src_or_href = tag.get('src') or tag.get('href') or ''
            if any(lib in src_or_href.lower() for lib in ['jquery', 'splide']):
                tag.decompose()

        # Add new CDN links
        head = soup.find('head')
        if head:
            cdn_jquery = soup.new_tag('script', src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js')
            splide_css = soup.new_tag('link', rel='stylesheet', href='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css')
            splide_js = soup.new_tag('script', src='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js')
            head.insert(0, cdn_jquery)
            head.append(splide_css)
            head.append(splide_js)

        # INJECT CMS CONTENT HERE with custom selectors
        if cms_data and include_cms:
            soup = inject_cms_content(soup, cms_data, custom_selectors)

        # Add WordPress header/footer
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

    # Add components CSS override
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

    # Save CMS data and create plugin
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
        
        # Save the main plugin file
        plugin_file_path = os.path.join(plugin_dir, 'webflow-importer.php')
        with open(plugin_file_path, 'w', encoding='utf-8') as f:
            f.write(plugin_code)
        
        # Create readme.txt
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
        
        # Create the ZIP archive
        importer_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-importer.zip')
        
        with zipfile.ZipFile(importer_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(plugin_file_path, 'webflow-importer/webflow-importer.php')
            zipf.write(readme_path, 'webflow-importer/readme.txt')
        
        print(f"Created separate importer zip at: {importer_zip_path}")

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


@app.route('/delete-theme', methods=['POST'])
def delete_theme():
    """Delete theme files from server"""
    data = request.get_json()
    theme_name = data.get('theme_name', '').strip()
    
    if not theme_name:
        return jsonify({"success": False, "error": "Theme name is required"}), 400
    
    theme_name = secure_filename(theme_name)
    
    # Check multiple possible locations for the theme
    possible_locations = [
        os.path.join(BASE_DIR, 'generated_themes', theme_name),
        os.path.join(BASE_DIR, 'themes', theme_name),
        os.path.join(BASE_DIR, theme_name),
        os.path.join('/tmp', theme_name),  # temp directories
    ]
    
    deleted_locations = []
    errors = []
    
    # Also check for ZIP files
    possible_zip_locations = [
        os.path.join(BASE_DIR, 'generated_themes', theme_name + '.zip'),
        os.path.join(BASE_DIR, 'themes', theme_name + '.zip'),
        os.path.join(BASE_DIR, theme_name + '.zip'),
        os.path.join('/tmp', theme_name + '.zip'),
    ]
    
    # Delete theme directories
    for location in possible_locations:
        try:
            if os.path.exists(location) and os.path.isdir(location):
                shutil.rmtree(location)
                deleted_locations.append(location)
                print(f"Deleted theme directory: {location}")
        except Exception as e:
            errors.append(f"Error deleting {location}: {str(e)}")
    
    # Delete ZIP files
    for zip_location in possible_zip_locations:
        try:
            if os.path.exists(zip_location) and os.path.isfile(zip_location):
                os.remove(zip_location)
                deleted_locations.append(zip_location)
                print(f"Deleted theme ZIP: {zip_location}")
        except Exception as e:
            errors.append(f"Error deleting {zip_location}: {str(e)}")
    
    # Also clean up any temp directories that might contain the theme
    try:
        import glob
        temp_pattern = f"/tmp/tmp*/webflow-temp/{theme_name}*"
        temp_dirs = glob.glob(temp_pattern)
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                deleted_locations.append(temp_dir)
    except Exception as e:
        errors.append(f"Error cleaning temp directories: {str(e)}")
    
    if deleted_locations:
        return jsonify({
            "success": True, 
            "message": f"Deleted {len(deleted_locations)} files/directories for theme '{theme_name}'",
            "deleted": deleted_locations,
            "errors": errors if errors else None
        })
    else:
        return jsonify({
            "success": False, 
            "error": f"Theme '{theme_name}' not found in any expected locations",
            "errors": errors if errors else None
        }), 404


def inject_cms_content(soup, cms_data, custom_selectors=""):
    """
    Injects WordPress CMS queries into HTML where Webflow CMS content is detected
    """
    print("Starting CMS content injection...")
    
    # Create mapping of collection names to post types
    collection_mapping = {}
    for collection in cms_data:
        collection_name = collection.get('name', collection.get('slug', ''))
        post_type = 'webflow_' + sanitize_collection_name(collection_name)
        collection_mapping[collection_name.lower()] = {
            'post_type': post_type,
            'fields': collection.get('fields', []),
            'items': collection.get('items', [])
        }
    
    # 1. Find and replace collection lists (with custom selectors)
    soup = inject_collection_lists(soup, collection_mapping, custom_selectors)
    
    # 2. Find and replace individual CMS items
    soup = inject_individual_items(soup, collection_mapping)
    
    # 3. Handle special cases like testimonials, reviews, etc.
    soup = inject_special_collections(soup, collection_mapping)
    
    print("CMS content injection completed")
    return soup


def inject_collection_lists(soup, collection_mapping, custom_selectors=""):
    """
    Detects collection lists (like sliders, grids) and replaces with WordPress loops
    """
    # Default collection selectors
    collection_selectors = [
        '[data-collection]',  # Webflow collection wrapper
        '.w-dyn-list',        # Webflow dynamic list
        '.collection-list',   # Common class name
        '.team-list',         # Team members
        '.review-list',       # Reviews
        '.testimonial-list',  # Testimonials
        '.slider-wrapper',    # Sliders
    ]
    
    # Add custom selectors from user input
    if custom_selectors and custom_selectors.strip():
        user_selectors = [
            selector.strip() 
            for selector in custom_selectors.strip().split('\n') 
            if selector.strip()
        ]
        collection_selectors.extend(user_selectors)
        print(f"Added {len(user_selectors)} custom selectors: {user_selectors}")
    
    print(f"Using collection selectors: {collection_selectors}")
    
    for selector in collection_selectors:
        try:
            elements = soup.select(selector)
            print(f"Found {len(elements)} elements for selector: {selector}")
            
            for element in elements:
                # Try to determine which collection this represents
                collection_info = detect_collection_type(element, collection_mapping)
                if collection_info:
                    # Replace with WordPress query loop
                    wp_loop = generate_wordpress_loop(collection_info, element)
                    if wp_loop:
                        new_element = BeautifulSoup(wp_loop, 'html.parser')
                        element.replace_with(new_element)
                        print(f"Replaced collection list for: {collection_info['name']} using selector: {selector}")
                else:
                    print(f"Could not determine collection type for element with selector: {selector}")
        except Exception as e:
            print(f"Error processing selector '{selector}': {str(e)}")
            continue
    
    return soup


def inject_individual_items(soup, collection_mapping):
    """
    Replaces individual CMS-bound elements with WordPress field calls
    """
    # Look for elements with CMS binding attributes or patterns
    cms_bound_elements = soup.find_all(attrs={
        'data-name': True,
        'data-field': True,
        'data-cms': True
    })
    
    # Also look for common CMS field patterns
    cms_patterns = [
        {'tag': 'img', 'class': re.compile(r'.*main-image.*')},
        {'tag': 'h1', 'class': re.compile(r'.*heading.*|.*title.*')},
        {'tag': 'h2', 'class': re.compile(r'.*heading.*|.*title.*')},
        {'tag': 'h3', 'class': re.compile(r'.*heading.*|.*title.*')},
        {'tag': 'p', 'class': re.compile(r'.*description.*|.*content.*')},
        {'tag': 'div', 'class': re.compile(r'.*rich-text.*')},
    ]
    
    for pattern in cms_patterns:
        elements = soup.find_all(pattern['tag'], class_=pattern.get('class'))
        for element in elements:
            # Try to map this element to a CMS field
            field_mapping = detect_field_mapping(element, collection_mapping)
            if field_mapping:
                # Replace with WordPress field call
                wp_field_call = generate_field_call(field_mapping, element)
                if wp_field_call:
                    new_element = BeautifulSoup(wp_field_call, 'html.parser')
                    element.replace_with(new_element)
    
    return soup


def inject_special_collections(soup, collection_mapping):
    """
    Handle special collection types like testimonials, team members, etc.
    """
    # Handle team members specifically
    if 'team-members' in collection_mapping or 'team members' in collection_mapping:
        team_collection = collection_mapping.get('team-members') or collection_mapping.get('team members')
        if team_collection:
            # Find team member containers
            team_containers = soup.select('.team-member, .member-card, [class*="team"], [class*="member"]')
            for container in team_containers:
                wp_team_loop = f"""
                <?php
                $team_query = new WP_Query(array(
                    'post_type' => '{team_collection["post_type"]}',
                    'posts_per_page' => -1,
                    'post_status' => 'publish'
                ));
                if ($team_query->have_posts()) :
                    while ($team_query->have_posts()) : $team_query->the_post();
                ?>
                {str(container)}
                <?php
                    endwhile;
                    wp_reset_postdata();
                endif;
                ?>
                """
                # Replace static content with dynamic fields inside the container
                wp_team_loop = replace_team_member_fields(wp_team_loop)
                new_element = BeautifulSoup(wp_team_loop, 'html.parser')
                container.replace_with(new_element)
                break  # Only replace the first container to avoid duplicates
    
    # Handle reviews/testimonials
    if 'reviews' in collection_mapping or 'testimonials' in collection_mapping:
        review_collection = collection_mapping.get('reviews') or collection_mapping.get('testimonials')
        if review_collection:
            review_containers = soup.select('.review, .testimonial, [class*="review"], [class*="testimonial"]')
            for container in review_containers:
                wp_review_loop = f"""
                <?php
                $review_query = new WP_Query(array(
                    'post_type' => '{review_collection["post_type"]}',
                    'posts_per_page' => -1,
                    'post_status' => 'publish'
                ));
                if ($review_query->have_posts()) :
                    while ($review_query->have_posts()) : $review_query->the_post();
                ?>
                {str(container)}
                <?php
                    endwhile;
                    wp_reset_postdata();
                endif;
                ?>
                """
                wp_review_loop = replace_review_fields(wp_review_loop)
                new_element = BeautifulSoup(wp_review_loop, 'html.parser')
                container.replace_with(new_element)
                break
    
    return soup


def detect_collection_type(element, collection_mapping):
    """
    Try to determine which collection type this element represents
    """
    # Check element classes and attributes for collection hints
    classes = ' '.join(element.get('class', []))
    element_id = element.get('id', '')
    
    for collection_name, collection_info in collection_mapping.items():
        collection_keywords = [
            collection_name.lower(),
            collection_info['post_type'].replace('webflow_', ''),
            'team', 'member', 'review', 'testimonial', 'portfolio', 'project', 'service'
        ]
        
        # Check classes and ID for matches
        search_text = (classes + ' ' + element_id).lower()
        if any(keyword in search_text for keyword in collection_keywords):
            return {
                'name': collection_name,
                'post_type': collection_info['post_type'],
                'fields': collection_info['fields']
            }
    
    return None


def generate_wordpress_loop(collection_info, original_element):
    """
    Generate WordPress query loop for a collection
    """
    # Get the first item template from the original element
    item_template = original_element.find(class_=re.compile(r'.*item.*|.*card.*'))
    if not item_template:
        item_template = original_element.find('div')
    
    if not item_template:
        return None
    
    return f"""
    <?php
    $query = new WP_Query(array(
        'post_type' => '{collection_info["post_type"]}',
        'posts_per_page' => -1,
        'post_status' => 'publish'
    ));
    if ($query->have_posts()) :
        while ($query->have_posts()) : $query->the_post();
    ?>
    {str(item_template)}
    <?php
        endwhile;
        wp_reset_postdata();
    endif;
    ?>
    """


def detect_field_mapping(element, collection_mapping):
    """
    Try to map an HTML element to a CMS field
    """
    # Simple mapping based on common patterns
    if element.name == 'img':
        return {'type': 'image', 'field': 'main-image'}
    elif element.name in ['h1', 'h2', 'h3'] or 'heading' in ' '.join(element.get('class', [])):
        return {'type': 'text', 'field': 'name'}
    elif 'description' in ' '.join(element.get('class', [])):
        return {'type': 'text', 'field': 'description'}
    elif 'content' in ' '.join(element.get('class', [])):
        return {'type': 'text', 'field': 'content'}
    
    return None


def generate_field_call(field_mapping, element):
    """
    Generate WordPress field call for an element
    """
    if field_mapping['type'] == 'image':
        return f'<?php if (get_field("{field_mapping["field"]}")) : ?><img src="<?php echo get_field("{field_mapping["field"]}"); ?>" alt="<?php the_title(); ?>"><?php endif; ?>'
    elif field_mapping['type'] == 'text':
        return f'<?php echo get_field("{field_mapping["field"]}") ?: get_the_title(); ?>'
    
    return str(element)  # Return original if we can't map it


def replace_team_member_fields(html_content):
    """
    Replace common team member field patterns with WordPress calls
    """
    # Replace common patterns
    html_content = re.sub(r'<img[^>]*class="[^"]*main-image[^"]*"[^>]*>', 
                         '<?php if (get_field("main-image")) : ?><img src="<?php echo get_field("main-image"); ?>" alt="<?php the_title(); ?>"><?php endif; ?>', 
                         html_content)
    
    html_content = re.sub(r'<h[1-6][^>]*class="[^"]*name[^"]*"[^>]*>.*?</h[1-6]>', 
                         '<h3><?php the_title(); ?></h3>', 
                         html_content)
    
    html_content = re.sub(r'<[^>]*class="[^"]*position[^"]*"[^>]*>.*?</[^>]*>', 
                         '<p><?php echo get_field("position"); ?></p>', 
                         html_content)
    
    return html_content


def replace_review_fields(html_content):
    """
    Replace common review field patterns with WordPress calls
    """
    html_content = re.sub(r'<[^>]*class="[^"]*review-text[^"]*"[^>]*>.*?</[^>]*>', 
                         '<p><?php echo get_field("review-text") ?: get_the_content(); ?></p>', 
                         html_content)
    
    html_content = re.sub(r'<[^>]*class="[^"]*author[^"]*"[^>]*>.*?</[^>]*>', 
                         '<p><?php echo get_field("author") ?: get_the_title(); ?></p>', 
                         html_content)
    
    html_content = re.sub(r'<[^>]*class="[^"]*rating[^"]*"[^>]*>.*?</[^>]*>', 
                         '<div class="rating"><?php echo get_field("rating"); ?></div>', 
                         html_content)
    
    return html_content


def sanitize_collection_name(name):
    """
    Sanitize collection name for WordPress post type
    """
    return re.sub(r'[^a-z0-9_-]', '', name.lower().replace(' ', '-'))
    
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
 
    style_css_path = os.path.join(output_theme, 'style.css')
    

    if os.path.exists(style_css_path):
        with open(style_css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()


        updated_css_content = re.sub(
            r'\/\*!\s*Theme Name:\s*([^\*]+)\s*\*\/',
            f'/* Theme Name: {theme_name} */',
            css_content,
            flags=re.DOTALL 
        )

        if updated_css_content != css_content:
       
            with open(style_css_path, 'w', encoding='utf-8') as f:
                f.write(updated_css_content)
            print("style.css updated with new theme name.")
        else:
            print("No changes made to style.css (theme name already correct).")

    else:
        print(f"Error: style.css not found at {style_css_path}")



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
