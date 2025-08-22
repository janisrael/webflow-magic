# import os
# import requests
# import shutil
# from bs4 import BeautifulSoup, Comment, NavigableString
# from urllib.parse import urljoin
# import re

# FRAMER_SITE_URL = "https://goodness-tetragon-388195.framer.app/"
# THEME_NAME = "converted-theme"
# OUTPUT_DIR = os.path.abspath(THEME_NAME)

# # add this to the .htaccess

# # # BEGIN WordPress
# # # The directives (lines) between "BEGIN WordPress" and "END WordPress" are
# # # dynamically generated, and should only be modified via WordPress filters.
# # # Any changes to the directives between these markers will be overwritten.
# # <IfModule mod_rewrite.c>
# # RewriteEngine On
# # RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
# # RewriteBase /smartchart-website/
# # RewriteRule ^index\.php$ - [L]
# # RewriteCond %{REQUEST_FILENAME} !-f
# # RewriteCond %{REQUEST_FILENAME} !-d
# # RewriteRule . /smartchart-website/index.php [L]
# # </IfModule>
# # AddType text/javascript .mjs
# # AddType text/css .css

# # AddType image/png .png
# # AddType image/svg+xml .svg
# # <FilesMatch "\.svg$">
# #   Require all granted
# # </FilesMatch>
# # # END WordPress


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

# def create_theme_structure():
#     for folder in ['js', 'css', 'fonts', 'images', 'template-parts']:
#         os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)

# def download_file(url, folder):
#     local_filename = url.split('/')[-1].split('?')[0]
#     path = os.path.join(folder, local_filename)
#     if os.path.exists(path):
#         return path  # Don't re-download
#     try:
#         r = requests.get(url, stream=True, timeout=10)
#         if r.status_code == 200:
#             with open(path, 'wb') as f:
#                 f.write(r.content)
#             print(f"✔️  Downloaded: {local_filename}")
#             return path
#         else:
#             print(f"⚠️  Failed to download {url}: status code {r.status_code}")
#     except Exception as e:
#         print(f"⚠️  Failed to download {url}: {e}")
#     return None



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


# def download_assets_from_file(file_path):
#     """
#     Scan downloaded JS/CSS files for more framerstatic/framerusercontent asset URLs and download them recursively.
#     """
#     asset_url_regex = re.compile(
#         r'https://(?:app\.framerstatic\.com|framerusercontent\.com)[^\'"\)\s]+'
#     )
#     with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
#         content = f.read()
#     urls = set(asset_url_regex.findall(content))
#     for url in urls:
#         ext = os.path.splitext(url)[1].lower()
#         if ext in ('.js', '.mjs'):
#             folder = os.path.join(OUTPUT_DIR, 'js')
#         elif ext == '.css':
#             folder = os.path.join(OUTPUT_DIR, 'css')
#         elif ext in ('.woff', '.woff2', '.ttf', '.otf'):
#             folder = os.path.join(OUTPUT_DIR, 'fonts')
#         elif ext in ('.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp'):
#             folder = os.path.join(OUTPUT_DIR, 'images')
#         else:
#             folder = os.path.join(OUTPUT_DIR, 'images')
#         download_file(url, folder)

# def recursive_asset_download_and_rewrite():
#     """
#     After initial download, scan all JS, CSS, and HTML files in the theme for more framerstatic/framerusercontent URLs,
#     download any missing assets, and rewrite URLs to local theme paths.
#     """
#     checked_files = set()
#     files_to_check = []
#     for root, dirs, files in os.walk(OUTPUT_DIR):
#         for fname in files:
#             if fname.endswith(('.js', '.mjs', '.css', '.html', '.php')):
#                 files_to_check.append(os.path.join(root, fname))

#     while files_to_check:
#         file_path = files_to_check.pop()
#         if file_path in checked_files:
#             continue
#         checked_files.add(file_path)
#         with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
#             content = f.read()
#         download_assets_from_file(file_path)
#         for root, dirs, files in os.walk(OUTPUT_DIR):
#             for fname in files:
#                 fpath = os.path.join(root, fname)
#                 if fpath not in checked_files and fname.endswith(('.js', '.mjs', '.css')):
#                     files_to_check.append(fpath)

#     # URL rewriting functions
#     def replace_framerusercontent(match, php=False):
#         filename = os.path.basename(match.group(1))
#         if php:
#             return f"<?php echo get_template_directory_uri(); ?>/images/{filename}"
#         else:
#             return f"/wp-content/themes/{THEME_NAME}/images/{filename}"

#     def replace_framerstatic(match, php=False):
#         chunk = match.group(1)
#         if php:
#             return f"<?php echo get_template_directory_uri(); ?>/js/{chunk}"
#         else:
#             return f"/wp-content/themes/{THEME_NAME}/js/{chunk}"

#     # Rewrite URLs in all files
#     for root, dirs, files in os.walk(OUTPUT_DIR):
#         for fname in files:
#             fpath = os.path.join(root, fname)
#             with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
#                 content = f.read()

#             # Decide: use PHP (for .php/.html), or static (for .js/.css)
#             is_php = fname.endswith(('.php', '.html'))
#             # Images
#             content = re.sub(
#                 r'https://framerusercontent\.com/([^\'"\)\s]+)',
#                 lambda m: replace_framerusercontent(m, php=is_php),
#                 content
#             )
#             # JS chunks
#             content = re.sub(
#                 r'https://app\.framerstatic\.com/([^\'"\)\s]+)',
#                 lambda m: replace_framerstatic(m, php=is_php),
#                 content
#             )
#             # Fonts in js (optional, if you handle fonts)
#             content = re.sub(
#                 r'<?php echo get_template_directory_uri\(\); \?>/js/([^\'"\)\s]+?\.(?:woff2?|ttf|otf))',
#                 r'<?php echo get_template_directory_uri(); ?>/fonts/\1',
#                 content
#             )

