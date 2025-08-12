from flask import Flask, request, jsonify, send_file, render_template,make_response
import os, re
import tempfile
import zipfile
import shutil
from bs4 import BeautifulSoup
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Static config
# BASE_DIR = '/home/jan-israel/dev/webflow_magic/app'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"BASE_DIR: {BASE_DIR}")
STARTER_THEME = os.path.join(BASE_DIR, 'WebflowStarter')
ASSET_FOLDERS = ['css', 'js', 'images', 'videos', 'fonts', 'media', 'documents']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    theme_name = request.form.get('theme_name', 'converted-theme')
    webflow_zip = request.files.get('webflow_zip')
    screenshot_file = request.files.get("screenshot")
    
    print(f"Received screenshot_file: {screenshot_file}")
    if not webflow_zip:
        return jsonify({"error": "Missing Webflow ZIP"}), 400

    theme_name = secure_filename(theme_name)
    temp_base = tempfile.mkdtemp()
    zip_path = os.path.join(temp_base, theme_name + ".zip")
    temp_dir = os.path.join(temp_base, 'webflow-temp')
    output_theme = os.path.join(temp_base, theme_name)

    # Ensure that output_theme is clean (remove it if it exists)
    if os.path.exists(output_theme):
        shutil.rmtree(output_theme)

    os.makedirs(output_theme, exist_ok=True)

    # Handle the screenshot file (uploaded or default)
    screenshot_dest = os.path.join(output_theme, "screenshot.png")  # Explicit destination inside output_theme
    
    if screenshot_file and screenshot_file.filename != "":
        # Save the uploaded screenshot directly inside the output_theme folder
        screenshot_file.save(screenshot_dest)
        print(f"Screenshot uploaded and saved at: {screenshot_dest}")
    else:
        # Fallback to default thumbnail if no screenshot is provided
        default_thumbnail = os.path.join(BASE_DIR, "assets", "screenshot.png")
        if os.path.exists(default_thumbnail):
            print(f"Using default thumbnail: {default_thumbnail}")
            if os.path.exists(screenshot_dest):
                os.remove(screenshot_dest)  # Remove existing screenshot
            shutil.copy2(default_thumbnail, screenshot_dest)
            print(f"Default thumbnail saved at: {screenshot_dest}")
        else:
            print("Default thumbnail not found!")

    shutil.copytree(STARTER_THEME, output_theme, dirs_exist_ok=True)

    zip_path = os.path.join(temp_base, secure_filename(webflow_zip.filename))
    webflow_zip.save(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    for folder in ASSET_FOLDERS:
        src = os.path.join(temp_dir, folder)
        dest = os.path.join(output_theme, folder)
        if os.path.exists(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)

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

    # Update the style.css with the dynamic theme name
    update_style_css_with_theme_name(output_theme, theme_name)

    # Final zip path (inside temp)
    final_zip_path = os.path.join(temp_base, theme_name + ".zip")
    shutil.make_archive(final_zip_path.replace(".zip", ""), "zip", output_theme)

    # Send the file and return path header
    response = make_response(send_file(
        final_zip_path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=theme_name + ".zip"
    ))
    response.headers["X-Temp-Zip-Path"] = final_zip_path

    return response



    
def update_style_css_with_theme_name(output_theme, theme_name):
    # Path to the style.css file
    style_css_path = os.path.join(output_theme, 'style.css')
    
    # Check if the file exists
    if os.path.exists(style_css_path):
        with open(style_css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # Debugging: Print out the current content of the style.css
        # print("Original style.css content:")
        # print(css_content[:500])  # Show the first 500 characters to check the content

        # Update regex to ensure the match is more flexible for spaces or new lines
        updated_css_content = re.sub(
            r'\/\*!\s*Theme Name:\s*([^\*]+)\s*\*\/',
            f'/* Theme Name: {theme_name} */',
            css_content,
            flags=re.DOTALL  # Allow matching across lines for better flexibility
        )

        # Debugging: Print out the updated content to verify the change
        # print("Updated style.css content:")
        # print(updated_css_content[:500])  # Show the first 500 characters to check the update

        # Check if the content has actually changed
        if updated_css_content != css_content:
            # Write the updated content back to the style.css
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
