import os
import requests
import shutil
from bs4 import BeautifulSoup, Comment, NavigableString
from urllib.parse import urljoin
import re

FRAMER_SITE_URL = "https://remarkable-tetragon-895771.framer.app/"
THEME_NAME = "converted-theme"
OUTPUT_DIR = os.path.abspath(THEME_NAME)

# add this to the .htaccess

# # BEGIN WordPress
# # The directives (lines) between "BEGIN WordPress" and "END WordPress" are
# # dynamically generated, and should only be modified via WordPress filters.
# # Any changes to the directives between these markers will be overwritten.
# <IfModule mod_rewrite.c>
# RewriteEngine On
# RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
# RewriteBase /smartchart-website/
# RewriteRule ^index\.php$ - [L]
# RewriteCond %{REQUEST_FILENAME} !-f
# RewriteCond %{REQUEST_FILENAME} !-d
# RewriteRule . /smartchart-website/index.php [L]
# </IfModule>
# AddType text/javascript .mjs
# AddType text/css .css

# AddType image/png .png
# AddType image/svg+xml .svg
# <FilesMatch "\.svg$">
#   Require all granted
# </FilesMatch>
# # END WordPress


# Remove tags and attributes that are not needed in the WordPress theme
def remove_unwanted_meta_and_links(soup):
    
    for meta in soup.find_all("meta", {"name": "robots"}):
        meta.decompose()
    
    for link in soup.find_all("link", {"rel": "canonical"}):
        link.decompose()
    
    for meta in soup.find_all("meta", {"content": FRAMER_SITE_URL}):
        meta.decompose()
    
    for link in soup.find_all("link", {"rel": "preconnect", "href": "https://fonts.gstatic.com"}):
        link.decompose()
    
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "framer.com" in comment.lower():
            comment.extract()

def create_theme_structure():
    for folder in ['js', 'css', 'fonts', 'images', 'template-parts']:
        os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)

def download_file(url, folder):
    local_filename = url.split('/')[-1].split('?')[0]
    path = os.path.join(folder, local_filename)
    if os.path.exists(path):
        return path  # Don't re-download
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                f.write(r.content)
            print(f"✔️  Downloaded: {local_filename}")
            return path
        else:
            print(f"⚠️  Failed to download {url}: status code {r.status_code}")
    except Exception as e:
        print(f"⚠️  Failed to download {url}: {e}")
    return None



def create_wp_files():
    style_css = f"""/*
Theme Name: {THEME_NAME}
Author: SourceSelect.ca
Version: 1.0
*/"""

    header_php = """<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<header><h1><?php bloginfo('name'); ?></h1></header>
"""

    footer_php = """<footer><p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?></p></footer>
<?php wp_footer(); ?>
</body>
</html>
"""

    functions_php_content = """<?php
function theme_enqueue_scripts() {
    wp_enqueue_style('main-style', get_template_directory_uri() . '/css/style.css', array(), false);
    foreach (glob(get_template_directory() . '/js/*.js') as $js_file) {
        wp_enqueue_script(basename($js_file), get_template_directory_uri() . '/js/' . basename($js_file), array(), false, true);
    }
    foreach (glob(get_template_directory() . '/js/*.mjs') as $mjs_file) {
        wp_enqueue_script(basename($mjs_file), get_template_directory_uri() . '/js/' . basename($mjs_file), array(), false, true);
    }
}

add_filter('script_loader_tag', function($tag, $handle, $src) {
    if (strpos($src, '.mjs') !== false) {
        $tag = '<script type="module" src="' . esc_url($src) . '"></script>';
    }
    return $tag;
}, 10, 3);

add_action( 'wp_enqueue_scripts', 'theme_enqueue_scripts' );
"""

    with open(os.path.join(OUTPUT_DIR, "style.css"), "w", encoding="utf-8") as f:
        f.write(style_css)

    with open(os.path.join(OUTPUT_DIR, "header.php"), "w", encoding="utf-8") as f:
        f.write(header_php)

    with open(os.path.join(OUTPUT_DIR, "footer.php"), "w", encoding="utf-8") as f:
        f.write(footer_php)

    with open(os.path.join(OUTPUT_DIR, "functions.php"), "w", encoding="utf-8") as f:
        f.write(functions_php_content)