#             with open(fpath, 'w', encoding='utf-8') as f:
#                 f.write(content)


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



                
# def process_links_and_scripts(soup):
#     """
#     Updated to match both framerusercontent.com and framerstatic.com for downloads.
#     """
#     for script in soup.find_all("script", src=True):
#         src = script['src']
#         if ("framerusercontent.com" in src or
#             "framerstatic.com" in src or
#             src.startswith("/")):
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
#         if ("framerusercontent.com" in href or
#             "framerstatic.com" in href or
#             href.startswith("/")):
#             full_url = urljoin(FRAMER_SITE_URL, href)
#             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'css'))
#             if new_path:
#                 # Optional: download_fonts_from_css(new_path)
#                 new_href = "<?php echo get_template_directory_uri(); ?>/css/" + os.path.basename(new_path)
#                 link['href'] = NavigableString(new_href)
#         else:
#             new_href = "<?php echo get_template_directory_uri(); ?>/css/" + os.path.basename(href)
#             link['href'] = NavigableString(new_href)

#     for link in soup.find_all("link", rel="modulepreload", href=True):
#         href = link['href']
#         if ("framerusercontent.com" in href or
#             "framerstatic.com" in href or
#             href.startswith("/")):
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
#         if ("framerusercontent.com" in href or
#             "framerstatic.com" in href or
#             href.startswith("/")):
#             full_url = urljoin(FRAMER_SITE_URL, href)
#             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
#             if new_path:
#                 new_href = "<?php echo get_template_directory_uri(); ?>/images/" + os.path.basename(new_path)
#                 link['href'] = NavigableString(new_href)
#         else:
#             new_href = "<?php echo get_template_directory_uri(); ?>/images/" + os.path.basename(href)
#             link['href'] = NavigableString(new_href)

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
#     # ... (rest of your existing processing steps)
#     # After all processing and saving:
#     with open(os.path.join(OUTPUT_DIR, "index.php"), "w", encoding='utf-8') as f:
#         f.write("<?php get_header(); ?>\n")
#         f.write(soup.prettify(formatter=None))  # Ensures raw PHP in output
#         f.write("\n<?php get_footer(); ?>")



# def zip_theme():
#     zip_name = f"{THEME_NAME}.zip"
#     shutil.make_archive(base_name=THEME_NAME, format='zip', root_dir=OUTPUT_DIR)
#     print(f"🎉 Theme zipped at: {zip_name}")

# def main():
#     print("🚧 Converting Framer site to WordPress theme...")
#     create_theme_structure()
#     parse_and_rewrite_html()
  

#     # After initial parse, crawl all files for extra static/dynamic assets and rewrite URLs
#     recursive_asset_download_and_rewrite()
#     create_wp_files()
#     create_template_parts()
#     zip_theme()
#     # ... (rest of your theme file creation and zipping)
#     print(f"✅ Done! Theme saved in: {OUTPUT_DIR}")

# if __name__ == "__main__":
#     main()




# # import os
# # import requests
# # import shutil
# # from bs4 import BeautifulSoup, Comment,NavigableString
# # from urllib.parse import urljoin
# # import re

# # FRAMER_SITE_URL = "https://precious-adapts-207928.framer.app/"
# # THEME_NAME = "converted-theme"
# # OUTPUT_DIR = os.path.abspath(THEME_NAME)

# # # Remove tags and attributes that are not needed in the WordPress theme
# # def remove_unwanted_meta_and_links(soup):
    
# #     for meta in soup.find_all("meta", {"name": "robots"}):
# #         meta.decompose()
    
# #     for link in soup.find_all("link", {"rel": "canonical"}):
# #         link.decompose()
    
# #     for meta in soup.find_all("meta", {"content": FRAMER_SITE_URL}):
# #         meta.decompose()
    
# #     for link in soup.find_all("link", {"rel": "preconnect", "href": "https://fonts.gstatic.com"}):
# #         link.decompose()
    
# #     for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
# #         if "framer.com" in comment.lower():
# #             comment.extract()


# # def download_fonts_from_html_styles(soup):
 
# #     for style in soup.find_all("style"):
# #         css_content = style.string
# #         if not css_content:
# #             continue
# #         font_urls = re.findall(r"url\(['\"]?(https?://[^'\"\)]+)['\"]?\)", css_content)
# #         for font_url in font_urls:
# #             if font_url.endswith(('.woff', '.woff2', '.ttf', '.otf')):
# #                 local_path = download_file(font_url, os.path.join(OUTPUT_DIR, 'fonts'))
# #                 if local_path:
       
# #                     css_content = css_content.replace(font_url,
# #                         f"<?php echo get_template_directory_uri(); ?>/fonts/{os.path.basename(local_path)}")
     
# #         style.string = css_content


# # def download_fonts_from_css(css_path):

# #     with open(css_path, 'r', encoding='utf-8') as f:
# #         css_content = f.read()
 
# #     font_urls = re.findall(r"url\(['\"]?(https?://[^'\"\)]+)['\"]?\)", css_content)
# #     for font_url in font_urls:
       
# #         if font_url.endswith(('.woff', '.woff2', '.ttf', '.otf')):
# #             local_path = download_file(font_url, os.path.join(OUTPUT_DIR, 'fonts'))
# #             if local_path:
           
# #                 css_content = css_content.replace(font_url,
# #                     f"<?php echo get_template_directory_uri(); ?>/fonts/{os.path.basename(local_path)}")

