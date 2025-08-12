import os
import shutil
import zipfile
from bs4 import BeautifulSoup
import re

# --- CONFIG ---
BASE_DIR = '/home/jan-israel/dev/webflow_magic/app'
WEBFLOW_ZIP = os.path.join(BASE_DIR, 'webflow_export/gridiron-7f4691.webflow.zip')
STARTER_THEME = os.path.join(BASE_DIR, 'WebflowStarter')
OUTPUT_THEME = os.path.join(BASE_DIR, 'output', 'converted-theme')
TEMP_DIR = os.path.join(BASE_DIR, 'webflow-temp')
ASSET_FOLDERS = ['css', 'js', 'images', 'videos', 'fonts', 'media', 'documents']

# --- CLEANUP ---
if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
os.makedirs(TEMP_DIR, exist_ok=True)

if os.path.exists(OUTPUT_THEME):
    shutil.rmtree(OUTPUT_THEME)
shutil.copytree(STARTER_THEME, OUTPUT_THEME)

# --- UNZIP WEBFLOW EXPORT ---
with zipfile.ZipFile(WEBFLOW_ZIP, 'r') as zip_ref:
    zip_ref.extractall(TEMP_DIR)

# --- COPY ASSETS ---
for folder in ASSET_FOLDERS:
    src = os.path.join(TEMP_DIR, folder)
    dest = os.path.join(OUTPUT_THEME, folder)
    if os.path.exists(src):
        shutil.copytree(src, dest, dirs_exist_ok=True)

# --- FIX ASSET PATHS ---
def fix_asset_paths(html):
    pattern = re.compile(
        r'(src|href)="[^"]*((?:' + '|'.join(ASSET_FOLDERS) + r')/([^"/?#]+))(\?[^"]*)?"'
    )

    def replacer(match):
        attr = match.group(1)
        folder = match.group(2).split('/')[0]
        raw_filename = match.group(3)
        parts = raw_filename.split('.')
        if len(parts) > 2 and re.fullmatch(r'[a-f0-9]{8,}', parts[-2]):
            raw_filename = '.'.join(parts[:-2] + parts[-1:])
        return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{raw_filename}"'

    html = pattern.sub(replacer, html)

    # Handle srcset
    def srcset_replacer(match):
        srcset_val = match.group(1)
        parts = [p.strip() for p in srcset_val.split(',')]
        new_parts = []
        for part in parts:
            if ' ' in part:
                url, size = part.rsplit(' ', 1)
            else:
                url, size = part, ''
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
        return f'srcset="{" , ".join(new_parts)}"'

    html = re.sub(r'srcset="([^"]+)"', srcset_replacer, html)

    # Handle data-poster-url and data-video-urls
    def custom_data_attr_replacer(match):
        attr, path = match.groups()
        folder = path.split('/')[0]
        filename = os.path.basename(path)
        if folder in ASSET_FOLDERS:
            return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{filename}"'
        return match.group(0)

    html = re.sub(r'(data-poster-url|data-video-urls)="([^"]+)"', custom_data_attr_replacer, html)

    # Fix background-image in inline styles
    def style_url_replacer(match):
        path = match.group(1)
        folder = path.split('/')[0]
        filename = os.path.basename(path)
        if folder in ASSET_FOLDERS:
            return f'url(<?php echo get_template_directory_uri(); ?>/{folder}/{filename})'
        return match.group(0)


    # Convert .html page links (internal nav) to WordPress template links
    def page_link_replacer(match):
        href_val = match.group(1)
        page_name = os.path.splitext(os.path.basename(href_val))[0]
        return f'href="<?php echo site_url(\'/{page_name}\'); ?>"'

    html = re.sub(r'href="([^"]+\.html)"', page_link_replacer, html)
    html = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', style_url_replacer, html)
    # --- REPLACE SPLIDE WITH CDN ---
    # Look for local splide minified CSS and JS files and replace with CDN
    html = re.sub(r'(<link href="[^"]*splide.min.css[^"]*" rel="stylesheet"[^>]*>)',
                  '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css">', html)
    html = re.sub(r'(<script src="[^"]*splide.min.js[^"]*"></script>)',
                  '<script src="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js"></script>', html)

    return html


# --- CONVERT EACH HTML PAGE ---
for filename in os.listdir(TEMP_DIR):
    if not filename.endswith('.html'):
        continue

    filepath = os.path.join(TEMP_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # ✅ REMOVE local jQuery or splide if present (scripts and styles)
    for tag in soup.find_all(['script', 'link']):
        src_or_href = tag.get('src') or tag.get('href') or ''
        if any(lib in src_or_href.lower() for lib in ['jquery', 'splide']):
            tag.decompose()

    # ✅ ADD jQuery & Splide CDN in <head>
    head = soup.find('head')
    if head:
        cdn_jquery = soup.new_tag('script', src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js')
        splide_css = soup.new_tag('link', rel='stylesheet',
            href='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css')
        splide_js = soup.new_tag('script',
            src='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js')

        head.insert(0, cdn_jquery)
        head.append(splide_css)
        head.append(splide_js)

    # ✅ Inject WordPress header/footer
    body = soup.find('body')
    if body:
        original_contents = list(body.contents)
        body.clear()
        body.append(BeautifulSoup('<?php get_header(); ?>', 'html.parser'))
        for elem in original_contents:
            body.append(elem)
        body.append(BeautifulSoup('<?php get_footer(); ?>', 'html.parser'))
    else:
        soup.insert(0, BeautifulSoup('<?php get_header(); ?>', 'html.parser'))
        soup.append(BeautifulSoup('<?php get_footer(); ?>', 'html.parser'))

    # ✅ Fix asset paths
    html_str = str(soup)
    html_str = fix_asset_paths(html_str)

    # ✅ Save as PHP
    if filename == 'index.html':
        out_filename = 'index.php'
    else:
        slug = os.path.splitext(filename)[0].lower().replace(' ', '-')
        out_filename = f'page-{slug}.php'

    out_path = os.path.join(OUTPUT_THEME, out_filename)
    with open(out_path, 'w', encoding='utf-8') as f_out:
        f_out.write(html_str)


# --- ADD CSS TO HIDE NAVIGATION ---
components_css_path = os.path.join(OUTPUT_THEME, 'css', 'components.css')
override_css = '\n.w-section {\n  display: none !important;\n}\n'

# Append the CSS rule if it's not already present
if os.path.exists(components_css_path):
    with open(components_css_path, 'r+', encoding='utf-8') as f:
        existing_css = f.read()
        if '.w-section' not in existing_css:
            f.write(override_css)
else:
    os.makedirs(os.path.dirname(components_css_path), exist_ok=True)
    with open(components_css_path, 'w', encoding='utf-8') as f:
        f.write(override_css)

# --- ZIP the final theme folder ---
zip_output = os.path.join(BASE_DIR, 'converted-theme.zip')
shutil.make_archive(zip_output.replace('.zip', ''), 'zip', OUTPUT_THEME)

print(f"✅ Conversion complete. Theme ready at: {OUTPUT_THEME}")
print(f"📦 Theme ZIP created: {zip_output}")