def create_template_parts():
    content_template = """<?php
/**
 * Template part for displaying page content
 */
?>

<article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
<?php the_content(); ?>
</article>
"""
    os.makedirs(os.path.join(OUTPUT_DIR, "template-parts"), exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "template-parts", "content-page.php"), "w", encoding="utf-8") as f:
        f.write(content_template)

    print(f"✔️ Template parts created.")


def download_assets_from_file(file_path):
    """
    Scan downloaded JS/CSS files for more framerstatic/framerusercontent asset URLs and download them recursively.
    """
    asset_url_regex = re.compile(
        r'https://(?:app\.framerstatic\.com|framerusercontent\.com)[^\'"\)\s]+'
    )
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    urls = set(asset_url_regex.findall(content))
    for url in urls:
        ext = os.path.splitext(url)[1].lower()
        if ext in ('.js', '.mjs'):
            folder = os.path.join(OUTPUT_DIR, 'js')
        elif ext == '.css':
            folder = os.path.join(OUTPUT_DIR, 'css')
        elif ext in ('.woff', '.woff2', '.ttf', '.otf'):
            folder = os.path.join(OUTPUT_DIR, 'fonts')
        elif ext in ('.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp'):
            folder = os.path.join(OUTPUT_DIR, 'images')
        else:
            folder = os.path.join(OUTPUT_DIR, 'images')
        download_file(url, folder)

def recursive_asset_download_and_rewrite():
    """
    After initial download, scan all JS, CSS, and HTML files in the theme for more framerstatic/framerusercontent URLs,
    download any missing assets, and rewrite URLs to local theme paths.
    """
    checked_files = set()
    files_to_check = []
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for fname in files:
            if fname.endswith(('.js', '.mjs', '.css', '.html', '.php')):
                files_to_check.append(os.path.join(root, fname))

    while files_to_check:
        file_path = files_to_check.pop()
        if file_path in checked_files:
            continue
        checked_files.add(file_path)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        download_assets_from_file(file_path)
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for fname in files:
                fpath = os.path.join(root, fname)
                if fpath not in checked_files and fname.endswith(('.js', '.mjs', '.css')):
                    files_to_check.append(fpath)

    # URL rewriting functions
    def replace_framerusercontent(match, php=False):
        filename = os.path.basename(match.group(1))
        if php:
            return f"<?php echo get_template_directory_uri(); ?>/images/{filename}"
        else:
            return f"/wp-content/themes/{THEME_NAME}/images/{filename}"

    def replace_framerstatic(match, php=False):
        chunk = match.group(1)
        if php:
            return f"<?php echo get_template_directory_uri(); ?>/js/{chunk}"
        else:
            return f"/wp-content/themes/{THEME_NAME}/js/{chunk}"

    # Rewrite URLs in all files
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for fname in files:
            fpath = os.path.join(root, fname)
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Decide: use PHP (for .php/.html), or static (for .js/.css)
            is_php = fname.endswith(('.php', '.html'))
            # Images
            content = re.sub(
                r'https://framerusercontent\.com/([^\'"\)\s]+)',
                lambda m: replace_framerusercontent(m, php=is_php),
                content
            )
            # JS chunks
            content = re.sub(
                r'https://app\.framerstatic\.com/([^\'"\)\s]+)',
                lambda m: replace_framerstatic(m, php=is_php),
                content
            )
            # Fonts in js (optional, if you handle fonts)
            content = re.sub(
                r'<?php echo get_template_directory_uri\(\); \?>/js/([^\'"\)\s]+?\.(?:woff2?|ttf|otf))',
                r'<?php echo get_template_directory_uri(); ?>/fonts/\1',
                content
            )

            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)


def download_images_from_external_sources(soup):
    for img in soup.find_all("img", src=True):
        src = img['src']
        if "framerusercontent.com" in src:
            full_url = urljoin(FRAMER_SITE_URL, src)
            new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
            if new_path:
                img['src'] = f"<?php echo get_template_directory_uri(); ?>/images/{os.path.basename(new_path)}"
        elif src:
            img['src'] = urljoin(FRAMER_SITE_URL, src)