# #     with open(css_path, 'w', encoding='utf-8') as f:
# #         f.write(css_content)

# # def remove_mjs_assets(soup):

# #     for script in soup.find_all("script", src=True):
# #         if script['src'].endswith('.mjs') or '.mjs' in script['src']:
# #             script.decompose()

# #     for link in soup.find_all("link", href=True):
# #         if link['href'].endswith('.mjs') or '.mjs' in link['href']:
# #             link.decompose()


# # def create_theme_structure():
# #     for folder in ['js', 'css', 'fonts', 'images', 'template-parts']:
# #         os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)

# # def download_file(url, folder):
# #     local_filename = url.split('/')[-1].split('?')[0]
# #     path = os.path.join(folder, local_filename)
# #     try:
# #         r = requests.get(url, stream=True, timeout=10)
# #         if r.status_code == 200:
# #             with open(path, 'wb') as f:
# #                 f.write(r.content)
# #             print(f"✔️  Downloaded: {local_filename}")
# #             return path
# #     except Exception as e:
# #         print(f"⚠️  Failed to download {url}: {e}")
# #     return None

# # def process_links_and_scripts(soup):
   
# #     for script in soup.find_all("script", src=True):
# #         src = script['src']
# #         if "framerusercontent.com" in src or src.startswith("/"):
# #             full_url = urljoin(FRAMER_SITE_URL, src)
# #             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'js'))
# #             if new_path:
# #                 new_src = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(new_path)
# #                 script['src'] = NavigableString(new_src)
           
# #                 if new_path.endswith('.mjs'):
# #                     script['type'] = "module"
# #         else:
       
# #             new_src = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(src)
# #             script['src'] = NavigableString(new_src)
# #             if src.endswith('.mjs'):
# #                 script['type'] = "module"


# #     for link in soup.find_all("link", rel="stylesheet", href=True):
# #         href = link['href']
# #         if "framerusercontent.com" in href or href.startswith("/"):
# #             full_url = urljoin(FRAMER_SITE_URL, href)
# #             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'css'))
# #             if new_path:
# #                 download_fonts_from_css(new_path) 
# #                 new_href = "<?php echo get_template_directory_uri(); ?>/css/" + os.path.basename(new_path)
# #                 link['href'] = NavigableString(new_href)
# #         else:
        
# #             new_href = "<?php echo get_template_directory_uri(); ?>/css/" + os.path.basename(href)
# #             link['href'] = NavigableString(new_href)


# #     for link in soup.find_all("link", rel="modulepreload", href=True):
# #         href = link['href']
# #         if "framerusercontent.com" in href or href.startswith("/"):
# #             full_url = urljoin(FRAMER_SITE_URL, href)
# #             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'js'))
# #             if new_path:
# #                 new_href = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(new_path)
# #                 link['href'] = NavigableString(new_href)
# #         else:
# #             new_href = "<?php echo get_template_directory_uri(); ?>/js/" + os.path.basename(href)
# #             link['href'] = NavigableString(new_href)


# #     for link in soup.find_all("link", rel=lambda v: v and "icon" in v, href=True):
# #         href = link['href']
# #         if "framerusercontent.com" in href or href.startswith("/"):
# #             full_url = urljoin(FRAMER_SITE_URL, href)
# #             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
# #             if new_path:
# #                 new_href = "<?php echo get_template_directory_uri(); ?>/images/" + os.path.basename(new_path)
# #                 link['href'] = NavigableString(new_href)
# #         else:
# #             new_href = "<?php echo get_template_directory_uri(); ?>/images/" + os.path.basename(href)
# #             link['href'] = NavigableString(new_href)



# # def download_images_from_external_sources(soup):
# #     for img in soup.find_all("img", src=True):
# #         src = img['src']
# #         if "framerusercontent.com" in src:
# #             full_url = urljoin(FRAMER_SITE_URL, src)
# #             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
# #             if new_path:
# #                 img['src'] = f"<?php echo get_template_directory_uri(); ?>/images/{os.path.basename(new_path)}"
# #         elif src:
# #             img['src'] = urljoin(FRAMER_SITE_URL, src)

# # def update_meta_tags_and_open_graph(soup):
# #     for meta in soup.find_all("meta", content=True):
# #         content = meta.get("content")
# #         if content and "framerusercontent.com" in content:
# #             full_url = urljoin(FRAMER_SITE_URL, content)
# #             new_path = download_file(full_url, os.path.join(OUTPUT_DIR, 'images'))
# #             if new_path:
# #                 meta['content'] = f"<?php echo get_template_directory_uri(); ?>/images/{os.path.basename(new_path)}"

# # def parse_and_rewrite_html():
# #     response = requests.get(FRAMER_SITE_URL)
# #     if response.status_code != 200:
# #         print("❌ Failed to load Framer URL")
# #         return

# #     soup = BeautifulSoup(response.text, "html.parser")

# #     process_links_and_scripts(soup)
# #     download_images_from_external_sources(soup)
# #     update_meta_tags_and_open_graph(soup)
# #     download_fonts_from_html_styles(soup)
# #     remove_unwanted_meta_and_links(soup)
# #     remove_mjs_assets(soup) 

# #     # Write to index.php
# #     # with open(os.path.join(OUTPUT_DIR, "index.php"), "w", encoding='utf-8') as f:
# #     #     f.write("<?php get_header(); ?>\n")
# #     #     f.write(soup.prettify())
# #     #     f.write("\n<?php get_footer(); ?>")

