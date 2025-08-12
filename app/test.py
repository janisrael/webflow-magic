from flask import Flask, request, jsonify, send_file, render_template, make_response
import os, re
import tempfile
import zipfile
import shutil
from bs4 import BeautifulSoup
import re
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)

# Static config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STARTER_THEME = os.path.join(BASE_DIR, 'WebflowStarter')
ASSET_FOLDERS = ['css', 'js', 'images', 'videos', 'fonts', 'media', 'documents', 'cms']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    theme_name = request.form.get('theme_name', 'converted-theme')
    webflow_zip = request.files.get('webflow_zip')
    screenshot_file = request.files.get("screenshot")
    include_cms = request.form.get('include_cms', 'no') == 'yes'
    
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

    # Handle screenshot
    screenshot_dest = os.path.join(output_theme, "screenshot.png")  
    if screenshot_file and screenshot_file.filename != "":
        screenshot_file.save(screenshot_dest)
    else:
        default_thumbnail = os.path.join(BASE_DIR, "assets", "screenshot.png")
        if os.path.exists(default_thumbnail):
            shutil.copy2(default_thumbnail, screenshot_dest)

    # Copy starter theme
    shutil.copytree(STARTER_THEME, output_theme, dirs_exist_ok=True)

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

        # Remove Webflow-specific scripts
        for tag in soup.find_all(['script', 'link']):
            src_or_href = tag.get('src') or tag.get('href') or ''
            if any(lib in src_or_href.lower() for lib in ['jquery', 'splide']):
                tag.decompose()

        # Add WordPress header/footer
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

        # Save as PHP file
        html_str = fix_asset_paths(str(soup))
        out_filename = 'index.php' if filename == 'index.html' else f"page-{os.path.splitext(filename)[0].lower().replace(' ', '-')}.php"
        out_path = os.path.join(output_theme, out_filename)

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html_str)

    # Add CSS override
    components_css_path = os.path.join(output_theme, 'css', 'components.css')
    override_css = '\n.w-section {\n  display: none !important;\n}\n'
    if os.path.exists(components_css_path):
        with open(components_css_path, 'a', encoding='utf-8') as f:
            f.write(override_css)
    else:
        os.makedirs(os.path.dirname(components_css_path), exist_ok=True)
        with open(components_css_path, 'w', encoding='utf-8') as f:
            f.write(override_css)

    # Update style.css
    update_style_css_with_theme_name(output_theme, theme_name)

    # Process CMS if requested
    if include_cms:
        collections = extract_webflow_collections(temp_dir)
        if collections:
            plugin_code = generate_plugin_from_template(collections, theme_name)
            plugin_dir = os.path.join(output_theme, 'webflow-importer')
            os.makedirs(plugin_dir, exist_ok=True)
            
            with open(os.path.join(plugin_dir, 'webflow-importer.php'), 'w') as f:
                f.write(plugin_code)
            
            with open(os.path.join(plugin_dir, 'readme.txt'), 'w') as f:
                f.write(f"=== {theme_name} Importer ===\n")
                f.write("This plugin imports Webflow CMS content into WordPress.\n")
                f.write("After installing the theme, activate this plugin and go to Tools > Webflow Import.\n")

    # Create final ZIP
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
    """Generates the importer plugin from template"""
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-importer.php')
    with open(template_path, 'r') as f:
        template = f.read()
    
    return template.replace('{plugin_name}', f'{theme_name} Importer').replace(
        '{collections_json}', json.dumps(collections, indent=4)
    )

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

        with open(style_css_path, 'w', encoding='utf-8') as f:
            f.write(updated_css_content)

def fix_asset_paths(html):
    """Fix asset paths in HTML to use WordPress template directory"""
    asset_folders = '|'.join(ASSET_FOLDERS)
    pattern = re.compile(r'(src|href)="[^"]*((?:' + asset_folders + r')/([^"/\?#]+))(\?[^\"]*)?"')

    def replacer(match):
        attr, folder_path, raw_filename = match.group(1), match.group(2), match.group(3)
        folder = folder_path.split('/')[0]
        parts = raw_filename.split('.')
        if len(parts) > 2 and re.fullmatch(r'[a-f0-9]{8,}', parts[-2]):
            raw_filename = '.'.join(parts[:-2] + parts[-1:])
        return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{raw_filename}"'

    return pattern.sub(replacer, html)

@app.route("/delete_temp_zip", methods=["POST"])
def delete_temp_zip():
    data = request.get_json()
    zip_path = data.get("zip_path")
    if zip_path and os.path.exists(zip_path):
        os.remove(zip_path)
        return jsonify({"message": "Temporary ZIP deleted."})
    return jsonify({"error": "ZIP file not found."}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5022, debug=True)