def update_meta_tags_and_open_graph(soup):
    for meta in soup.find_all("meta", content=True):
        content = meta.get("content")
        if content and "framerusercontent.com" in content:
            full_url = urljoin(FRAMER_SITE_URL, content)
            new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
            if new_path:
                meta['content'] = f"<?php echo get_template_directory_uri(); ?>/images/{os.path.basename(new_path)}"




def download_fonts_from_html_styles(soup):
 
    for style in soup.find_all("style"):
        css_content = style.string
        if not css_content:
            continue
        font_urls = re.findall(r"url\(['\"]?(https?://[^'\"\)]+)['\"]?\)", css_content)
        for font_url in font_urls:
            if font_url.endswith(('.woff', '.woff2', '.ttf', '.otf')):
                local_path = download_file(font_url, os.path.join(OUTPUT_DIR, 'fonts'))
                if local_path:
       
                    css_content = css_content.replace(font_url,
                        f"<?php echo get_template_directory_uri(); ?>/fonts/{os.path.basename(local_path)}")
     
        style.string = css_content


def download_fonts_from_css(css_path):

    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
 
    font_urls = re.findall(r"url\(['\"]?(https?://[^'\"\)]+)['\"]?\)", css_content)
    for font_url in font_urls:
       
        if font_url.endswith(('.woff', '.woff2', '.ttf', '.otf')):
            local_path = download_file(font_url, os.path.join(OUTPUT_DIR, 'fonts'))
            if local_path:
           
                css_content = css_content.replace(font_url,
                    f"<?php echo get_template_directory_uri(); ?>/fonts/{os.path.basename(local_path)}")

    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)

def remove_mjs_assets(soup):

    for script in soup.find_all("script", src=True):
        if script['src'].endswith('.mjs') or '.mjs' in script['src']:
            script.decompose()

    for link in soup.find_all("link", href=True):
        if link['href'].endswith('.mjs') or '.mjs' in link['href']:
            link.decompose()



                
def process_links_and_scripts(soup):
    """
    Updated to match both framerusercontent.com and framerstatic.com for downloads.
    """
    for script in soup.find_all("script", src=True):
        src = script['src']
        if ("framerusercontent.com" in src or
            "framerstatic.com" in src or
            src.startswith("/")):
            full_url = urljoin(FRAMER_SITE_URL, src)
            new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'js'))
            if new_path:
                new_src = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(new_path)
                script['src'] = NavigableString(new_src)
                if new_path.endswith('.mjs'):
                    script['type'] = "module"
        else:
            new_src = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(src)
            script['src'] = NavigableString(new_src)
            if src.endswith('.mjs'):
                script['type'] = "module"

    for link in soup.find_all("link", rel="stylesheet", href=True):
        href = link['href']
        if ("framerusercontent.com" in href or
            "framerstatic.com" in href or
            href.startswith("/")):
            full_url = urljoin(FRAMER_SITE_URL, href)
            new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'css'))
            if new_path:
                # Optional: download_fonts_from_css(new_path)
                new_href = "<?php echo get_template_directory_uri(); ?>/css/" + os.path.basename(new_path)
                link['href'] = NavigableString(new_href)
        else:
            new_href = "<?php echo get_template_directory_uri(); ?>/css/" + os.path.basename(href)
            link['href'] = NavigableString(new_href)

    for link in soup.find_all("link", rel="modulepreload", href=True):
        href = link['href']
        if ("framerusercontent.com" in href or
            "framerstatic.com" in href or
            href.startswith("/")):
            full_url = urljoin(FRAMER_SITE_URL, href)
            new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'js'))
            if new_path:
                new_href = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(new_path)
                link['href'] = NavigableString(new_href)
        else:
            new_href = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(href)
            link['href'] = NavigableString(new_href)

    for link in soup.find_all("link", rel=lambda v: v and "icon" in v, href=True):
        href = link['href']
        if ("framerusercontent.com" in href or
            "framerstatic.com" in href or
            href.startswith("/")):
            full_url = urljoin(FRAMER_SITE_URL, href)
            new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
            if new_path:
                new_href = "<?php echo get_template_directory_uri(); ?>/images/" + os.path.basename(new_path)
                link['href'] = NavigableString(new_href)
        else:
            new_href = "<?php echo get_template_directory_uri(); ?>/images/" + os.path.basename(href)
            link['href'] = NavigableString(new_href)