# #     with open(os.path.join(OUTPUT_DIR, "index.php"), "w", encoding='utf-8') as f:
# #         f.write("<?php get_header(); ?>\n")
# #         f.write(soup.prettify(formatter=None))  # Ensures raw PHP in output
# #         f.write("\n<?php get_footer(); ?>")

# # def create_wp_files():
# #     style_css = f"""/*
# # Theme Name: {THEME_NAME}
# # Author: SourceSelect.ca
# # Version: 1.0
# # */"""

# #     header_php = """<!DOCTYPE html>
# # <html <?php language_attributes(); ?>>
# # <head>
# #     <meta charset="<?php bloginfo('charset'); ?>">
# #     <?php wp_head(); ?>
# # </head>
# # <body <?php body_class(); ?>>
# # <header><h1><?php bloginfo('name'); ?></h1></header>
# # """

# #     footer_php = """<footer><p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?></p></footer>
# # <?php wp_footer(); ?>
# # </body>
# # </html>
# # """

# #     functions_php_content = """<?php
# # function theme_enqueue_scripts() {
# #     wp_enqueue_style('main-style', get_template_directory_uri() . '/css/style.css', array(), false);
# #     foreach (glob(get_template_directory() . '/js/*.js') as $js_file) {
# #         wp_enqueue_script(basename($js_file), get_template_directory_uri() . '/js/' . basename($js_file), array(), false, true);
# #     }
# #     foreach (glob(get_template_directory() . '/js/*.mjs') as $mjs_file) {
# #         wp_enqueue_script(basename($mjs_file), get_template_directory_uri() . '/js/' . basename($mjs_file), array(), false, true);
# #     }
# # }

# # add_filter('script_loader_tag', function($tag, $handle, $src) {
# #     if (strpos($src, '.mjs') !== false) {
# #         $tag = '<script type="module" src="' . esc_url($src) . '"></script>';
# #     }
# #     return $tag;
# # }, 10, 3);

# # add_action( 'wp_enqueue_scripts', 'theme_enqueue_scripts' );
# # """

# #     with open(os.path.join(OUTPUT_DIR, "style.css"), "w", encoding="utf-8") as f:
# #         f.write(style_css)

# #     with open(os.path.join(OUTPUT_DIR, "header.php"), "w", encoding="utf-8") as f:
# #         f.write(header_php)

# #     with open(os.path.join(OUTPUT_DIR, "footer.php"), "w", encoding="utf-8") as f:
# #         f.write(footer_php)

# #     with open(os.path.join(OUTPUT_DIR, "functions.php"), "w", encoding="utf-8") as f:
# #         f.write(functions_php_content)

        

# # def create_template_parts():
# #     content_template = """<?php
# # /**
# #  * Template part for displaying page content
# #  */
# # ?>

# # <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
# # <?php the_content(); ?>
# # </article>
# # """
# #     os.makedirs(os.path.join(OUTPUT_DIR, "template-parts"), exist_ok=True)
# #     with open(os.path.join(OUTPUT_DIR, "template-parts", "content-page.php"), "w", encoding="utf-8") as f:
# #         f.write(content_template)

# #     print(f"✔️ Template parts created.")

# # def zip_theme():
# #     zip_name = f"{THEME_NAME}.zip"
# #     shutil.make_archive(base_name=THEME_NAME, format='zip', root_dir=OUTPUT_DIR)
# #     print(f"🎉 Theme zipped at: {zip_name}")

# # def main():
# #     print("🚧 Converting Framer site to WordPress theme...")
# #     create_theme_structure()
# #     parse_and_rewrite_html()
# #     create_wp_files()
# #     create_template_parts()
# #     zip_theme()
# #     print(f"✅ Done! Theme saved in: {OUTPUT_DIR}")

# # if __name__ == "__main__":
# #     main()


import os
import re
import requests
import shutil
import time
from bs4 import BeautifulSoup, Comment, NavigableString
from urllib.parse import urljoin, urlparse, urlunparse
import hashlib
from pathlib import Path

# Configuration
FRAMER_SITE_URL = "https://trusting-evidence-175718-1fc5116ff.framer.app/"  # Replace with your Framer site URL
THEME_NAME = "FramerConvertedTheme"
OUTPUT_DIR = os.path.join(os.getcwd(), THEME_NAME)

# Social media domains to skip
SOCIAL_MEDIA_DOMAINS = [
    'facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'linkedin.com',
    'pinterest.com', 'youtube.com', 'tiktok.com', 'snapchat.com', 'whatsapp.com',
    'telegram.org', 'discord.com', 'reddit.com', 'tumblr.com', 'flickr.com',
    'vimeo.com', 'twitch.tv', 'medium.com', 'behance.net', 'dribbble.com',
    'github.com', 'gitlab.com', 'bitbucket.org', 'slack.com', 'mastodon.social'
]

# Create a session for persistent connections with retry capability
session = requests.Session()
session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

# Track downloaded resources to avoid duplicates
downloaded_resources = set()

def is_social_media_url(url):
    """Check if a URL is a social media link that should be skipped"""
    if not url or not isinstance(url, str):
        return False
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check if this is a social media domain
        for social_domain in SOCIAL_MEDIA_DOMAINS:
            if social_domain in domain:
                return True
                
        # Also skip common social media share links
        social_path_indicators = ['/share/', '/sharing/', '/share.php', '/like.php', '/follow.php']
        if any(indicator in parsed_url.path for indicator in social_path_indicators):
            return True
            
        # Skip mailto links
        if url.startswith('mailto:'):
            return True
            
        # Skip tel links
        if url.startswith('tel:'):
            return True
            
    except Exception:
        pass
        
    return False

