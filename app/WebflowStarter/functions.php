<?php
/**
 * WebflowStarter functions and definitions
 *
 * @link https://developer.wordpress.org/themes/basics/theme-functions/
 *
 * @package WebflowStarter
 */

if (!function_exists('webflowstarter_setup')):
	/**
	 * Sets up theme defaults and registers support for various WordPress features.
	 *
	 * Note that this function is hooked into the after_setup_theme hook, which
	 * runs before the init hook. The init hook is too late for some features, such
	 * as indicating support for post thumbnails.
	 */
	function webflowstarter_setup()
	{
		/*
		 * Make theme available for translation.
		 * Translations can be filed in the /languages/ directory.
		 * If you're building a theme based on WebflowStarter, use a find and replace
		 * to change 'webflowstarter' to the name of your theme in all the template files.
		 */
		load_theme_textdomain('webflowstarter', get_template_directory() . '/languages');

		// Add default posts and comments RSS feed links to head.
		add_theme_support('automatic-feed-links');

		/*
		 * Let WordPress manage the document title.
		 * By adding theme support, we declare that this theme does not use a
		 * hard-coded <title> tag in the document head, and expect WordPress to
		 * provide it for us.
		 */
		add_theme_support('title-tag');

		/*
		 * Enable support for Post Thumbnails on posts and pages.
		 *
		 * @link https://developer.wordpress.org/themes/functionality/featured-images-post-thumbnails/
		 */
		add_theme_support('post-thumbnails');

		// This theme uses wp_nav_menu() in one location.
		register_nav_menus(array(
			'menu-1' => esc_html__('Primary', 'webflowstarter'),
		));

		/*
		 * Switch default core markup for search form, comment form, and comments
		 * to output valid HTML5.
		 */
		add_theme_support('html5', array(
			'search-form',
			'comment-form',
			'comment-list',
			'gallery',
			'caption',
		));

		// Set up the WordPress core custom background feature.
		add_theme_support('custom-background', apply_filters('webflowstarter_custom_background_args', array(
			'default-color' => 'ffffff',
			'default-image' => '',
		)));

		// Add theme support for selective refresh for widgets.
		add_theme_support('customize-selective-refresh-widgets');

		/**
		 * Add support for core custom logo.
		 *
		 * @link https://codex.wordpress.org/Theme_Logo
		 */
		add_theme_support('custom-logo', array(
			'height' => 250,
			'width' => 250,
			'flex-width' => true,
			'flex-height' => true,
		));
	}
endif;
add_action('after_setup_theme', 'webflowstarter_setup');

/**
 * Set the content width in pixels, based on the theme's design and stylesheet.
 *
 * Priority 0 to make it available to lower priority callbacks.
 *
 * @global int $content_width
 */
function webflowstarter_content_width()
{
	$GLOBALS['content_width'] = apply_filters('webflowstarter_content_width', 640);
}
add_action('after_setup_theme', 'webflowstarter_content_width', 0);

/**
 * Register widget area.
 *
 * @link https://developer.wordpress.org/themes/functionality/sidebars/#registering-a-sidebar
 */
function webflowstarter_widgets_init()
{
	register_sidebar(array(
		'name' => esc_html__('Sidebar', 'webflowstarter'),
		'id' => 'sidebar-1',
		'description' => esc_html__('Add widgets here.', 'webflowstarter'),
		'before_widget' => '<section id="%1$s" class="widget %2$s">',
		'after_widget' => '</section>',
		'before_title' => '<h2 class="widget-title">',
		'after_title' => '</h2>',
	));
}
add_action('widgets_init', 'webflowstarter_widgets_init');

/**
 * Enqueue scripts and styles.
 */
function webflowstarter_scripts()
{
	// Auto-bust style.css cache with last modified time
	wp_enqueue_style(
		'webflowstarter-style',
		get_stylesheet_uri(),
		array(),
		filemtime(get_stylesheet_directory() . '/style.css')
	);

	// Optional: Apply same to other styles
	wp_register_style(
		'styleguide',
		get_template_directory_uri() . '/styleguide.css',
		array(),
		file_exists(get_template_directory() . '/styleguide.css') ? filemtime(get_template_directory() . '/styleguide.css') : null,
		'all'
	);
	wp_enqueue_style('styleguide');

	wp_register_style(
		'theme',
		get_template_directory_uri() . '/theme.css',
		array(),
		file_exists(get_template_directory() . '/theme.css') ? filemtime(get_template_directory() . '/theme.css') : null,
		'all'
	);
	wp_enqueue_style('theme');

	// JS
	wp_enqueue_script(
		'webflowstarter-navigation',
		get_template_directory_uri() . '/js/navigation.js',
		array(),
		file_exists(get_template_directory() . '/js/navigation.js') ? filemtime(get_template_directory() . '/js/navigation.js') : null,
		true
	);

	wp_enqueue_script(
		'webflowstarter-skip-link-focus-fix',
		get_template_directory_uri() . '/js/skip-link-focus-fix.js',
		array(),
		file_exists(get_template_directory() . '/js/skip-link-focus-fix.js') ? filemtime(get_template_directory() . '/js/skip-link-focus-fix.js') : null,
		true
	);

	if (is_singular() && comments_open() && get_option('thread_comments')) {
		wp_enqueue_script('comment-reply');
	}
}

add_action('wp_enqueue_scripts', 'webflowstarter_scripts');

/**
 * Implement the Custom Header feature.
 */
require get_template_directory() . '/inc/custom-header.php';

/**
 * Custom template tags for this theme.
 */
require get_template_directory() . '/inc/template-tags.php';

/**
 * Functions which enhance the theme by hooking into WordPress.
 */
require get_template_directory() . '/inc/template-functions.php';

/**
 * Customizer additions.
 */
require get_template_directory() . '/inc/customizer.php';

/**
 * Load Jetpack compatibility file.
 */
if (defined('JETPACK__VERSION')) {
	require get_template_directory() . '/inc/jetpack.php';
}


/**
 * AUTO-INSTALL PLUGINS WHEN THEME ACTIVATES
 */
function webflow_auto_setup()
{
	// 1. Setup file paths
	$acf_zip = get_template_directory() . '/includes/plugins/advanced-custom-fields-pro.zip';
	$importer_zip = get_template_directory() . '/includes/plugins/webflow-importer.zip';

	// 2. Load WordPress plugin installer
	if (!function_exists('install_plugin_install_status')) {
		require_once ABSPATH . 'wp-admin/includes/plugin.php';
		require_once ABSPATH . 'wp-admin/includes/file.php';
		require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
	}

	// 3. Install ACF Pro
	if (!is_plugin_active('advanced-custom-fields-pro/acf.php')) {
		if (file_exists($acf_zip)) {
			$upgrader = new Plugin_Upgrader(new WP_Ajax_Upgrader_Skin());
			$upgrader->install($acf_zip);
			activate_plugin('advanced-custom-fields-pro/acf.php');
		}
	}

	// 4. Install Webflow Importer
	if (!is_plugin_active('webflow-importer/webflow-importer.php')) {
		if (file_exists($importer_zip)) {
			$upgrader = new Plugin_Upgrader(new WP_Ajax_Upgrader_Skin());
			$upgrader->install($importer_zip);
			activate_plugin('webflow-importer/webflow-importer.php');

			// Trigger import if function exists
			if (function_exists('webflow_auto_import_content')) {
				webflow_auto_import_content();
			}
		}
	}
}
add_action('after_switch_theme', 'webflow_auto_setup');