def parse_and_rewrite_html():
    response = requests.get(FRAMER_SITE_URL)
    if response.status_code != 200:
        print("❌ Failed to load Framer URL")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    
    process_links_and_scripts(soup)
    download_images_from_external_sources(soup)
    update_meta_tags_and_open_graph(soup)
    download_fonts_from_html_styles(soup)
    remove_unwanted_meta_and_links(soup)
    remove_mjs_assets(soup) 
    # ... (rest of your existing processing steps)
    # After all processing and saving:
    with open(os.path.join(OUTPUT_DIR, "index.php"), "w", encoding='utf-8') as f:
        f.write("<?php get_header(); ?>\n")
        f.write(soup.prettify(formatter=None))  # Ensures raw PHP in output
        f.write("\n<?php get_footer(); ?>")



def zip_theme():
    zip_name = f"{THEME_NAME}.zip"
    shutil.make_archive(base_name=THEME_NAME, format='zip', root_dir=OUTPUT_DIR)
    print(f"🎉 Theme zipped at: {zip_name}")

def main():
    print("🚧 Converting Framer site to WordPress theme...")
    create_theme_structure()
    parse_and_rewrite_html()
  

    # After initial parse, crawl all files for extra static/dynamic assets and rewrite URLs
    recursive_asset_download_and_rewrite()
    create_wp_files()
    create_template_parts()
    zip_theme()
    # ... (rest of your theme file creation and zipping)
    print(f"✅ Done! Theme saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()




# import os
# import requests
# import shutil
# from bs4 import BeautifulSoup, Comment,NavigableString
# from urllib.parse import urljoin
# import re

# FRAMER_SITE_URL = "https://precious-adapts-207928.framer.app/"
# THEME_NAME = "converted-theme"
# OUTPUT_DIR = os.path.abspath(THEME_NAME)

# # Remove tags and attributes that are not needed in the WordPress theme
# def remove_unwanted_meta_and_links(soup):
    
#     for meta in soup.find_all("meta", {"name": "robots"}):
#         meta.decompose()
    
#     for link in soup.find_all("link", {"rel": "canonical"}):
#         link.decompose()
    
#     for meta in soup.find_all("meta", {"content": FRAMER_SITE_URL}):
#         meta.decompose()
    
#     for link in soup.find_all("link", {"rel": "preconnect", "href": "https://fonts.gstatic.com"}):
#         link.decompose()
    
#     for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
#         if "framer.com" in comment.lower():
#             comment.extract()


# def download_fonts_from_html_styles(soup):
 
#     for style in soup.find_all("style"):
#         css_content = style.string
#         if not css_content:
#             continue
#         font_urls = re.findall(r"url\(['\"]?(https?://[^'\"\)]+)['\"]?\)", css_content)
#         for font_url in font_urls:
#             if font_url.endswith(('.woff', '.woff2', '.ttf', '.otf')):
#                 local_path = download_file(font_url, os.path.join(OUTPUT_DIR, 'fonts'))
#                 if local_path:
       
#                     css_content = css_content.replace(font_url,
#                         f"<?php echo get_template_directory_uri(); ?>/fonts/{os.path.basename(local_path)}")
     
#         style.string = css_content


# def download_fonts_from_css(css_path):

#     with open(css_path, 'r', encoding='utf-8') as f:
#         css_content = f.read()
 
#     font_urls = re.findall(r"url\(['\"]?(https?://[^'\"\)]+)['\"]?\)", css_content)
#     for font_url in font_urls:
       
#         if font_url.endswith(('.woff', '.woff2', '.ttf', '.otf')):
#             local_path = download_file(font_url, os.path.join(OUTPUT_DIR, 'fonts'))
#             if local_path:
           
#                 css_content = css_content.replace(font_url,
#                     f"<?php echo get_template_directory_uri(); ?>/fonts/{os.path.basename(local_path)}")

#     with open(css_path, 'w', encoding='utf-8') as f:
#         f.write(css_content)

# def remove_mjs_assets(soup):

#     for script in soup.find_all("script", src=True):
#         if script['src'].endswith('.mjs') or '.mjs' in script['src']:
#             script.decompose()

#     for link in soup.find_all("link", href=True):
#         if link['href'].endswith('.mjs') or '.mjs' in link['href']:
#             link.decompose()


# def create_theme_structure():
#     for folder in ['js', 'css', 'fonts', 'images', 'template-parts']:
#         os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)

# def download_file(url, folder):
#     local_filename = url.split('/')[-1].split('?')[0]
#     path = os.path.join(folder, local_filename)
#     try:
#         r = requests.get(url, stream=True, timeout=10)
#         if r.status_code == 200:
#             with open(path, 'wb') as f:
#                 f.write(r.content)
#             print(f"✔️  Downloaded: {local_filename}")
#             return path
#     except Exception as e:
#         print(f"⚠️  Failed to download {url}: {e}")
#     return None

# def process_links_and_scripts(soup):
   
#     for script in soup.find_all("script", src=True):
#         src = script['src']
#         if "framerusercontent.com" in src or src.startswith("/"):
#             full_url = urljoin(FRAMER_SITE_URL, src)
#             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'js'))
#             if new_path:
#                 new_src = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(new_path)
#                 script['src'] = NavigableString(new_src)
           
#                 if new_path.endswith('.mjs'):
#                     script['type'] = "module"
#         else:
       
#             new_src = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(src)
#             script['src'] = NavigableString(new_src)
#             if src.endswith('.mjs'):
#                 script['type'] = "module"


#     for link in soup.find_all("link", rel="stylesheet", href=True):
#         href = link['href']
#         if "framerusercontent.com" in href or href.startswith("/"):
#             full_url = urljoin(FRAMER_SITE_URL, href)
#             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'css'))
#             if new_path:
#                 download_fonts_from_css(new_path) 
#                 new_href = "<?php echo get_template_directory_uri(); ?>/css/" + os.path.basename(new_path)
#                 link['href'] = NavigableString(new_href)
#         else:
        
#             new_href = "<?php echo get_template_directory_uri(); ?>/css/" + os.path.basename(href)
#             link['href'] = NavigableString(new_href)


#     for link in soup.find_all("link", rel="modulepreload", href=True):
#         href = link['href']
#         if "framerusercontent.com" in href or href.startswith("/"):
#             full_url = urljoin(FRAMER_SITE_URL, href)
#             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'js'))
#             if new_path:
#                 new_href = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(new_path)
#                 link['href'] = NavigableString(new_href)
#         else:
#             new_href = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(href)
#             link['href'] = NavigableString(new_href)


#     for link in soup.find_all("link", rel=lambda v: v and "icon" in v, href=True):
#         href = link['href']
#         if "framerusercontent.com" in href or href.startswith("/"):
#             full_url = urljoin(FRAMER_SITE_URL, href)
#             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
#             if new_path:
#                 new_href = "<?php echo get_template_directory_uri(); ?>/images/" + os.path.basename(new_path)
#                 link['href'] = NavigableString(new_href)
#         else:
#             new_href = "<?php echo get_template_directory_uri(); ?>/images/" + os.path.basename(href)
#             link['href'] = NavigableString(new_href)



# def download_images_from_external_sources(soup):
#     for img in soup.find_all("img", src=True):
#         src = img['src']
#         if "framerusercontent.com" in src:
#             full_url = urljoin(FRAMER_SITE_URL, src)
#             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
#             if new_path:
#                 img['src'] = f"<?php echo get_template_directory_uri(); ?>/images/{os.path.basename(new_path)}"
#         elif src:
#             img['src'] = urljoin(FRAMER_SITE_URL, src)

# def update_meta_tags_and_open_graph(soup):
#     for meta in soup.find_all("meta", content=True):
#         content = meta.get("content")
#         if content and "framerusercontent.com" in content:
#             full_url = urljoin(FRAMER_SITE_URL, content)
#             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
#             if new_path:
#                 meta['content'] = f"<?php echo get_template_directory_uri(); ?>/images/{os.path.basename(new_path)}"

# def parse_and_rewrite_html():
#     response = requests.get(FRAMER_SITE_URL)
#     if response.status_code != 200:
#         print("❌ Failed to load Framer URL")
#         return

#     soup = BeautifulSoup(response.text, "html.parser")

#     process_links_and_scripts(soup)
#     download_images_from_external_sources(soup)
#     update_meta_tags_and_open_graph(soup)
#     download_fonts_from_html_styles(soup)
#     remove_unwanted_meta_and_links(soup)
#     remove_mjs_assets(soup) 

#     # Write to index.php
#     # with open(os.path.join(OUTPUT_DIR, "index.php"), "w", encoding='utf-8') as f:
#     #     f.write("<?php get_header(); ?>\n")
#     #     f.write(soup.prettify())
#     #     f.write("\n<?php get_footer(); ?>")

#     with open(os.path.join(OUTPUT_DIR, "index.php"), "w", encoding='utf-8') as f:
#         f.write("<?php get_header(); ?>\n")
#         f.write(soup.prettify(formatter=None))  # Ensures raw PHP in output
#         f.write("\n<?php get_footer(); ?>")

# def create_wp_files():
#     style_css = f"""/*
# Theme Name: {THEME_NAME}
# Author: SourceSelect.ca
# Version: 1.0
# */"""

#     header_php = """<!DOCTYPE html>
# <html <?php language_attributes(); ?>>
# <head>
#     <meta charset="<?php bloginfo('charset'); ?>">
#     <?php wp_head(); ?>
# </head>
# <body <?php body_class(); ?>>
# <header><h1><?php bloginfo('name'); ?></h1></header>
# """

#     footer_php = """<footer><p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?></p></footer>
# <?php wp_footer(); ?>
# </body>
# </html>
# """

#     functions_php_content = """<?php
# function theme_enqueue_scripts() {
#     wp_enqueue_style('main-style', get_template_directory_uri() . '/css/style.css', array(), false);
#     foreach (glob(get_template_directory() . '/js/*.js') as $js_file) {
#         wp_enqueue_script(basename($js_file), get_template_directory_uri() . '/js/' . basename($js_file), array(), false, true);
#     }
#     foreach (glob(get_template_directory() . '/js/*.mjs') as $mjs_file) {
#         wp_enqueue_script(basename($mjs_file), get_template_directory_uri() . '/js/' . basename($mjs_file), array(), false, true);
#     }
# }

# add_filter('script_loader_tag', function($tag, $handle, $src) {
#     if (strpos($src, '.mjs') !== false) {
#         $tag = '<script type="module" src="' . esc_url($src) . '"></script>';
#     }
#     return $tag;
# }, 10, 3);

# add_action( 'wp_enqueue_scripts', 'theme_enqueue_scripts' );
# """

#     with open(os.path.join(OUTPUT_DIR, "style.css"), "w", encoding="utf-8") as f:
#         f.write(style_css)

#     with open(os.path.join(OUTPUT_DIR, "header.php"), "w", encoding="utf-8") as f:
#         f.write(header_php)

#     with open(os.path.join(OUTPUT_DIR, "footer.php"), "w", encoding="utf-8") as f:
#         f.write(footer_php)

#     with open(os.path.join(OUTPUT_DIR, "functions.php"), "w", encoding="utf-8") as f:
#         f.write(functions_php_content)

        

# def create_template_parts():
#     content_template = """<?php
# /**
#  * Template part for displaying page content
#  */
# ?>

# <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
# <?php the_content(); ?>
# </article>
# """
#     os.makedirs(os.path.join(OUTPUT_DIR, "template-parts"), exist_ok=True)
#     with open(os.path.join(OUTPUT_DIR, "template-parts", "content-page.php"), "w", encoding="utf-8") as f:
#         f.write(content_template)

#     print(f"✔️ Template parts created.")

# def zip_theme():
#     zip_name = f"{THEME_NAME}.zip"
#     shutil.make_archive(base_name=THEME_NAME, format='zip', root_dir=OUTPUT_DIR)
#     print(f"🎉 Theme zipped at: {zip_name}")

# def main():
#     print("🚧 Converting Framer site to WordPress theme...")
#     create_theme_structure()
#     parse_and_rewrite_html()
#     create_wp_files()
#     create_template_parts()
#     zip_theme()
#     print(f"✅ Done! Theme saved in: {OUTPUT_DIR}")

# if __name__ == "__main__":
#     main()