def robust_request(url, max_retries=5, timeout=30):
    """Make HTTP requests with retry logic"""
    # Skip social media URLs entirely
    if is_social_media_url(url):
        print(f"⏭️  Skipping social media URL: {url}")
        return None
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=timeout, stream=True)
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                print(f"⚠️  Resource not found: {url}")
                return None
            else:
                print(f"⚠️  HTTP {response.status_code} for {url}, attempt {attempt + 1}")
        except Exception as e:
            print(f"⚠️  Request failed for {url}: {e}, attempt {attempt + 1}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    print(f"❌ Failed to retrieve {url} after {max_retries} attempts")
    return None

def download_file_with_retry(url, folder, max_retries=3):
    """Download a file with retry logic and return its local path"""
    if url in downloaded_resources:
        return None
        
    # Skip social media URLs
    if is_social_media_url(url):
        print(f"⏭️  Skipping social media resource: {url}")
        return None
        
    downloaded_resources.add(url)
    
    try:
        # Clean URL and create filename
        parsed_url = urlparse(url)
        path = parsed_url.path
        filename = os.path.basename(path)
        
        # If no proper filename, create one based on content type and URL hash
        if not filename or '.' not in filename or len(filename) > 100:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            
            # Try to determine file type from URL pattern or content
            if any(x in url for x in ['.css', '/css', 'style']):
                filename = f"{url_hash}.css"
            elif any(x in url for x in ['.js', '/js', 'script']):
                filename = f"{url_hash}.js"
            elif any(x in url for x in ['.png', '/image', 'img']):
                filename = f"{url_hash}.png"
            elif any(x in url for x in ['.jpg', '.jpeg', 'jpeg']):
                filename = f"{url_hash}.jpg"
            elif any(x in url for x in ['.svg', 'vector']):
                filename = f"{url_hash}.svg"
            elif any(x in url for x in ['.woff', 'font']):
                filename = f"{url_hash}.woff"
            elif any(x in url for x in ['.woff2']):
                filename = f"{url_hash}.woff2"
            elif any(x in url for x in ['.ttf']):
                filename = f"{url_hash}.ttf"
            elif any(x in url for x in ['.eot']):
                filename = f"{url_hash}.eot"
            else:
                filename = f"{url_hash}.bin"
        
        local_path = os.path.join(folder, filename)
        
        # Check if file already exists
        if os.path.exists(local_path):
            return local_path
        
        # Download the file with retries
        for attempt in range(max_retries):
            try:
                response = robust_request(url)
                if response and response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✔️  Downloaded: {filename} from {url}")
                    return local_path
            except Exception as e:
                print(f"⚠️  Download failed for {url}: {e}, attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        print(f"❌ Failed to download {url} after {max_retries} attempts")
        return None
        
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return None

def create_theme_structure():
    """Create the necessary folder structure for the WordPress theme"""
    for folder in ['js', 'css', 'fonts', 'images', 'template-parts', 'assets']:
        os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)

def remove_unwanted_meta_and_links(soup):
    """Remove tags and attributes that are not needed in the WordPress theme"""
    # Remove Framer-specific meta tags
    for meta in soup.find_all("meta"):
        if (meta.get('name') in ['robots', 'framer', 'generator'] or 
            meta.get('property', '').startswith('framer:') or
            'framer' in str(meta.get('content', '')).lower()):
            meta.decompose()
    
    # Remove Framer-specific links
    for link in soup.find_all("link"):
        if (link.get('rel') in [['canonical'], ['manifest']] or 
            any(x in str(link.get('href', '')).lower() for x in ['framer', 'static'])):
            link.decompose()
    
    # Remove Framer comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if 'framer' in comment.lower():
            comment.extract()
    
    # Remove Framer-specific scripts
    for script in soup.find_all("script"):
        src = script.get('src', '')
        if src and any(x in src for x in ['framerstatic.com', 'framerusercontent.com']):
            script.decompose()
        elif script.string and 'Framer' in script.string:
            script.decompose()

def extract_all_urls_from_content(content, base_url):
    """Extract all URLs from HTML, CSS, or JS content"""
    urls = set()
    
    # Patterns for different types of URLs
    patterns = [
        r'url\([\'"]?([^\'"\)]+)[\'"]?\)',  # CSS url()
        r'src=[\'"]([^\'"]+)[\'"]',         # HTML src attribute
        r'href=[\'"]([^\'"]+)[\'"]',        # HTML href attribute
        r'@import\s+[\'"]([^\'"]+)[\'"]',   # CSS @import
        r'import\s+[\'"]([^\'"]+)[\'"]',    # JS import
        r'fetch\([\'"]([^\'"]+)[\'"]',      # JS fetch
        r'new\s+URL\([\'"]([^\'"]+)[\'"]',  # JS new URL
        r'["\']([^"\']+\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot))["\']',  # General file references
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            # Handle both string matches and tuple matches from groups
            url = match if isinstance(match, str) else match[0] if match else None
            if url and not url.startswith(('data:', '#')) and not url.startswith(('http', '//')):
                # Convert relative URLs to absolute
                if url.startswith('/'):
                    full_url = urljoin(base_url, url)
                else:
                    # For relative paths, join with base URL
                    full_url = urljoin(base_url + '/', url)
                
                # Skip social media URLs
                if not is_social_media_url(full_url):
                    urls.add(full_url)
            elif url and any(x in url for x in ['framerstatic.com', 'framerusercontent.com']):
                # Skip social media URLs
                if not is_social_media_url(url):
                    urls.add(url)
    
    return urls

def download_all_assets(soup, base_url):
    """Download all assets found in the HTML"""
    print("🔍 Searching for assets to download...")
    
    # Download CSS files
    for link in soup.find_all("link", rel="stylesheet", href=True):
        href = link['href']
        if href.startswith(('http', '//')) or href.startswith('/'):
            full_url = urljoin(base_url, href)
            css_path = download_file_with_retry(full_url, os.path.join(OUTPUT_DIR, 'css'))
            if css_path:
                link['href'] = f"<?php echo get_template_directory_uri(); ?>/css/{os.path.basename(css_path)}"
                # Process CSS file to extract nested assets
                process_file_for_assets(css_path, base_url)
    
    # Download JS files
    for script in soup.find_all("script", src=True):
        src = script['src']
        if src.startswith(('http', '//')) or src.startswith('/'):
            full_url = urljoin(base_url, src)
            js_path = download_file_with_retry(full_url, os.path.join(OUTPUT_DIR, 'js'))
            if js_path:
                script['src'] = f"<?php echo get_template_directory_uri(); ?>/js/{os.path.basename(js_path)}"
                if js_path.endswith('.mjs'):
                    script['type'] = 'module'
                # Process JS file to extract nested assets
                process_file_for_assets(js_path, base_url)
    
    # Download images
    for img in soup.find_all("img", src=True):
        src = img['src']
        if src.startswith(('http', '//')) or src.startswith('/'):
            full_url = urljoin(base_url, src)
            img_path = download_file_with_retry(full_url, os.path.join(OUTPUT_DIR, 'images'))
            if img_path:
                img['src'] = f"<?php echo get_template_directory_uri(); ?>/images/{os.path.basename(img_path)}"
    
    # Download favicons and other icons
    for link in soup.find_all("link", href=True):
        rel = link.get('rel', [])
        href = link.get('href', '')
        if (any(x in rel for x in ['icon', 'apple-touch-icon', 'manifest', 'mask-icon', 'stylesheet']) or
            any(x in href for x in ['.ico', '.png', '.jpg', '.svg'])):
            if href.startswith(('http', '//')) or href.startswith('/'):
                full_url = urljoin(base_url, href)
                icon_path = download_file_with_retry(full_url, os.path.join(OUTPUT_DIR, 'images'))
                if icon_path:
                    link['href'] = f"<?php echo get_template_directory_uri(); ?>/images/{os.path.basename(icon_path)}"
    
    # Process inline styles for font references
    for style in soup.find_all("style"):
        if style.string:
            # Extract font URLs from inline CSS
            css_content = style.string
            font_urls = extract_all_urls_from_content(css_content, base_url)
            
            for font_url in font_urls:
                if any(x in font_url for x in ['.woff', '.woff2', '.ttf', '.otf', '.eot']):
                    font_path = download_file_with_retry(font_url, os.path.join(OUTPUT_DIR, 'fonts'))
                    if font_path:
                        filename = os.path.basename(font_path)
                        replacement = f"<?php echo get_template_directory_uri(); ?>/fonts/{filename}"
                        css_content = css_content.replace(font_url, replacement)
            
            # Update the style tag content
            style.string = css_content
    
    # Process meta tags for social images
    for meta in soup.find_all("meta", content=True):
        content = meta.get("content", "")
        if any(x in content for x in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
            if content.startswith(('http', '//')) or content.startswith('/'):
                full_url = urljoin(base_url, content)
                meta_path = download_file_with_retry(full_url, os.path.join(OUTPUT_DIR, 'images'))
                if meta_path:
                    meta['content'] = f"<?php echo get_template_directory_uri(); ?>/images/{os.path.basename(meta_path)}"

def process_file_for_assets(file_path, base_url):
    """Process a file (CSS/JS) to extract and download nested assets"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find all asset URLs in the file
        asset_urls = extract_all_urls_from_content(content, base_url)
        
        for url in asset_urls:
            # Skip social media URLs
            if is_social_media_url(url):
                continue
                
            # Determine the appropriate folder based on file type
            if any(x in url for x in ['.woff', '.woff2', '.ttf', '.otf', '.eot']):
                folder = os.path.join(OUTPUT_DIR, 'fonts')
            elif any(x in url for x in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.ico']):
                folder = os.path.join(OUTPUT_DIR, 'images')
            elif any(x in url for x in ['.css']):
                folder = os.path.join(OUTPUT_DIR, 'css')
            elif any(x in url for x in ['.js', '.mjs']):
                folder = os.path.join(OUTPUT_DIR, 'js')
            else:
                folder = os.path.join(OUTPUT_DIR, 'assets')
            
            # Download the asset
            local_path = download_file_with_retry(url, folder)
            if local_path:
                # Create the replacement URL
                filename = os.path.basename(local_path)
                if folder.endswith('fonts'):
                    replacement = f"<?php echo get_template_directory_uri(); ?>/fonts/{filename}"
                elif folder.endswith('images'):
                    replacement = f"<?php echo get_template_directory_uri(); ?>/images/{filename}"
                elif folder.endswith('css'):
                    replacement = f"<?php echo get_template_directory_uri(); ?>/css/{filename}"
                elif folder.endswith('js'):
                    replacement = f"<?php echo get_template_directory_uri(); ?>/js/{filename}"
                else:
                    replacement = f"<?php echo get_template_directory_uri(); ?>/assets/{filename}"
                
                # Replace the URL in the content
                content = content.replace(url, replacement)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        print(f"⚠️  Error processing file {file_path}: {e}")

def crawl_page(url, depth=0, max_depth=2):
    """Crawl a page and its linked resources"""
    if depth > max_depth or url in downloaded_resources:
        return None
    
    # Skip social media URLs
    if is_social_media_url(url):
        print(f"⏭️  Skipping social media page: {url}")
        return None
    
    print(f"🌐 Crawling: {url} (depth {depth})")
    
    response = robust_request(url)
    if not response:
        return None
    
    # Determine content type and handle accordingly
    content_type = response.headers.get('content-type', '').lower()
    
    if 'text/html' in content_type:
        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted Framer-specific tags
        remove_unwanted_meta_and_links(soup)
        
        # Download all assets
        download_all_assets(soup, url)
        
        # Find and follow links for further crawling (skip social media links)
        if depth < max_depth:
            for link in soup.find_all("a", href=True):
                href = link['href']
                if href.startswith(('http', '//')):
                    # Skip social media URLs
                    if not is_social_media_url(href):
                        crawl_page(href, depth + 1, max_depth)
                elif href.startswith('/'):
                    # Root-relative URL
                    parsed_url = urlparse(url)
                    absolute_url = f"{parsed_url.scheme}://{parsed_url.netloc}{href}"
                    # Skip social media URLs
                    if not is_social_media_url(absolute_url):
                        crawl_page(absolute_url, depth + 1, max_depth)
        
        return soup
    else:
        # Handle non-HTML content (download directly)
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        if not filename:
            filename = hashlib.md5(url.encode()).hexdigest()[:12]
            if 'css' in content_type:
                filename += '.css'
            elif 'javascript' in content_type:
                filename += '.js'
            elif 'image' in content_type:
                filename += '.png'
        
        # Determine folder based on content type
        if 'css' in content_type:
            folder = os.path.join(OUTPUT_DIR, 'css')
        elif 'javascript' in content_type:
            folder = os.path.join(OUTPUT_DIR, 'js')
        elif 'image' in content_type:
            folder = os.path.join(OUTPUT_DIR, 'images')
        elif 'font' in content_type:
            folder = os.path.join(OUTPUT_DIR, 'fonts')
        else:
            folder = os.path.join(OUTPUT_DIR, 'assets')
        
        # Save the file
        local_path = os.path.join(folder, filename)
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✔️  Downloaded: {filename} from {url}")
        return local_path

def create_wp_files():
    """Create the necessary WordPress theme files"""
    style_css = f"""/*
Theme Name: {THEME_NAME}
Author: SourceSelect.ca
Description: Theme converted from Framer
Version: 1.0
License: GNU General Public License v2 or later
Text Domain: {THEME_NAME.lower()}
*/"""

    header_php = """<!DOCTYPE html>
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
    <a class="skip-link screen-reader-text" href="#content"><?php esc_html_e('Skip to content', 'textdomain'); ?></a>
    <header id="masthead" class="site-header">
        <div class="site-branding">
            <?php
            if (has_custom_logo()) {
                the_custom_logo();
            } else {
                ?>
                <h1 class="site-title"><a href="<?php echo esc_url(home_url('/')); ?>" rel="home"><?php bloginfo('name'); ?></a></h1>
                <p class="site-description"><?php bloginfo('description'); ?></p>
                <?php
            }
            ?>
        </div>
        <nav id="site-navigation" class="main-navigation">
            <button class="menu-toggle" aria-controls="primary-menu" aria-expanded="false"><?php esc_html_e('Menu', 'textdomain'); ?></button>
            <?php
            wp_nav_menu(array(
                'theme_location' => 'menu-1',
                'menu_id'        => 'primary-menu',
                'menu_class'     => 'nav-menu',
            ));
            ?>
        </nav>
    </header>
    <div id="content" class="site-content">
"""

    footer_php = """    </div>
    <footer id="colophon" class="site-footer">
        <div class="site-info">
            <p>&copy; <?php echo date('Y'); ?> <a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a></p>
        </div>
    </footer>
</div>
<?php wp_footer(); ?>
</body>
</html>
"""

    functions_php_content = """<?php
function theme_enqueue_scripts() {
    // Enqueue styles
    $css_files = glob(get_template_directory() . '/css/*.css');
    foreach ($css_files as $css_file) {
        $handle = 'theme-' . basename($css_file, '.css');
        wp_enqueue_style($handle, get_template_directory_uri() . '/css/' . basename($css_file), array(), filemtime($css_file));
    }
    
    // Enqueue scripts
    $js_files = glob(get_template_directory() . '/js/*.js');
    foreach ($js_files as $js_file) {
        $handle = 'theme-' . basename($js_file, '.js');
        wp_enqueue_script($handle, get_template_directory_uri() . '/js/' . basename($js_file), array(), filemtime($js_file), true);
    }
    
    // Enqueue module scripts
    $mjs_files = glob(get_template_directory() . '/js/*.mjs');
    foreach ($mjs_files as $mjs_file) {
        $handle = 'theme-' . basename($mjs_file, '.mjs');
        wp_enqueue_script($handle, get_template_directory_uri() . '/js/' . basename($mjs_file), array(), filemtime($mjs_file), true);
    }
}

add_filter('script_loader_tag', function($tag, $handle, $src) {
    if (strpos($src, '.mjs') !== false) {
        $tag = '<script type="module" src="' . esc_url($src) . '" id="' . $handle . '-js"></script>';
    }
    return $tag;
}, 10, 3);

add_action('wp_enqueue_scripts', 'theme_enqueue_scripts');

// Register navigation menus
function theme_register_menus() {
    register_nav_menus(array(
        'menu-1' => esc_html__('Primary Menu', 'textdomain'),
    ));
}
add_action('init', 'theme_register_menus');

// Add theme support
function theme_setup() {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('custom-logo', array(
        'height'      => 100,
        'width'       => 400,
        'flex-height' => true,
        'flex-width'  => true,
    ));
    add_theme_support('html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
    ));
    add_theme_support('custom-background');
}
add_action('after_setup_theme', 'theme_setup');

// Add editor styles
function theme_add_editor_styles() {
    add_editor_style('css/editor-style.css');
}
add_action('admin_init', 'theme_add_editor_styles');
"""

    index_php = """<?php
/**
 * The main template file
 *
 * @package <?php echo THEME_NAME; ?>
 */
get_header();
?>

<main id="main" class="site-main">
    <?php if (have_posts()) : ?>
        <?php while (have_posts()) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                <header class="entry-header">
                    <?php the_title('<h1 class="entry-title">', '</h1>'); ?>
                </header>
                <div class="entry-content">
                    <?php the_content(); ?>
                </div>
            </article>
        <?php endwhile; ?>
    <?php else : ?>
        <article>
            <header class="entry-header">
                <h1 class="entry-title"><?php esc_html_e('Nothing Found', 'textdomain'); ?></h1>
            </header>
            <div class="entry-content">
                <p><?php esc_html_e('No content found.', 'textdomain'); ?></p>
            </div>
        </article>
    <?php endif; ?>
</main>

<?php
get_footer();
"""

    # Create the theme files
    with open(os.path.join(OUTPUT_DIR, "style.css"), "w", encoding="utf-8") as f:
        f.write(style_css)

    with open(os.path.join(OUTPUT_DIR, "header.php"), "w", encoding="utf-8") as f:
        f.write(header_php)

    with open(os.path.join(OUTPUT_DIR, "footer.php"), "w", encoding="utf-8") as f:
        f.write(footer_php)

    with open(os.path.join(OUTPUT_DIR, "functions.php"), "w", encoding="utf-8") as f:
        f.write(functions_php_content)

    with open(os.path.join(OUTPUT_DIR, "index.php"), "w", encoding="utf-8") as f:
        f.write(index_php)

    # Create additional theme files
    with open(os.path.join(OUTPUT_DIR, "404.php"), "w", encoding="utf-8") as f:
        f.write("""<?php
/**
 * The template for displaying 404 pages (not found)
 */
get_header();
?>
<main id="main" class="site-main">
    <article>
        <header class="entry-header">
            <h1 class="entry-title"><?php esc_html_e('Page Not Found', 'textdomain'); ?></h1>
        </header>
        <div class="entry-content">
            <p><?php esc_html_e('The page you are looking for does not exist.', 'textdomain'); ?></p>
            <?php get_search_form(); ?>
        </div>
    </article>
</main>
<?php get_footer(); ?>
""")

    with open(os.path.join(OUTPUT_DIR, "search.php"), "w", encoding="utf-8") as f:
        f.write("""<?php
/**
 * The template for displaying search results
 */
get_header();
?>
<main id="main" class="site-main">
    <header class="page-header">
        <h1 class="page-title">
            <?php printf(esc_html__('Search Results for: %s', 'textdomain'), '<span>' . get_search_query() . '</span>'); ?>
        </h1>
    </header>
    <?php if (have_posts()) : ?>
        <?php while (have_posts()) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                <header class="entry-header">
                    <h2 class="entry-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                </header>
                <div class="entry-summary">
                    <?php the_excerpt(); ?>
                </div>
            </article>
        <?php endwhile; ?>
        <?php the_posts_navigation(); ?>
    <?php else : ?>
        <article>
            <p><?php esc_html_e('No results found.', 'textdomain'); ?></p>
        </article>
    <?php endif; ?>
</main>
<?php get_footer(); ?>
""")

def create_template_parts():
    """Create template parts for the WordPress theme"""
    content_template = """<?php
/**
 * Template part for displaying page content
 */
?>

<article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
    <header class="entry-header">
        <?php the_title('<h1 class="entry-title">', '</h1>'); ?>
    </header>
    <div class="entry-content">
        <?php the_content(); ?>
        <?php
        wp_link_pages(array(
            'before' => '<div class="page-links">' . esc_html_e('Pages:', 'textdomain'),
            'after'  => '</div>',
        ));
        ?>
    </div>
</article>
"""
    os.makedirs(os.path.join(OUTPUT_DIR, "template-parts"), exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "template-parts", "content-page.php"), "w", encoding="utf-8") as f:
        f.write(content_template)

    print("✔️ Template parts created.")

def zip_theme():
    """Create a zip file of the theme"""
    zip_name = f"{THEME_NAME}.zip"
    shutil.make_archive(base_name=THEME_NAME, format='zip', root_dir=OUTPUT_DIR)
    print(f"🎉 Theme zipped at: {zip_name}")

def main():
    """Main function to convert Framer site to WordPress theme"""
    print("🚧 Converting Framer site to WordPress theme...")
    print("⏰ This may take several minutes depending on the site size...")
    print("⏭️  Social media links will be skipped...")
    
    # Create theme structure
    create_theme_structure()
    
    # Start crawling from the main URL
    soup = crawl_page(FRAMER_SITE_URL, max_depth=3)
    
    if soup:
        # Save the main HTML content
        with open(os.path.join(OUTPUT_DIR, "index.php"), "w", encoding="utf-8") as f:
            f.write("<?php get_header(); ?>\n")
            f.write(str(soup))
            f.write("\n<?php get_footer(); ?>")
    
    # Create WordPress theme files
    create_wp_files()
    create_template_parts()
    
    # Zip the theme
    zip_theme()
    
    print(f"✅ Done! Theme saved in: {OUTPUT_DIR}")
    print("📦 Install the theme zip file in WordPress")
    print("⚙️  You may need to adjust some styles in the CSS files")

if __name__ == "__main__":
    main()