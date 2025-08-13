<?php
/*
Plugin Name: Webflow Magic
Description: Import Webflow CMS content to WordPress with real-time progress tracking
Version: 4.3
Author: SourceSelect.ca
*/

class Webflow_Importer_Complete {
    private $debug_log = [];
    private $first_run = false;
    private static $import_progress = [
        'message' => 'Ready to start import',
        'progress' => 0,
        'log' => []
    ];

    public function __construct() {
        $this->first_run = !get_option('webflow_importer_initialized');
        
        // Setup admin interface
        add_action('admin_menu', [$this, 'add_admin_page']);
        add_action('admin_enqueue_scripts', [$this, 'admin_scripts']);
        
        // AJAX handlers
        add_action('wp_ajax_webflow_import', [$this, 'ajax_import']);
        add_action('wp_ajax_webflow_import_progress', [$this, 'ajax_import_progress']);
        add_action('wp_ajax_webflow_import_cancel', [$this, 'ajax_import_cancel']);
        
        // Post type registration
        register_activation_hook(__FILE__, [$this, 'plugin_activation']);
        add_action('admin_init', [$this, 'maybe_register_post_types']);
        add_action('wp_loaded', [$this, 'maybe_register_post_types']);
        
        // Admin notices
        add_action('admin_notices', [$this, 'show_admin_notices']);
    }

    // 1. PLUGIN ACTIVATION
    public function plugin_activation() {
        update_option('webflow_importer_initialized', true);
        $this->first_run = true;
        $this->register_dynamic_post_types(true);
        flush_rewrite_rules();
    }

    // 2. POST TYPE REGISTRATION
    public function maybe_register_post_types() {
        if ($this->first_run || $this->has_webflow_data()) {
            $this->register_dynamic_post_types();
        }
    }

    private function has_webflow_data() {
        return file_exists($this->get_collections_path());
    }

    private function get_collections_path() {
        return get_template_directory() . '/cms-data/collections.json';
    }

    private function register_dynamic_post_types($force = false) {
        $json_path = $this->get_collections_path();
        
        if ($force || file_exists($json_path)) {
            $collections = [];
            if (file_exists($json_path)) {
                $collections = json_decode(file_get_contents($json_path), true);
                if (json_last_error() !== JSON_ERROR_NONE) {
                    $collections = [];
                }
            }
            
            if (!empty($collections)) {
                foreach ($collections as $collection) {
                    if (empty($collection['name']) || empty($collection['items'])) continue;
                    $this->register_single_post_type($collection);
                }
                return;
            }
        }
        
        $this->register_fallback_post_types();
    }

    private function register_single_post_type($collection) {
        $post_type_slug = 'webflow_' . sanitize_title($collection['name']);
        $post_type_label = ucwords(str_replace('-', ' ', $collection['name']));
        
        $args = [
            'labels' => [
                'name' => $post_type_label,
                'singular_name' => $post_type_label,
                'menu_name' => $post_type_label,
                'all_items' => 'All ' . $post_type_label,
                'add_new' => 'Add New',
                'add_new_item' => 'Add New ' . $post_type_label,
                'edit_item' => 'Edit ' . $post_type_label,
                'new_item' => 'New ' . $post_type_label,
                'view_item' => 'View ' . $post_type_label,
                'search_items' => 'Search ' . $post_type_label,
                'not_found' => 'No ' . $post_type_label . ' found',
                'not_found_in_trash' => 'No ' . $post_type_label . ' found in Trash'
            ],
            'public' => true,
            'publicly_queryable' => true,
            'show_ui' => true,
            'show_in_menu' => 'webflow-import',
            'show_in_nav_menus' => true,
            'show_in_admin_bar' => true,
            'menu_position' => 25,
            'menu_icon' => $this->get_post_type_icon($collection['name']),
            'capability_type' => 'post',
            'hierarchical' => false,
            'supports' => $this->get_post_type_supports($collection['name']),
            'has_archive' => true,
            'rewrite' => ['slug' => sanitize_title($collection['name'])],
            'query_var' => true,
            'show_in_rest' => true
        ];
        
        register_post_type($post_type_slug, $args);
    }

    private function get_post_type_icon($collection_name) {
        $name = strtolower($collection_name);
        $icons = [
            'team' => 'dashicons-groups',
            'review' => 'dashicons-testimonial',
            'blog' => 'dashicons-edit',
            'post' => 'dashicons-edit',
            'product' => 'dashicons-cart',
            'service' => 'dashicons-admin-tools',
            'supplier' => 'dashicons-businessperson',
            'vendor' => 'dashicons-store',
            'city' => 'dashicons-location',
            'location' => 'dashicons-location-alt',
            'job' => 'dashicons-clipboard',
            'gallery' => 'dashicons-format-gallery',
            'catalog' => 'dashicons-media-spreadsheet',
            'blind' => 'dashicons-welcome-view-site',
            'category' => 'dashicons-category'
        ];
        
        foreach ($icons as $key => $icon) {
            if (strpos($name, $key) !== false) return $icon;
        }
        
        return 'dashicons-admin-post';
    }

    private function get_post_type_supports($collection_name) {
        $name = strtolower($collection_name);
        
        if (strpos($name, 'team') !== false || strpos($name, 'member') !== false) {
            return ['title', 'thumbnail', 'custom-fields', 'excerpt'];
        }
        
        if (strpos($name, 'review') !== false || strpos($name, 'testimonial') !== false) {
            return ['title', 'editor', 'custom-fields', 'thumbnail'];
        }
        
        if (strpos($name, 'product') !== false || strpos($name, 'service') !== false) {
            return ['title', 'editor', 'thumbnail', 'custom-fields', 'excerpt'];
        }
        
        if (strpos($name, 'blog') !== false || strpos($name, 'post') !== false) {
            return ['title', 'editor', 'thumbnail', 'custom-fields', 'excerpt', 'comments'];
        }
        
        return ['title', 'editor', 'thumbnail', 'custom-fields'];
    }

    private function register_fallback_post_types() {
        $post_types = [
            'webflow_team-members' => [
                'label' => 'Team Members',
                'icon' => 'dashicons-groups',
                'supports' => ['title', 'thumbnail', 'custom-fields']
            ],
            'webflow_reviews' => [
                'label' => 'Reviews',
                'icon' => 'dashicons-testimonial',
                'supports' => ['title', 'editor', 'custom-fields']
            ]
        ];

        foreach ($post_types as $slug => $args) {
            register_post_type($slug, [
                'labels' => [
                    'name' => $args['label'],
                    'singular_name' => $args['label'],
                    'menu_name' => $args['label'],
                    'all_items' => 'All ' . $args['label']
                ],
                'public' => true,
                'publicly_queryable' => true,
                'show_ui' => true,
                'show_in_menu' => 'webflow-import',
                'show_in_nav_menus' => true,
                'show_in_admin_bar' => true,
                'menu_position' => 25,
                'menu_icon' => $args['icon'],
                'capability_type' => 'post',
                'hierarchical' => false,
                'supports' => $args['supports'],
                'has_archive' => true,
                'rewrite' => ['slug' => str_replace('webflow_', '', $slug)],
                'query_var' => true,
                'show_in_rest' => true
            ]);
        }
    }

    // 3. ADMIN INTERFACE
    public function add_admin_page() {
        add_menu_page(
            'Webflow Import',
            'Webflow Import',
            'manage_options',
            'webflow-import',
            [$this, 'render_admin_page'],
            'dashicons-database-import',
            20
        );
    }

    public function admin_scripts($hook) {
        if ($hook === 'toplevel_page_webflow-import') {
            wp_enqueue_style(
                'webflow-importer-css',
                plugins_url('assets/css/admin.css', __FILE__),
                [],
                filemtime(plugin_dir_path(__FILE__) . 'assets/css/admin.css')
            );
            
            wp_enqueue_script(
                'webflow-importer-js',
                plugins_url('assets/js/admin.js', __FILE__),
                ['jquery'],
                filemtime(plugin_dir_path(__FILE__) . 'assets/js/admin.js'),
                true
            );
            
            wp_localize_script('webflow-importer-js', 'webflowImporter', [
                'ajaxurl' => admin_url('admin-ajax.php'),
                'nonce' => wp_create_nonce('webflow_import'),
                'progress_nonce' => wp_create_nonce('webflow_import_progress'),
                'cancel_nonce' => wp_create_nonce('webflow_import_cancel'),
                'i18n' => [
                    'importing' => __('Importing...', 'webflow-importer'),
                    'completed' => __('Completed!', 'webflow-importer'),
                    'error' => __('Error occurred', 'webflow-importer'),
                    'cancelled' => __('Cancelled', 'webflow-importer')
                ]
            ]);
        }
    }

    public function render_admin_page() {
        ?>
        <div class="wrap">
            <h1>Webflow CMS Importer</h1>
            
            <div class="webflow-importer-container">
                <div class="import-status-container">
                    <div id="import-status" class="import-status">
                        <div class="status-message">Ready to import</div>
                        <div class="progress-container">
                            <div class="progress-bar"></div>
                            <div class="progress-text">0%</div>
                        </div>
                    </div>
                    
                    <div id="current-action" class="current-action">
                        <span class="spinner is-active"></span>
                        <span class="action-text">Waiting to start...</span>
                    </div>
                </div>
                
                <div class="import-controls">
                    <button id="start-import" class="button button-primary">Start Import</button>
                    <button id="cancel-import" class="button button-secondary" disabled>Cancel</button>
                </div>
                
                <div class="import-results">
                    <h3>Import Log</h3>
                    <div class="log-entries"></div>
                </div>
            </div>
        </div>
        <?php
    }

    // 4. IMPORT PROCESS
    public function ajax_import() {
        check_ajax_referer('webflow_import');
        
        // Initialize progress tracking
        self::$import_progress = [
            'message' => 'Starting import process...',
            'progress' => 5,
            'log' => []
        ];
        
        $this->log_import('Import process started', 'info');

        try {
            $json_path = $this->get_collections_path();
            $this->log_import('Looking for collections file at: ' . $json_path, 'info');

            if (!file_exists($json_path)) {
                throw new Exception("Webflow collections.json file not found at: " . $json_path);
            }

            $json = json_decode(file_get_contents($json_path), true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new Exception("Invalid JSON: " . json_last_error_msg());
            }

            $total_collections = count($json);
            $current_collection = 0;
            $results = [];
            
            $this->log_import('Found ' . $total_collections . ' collections to import', 'info');
            $this->update_progress('Processing collections...', 10);

            foreach ($json as $collection) {
                if (get_transient('webflow_import_cancelled')) {
                    throw new Exception("Import cancelled by user");
                }

                $current_collection++;
                $collection_progress = 10 + (($current_collection / $total_collections) * 80);
                
                if (empty($collection['name']) || empty($collection['items'])) {
                    $this->log_import('Skipping collection - missing name or items', 'warning');
                    continue;
                }

                $post_type = 'webflow_' . sanitize_title($collection['name']);
                $imported = 0;
                $total_items = count($collection['items']);
                
                $this->update_progress(
                    'Importing ' . $collection['name'] . ' (' . $total_items . ' items)',
                    $collection_progress
                );
                
                $this->log_import('Starting import for collection: ' . $collection['name'], 'info');

                foreach ($collection['items'] as $index => $item) {
                    if (get_transient('webflow_import_cancelled')) {
                        throw new Exception("Import cancelled by user");
                    }

                    $item_progress = $collection_progress + (($index / $total_items) * 10);
                    $this->update_progress(false, $item_progress);
                    
                    $data = $item['fieldData'] ?? $item;
                    $title = $data['name'] ?? $data['title'] ?? 'Untitled';
                    
                    $this->log_import('Importing item: ' . $title, 'info');

                    $post_id = wp_insert_post([
                        'post_title' => $title,
                        'post_type' => $post_type,
                        'post_status' => 'publish',
                        'post_content' => $data['description'] ?? $data['content'] ?? '',
                        'meta_input' => $data
                    ]);

                    if ($post_id && !is_wp_error($post_id)) {
                        $imported++;
                        $this->log_import('Successfully imported: ' . $title, 'success');

                        // Handle images
                        $this->handle_item_images($post_id, $data);
                    } else {
                        $error = is_wp_error($post_id) ? $post_id->get_error_message() : 'Unknown error';
                        $this->log_import('Failed to import ' . $title . ': ' . $error, 'error');
                    }
                }

                $results[] = [
                    'name' => $collection['name'],
                    'count' => $imported,
                    'post_type' => $post_type
                ];
                
                $this->log_import(
                    'Completed collection: ' . $collection['name'] . ' (' . $imported . '/' . $total_items . ' items imported)',
                    $imported === $total_items ? 'success' : 'warning'
                );
            }

            $this->update_progress('Finalizing import...', 95);
            $this->log_import('Registering post types with imported data', 'info');
            
            // Register post types with the new data
            $this->register_dynamic_post_types();
            flush_rewrite_rules();
            
            $this->update_progress('Import complete!', 100);
            $this->log_import('Successfully completed import process', 'success');

            wp_send_json_success($results);

        } catch (Exception $e) {
            $this->update_progress('Import failed', 0);
            $this->log_import('Error: ' . $e->getMessage(), 'error');
            wp_send_json_error($e->getMessage());
        }
    }

    private function handle_item_images($post_id, $data) {
        // Handle main image if exists
        if (!empty($data['main-image']['url'])) {
            $this->log_import('Importing main image for post ID ' . $post_id, 'info');
            $image_id = $this->import_media($data['main-image']['url']);
            if ($image_id) {
                set_post_thumbnail($post_id, $image_id);
                $this->log_import('Successfully set featured image', 'success');
            }
        }

        // Handle gallery images if exists
        if (!empty($data['gallery']) && is_array($data['gallery'])) {
            $this->log_import('Importing gallery images for post ID ' . $post_id, 'info');
            $gallery_ids = [];
            foreach ($data['gallery'] as $image) {
                if (!empty($image['url'])) {
                    $img_id = $this->import_media($image['url']);
                    if ($img_id) {
                        $gallery_ids[] = $img_id;
                    }
                }
            }
            if (!empty($gallery_ids)) {
                update_post_meta($post_id, '_webflow_gallery', $gallery_ids);
                $this->log_import('Imported ' . count($gallery_ids) . ' gallery images', 'success');
            }
        }
    }

    private function import_media($url) {
        require_once(ABSPATH . 'wp-admin/includes/image.php');
        require_once(ABSPATH . 'wp-admin/includes/file.php');
        require_once(ABSPATH . 'wp-admin/includes/media.php');

        $url = esc_url_raw($url);
        if (!$url) return false;

        // Check if media already exists
        $existing_id = $this->find_existing_media($url);
        if ($existing_id) return $existing_id;

        $tmp = download_url($url);
        if (is_wp_error($tmp)) {
            $this->log_import('Download error: ' . $tmp->get_error_message(), 'error');
            return false;
        }

        $file_array = [
            'name' => basename($url),
            'tmp_name' => $tmp
        ];

        $id = media_handle_sideload($file_array, 0);
        if (is_wp_error($id)) {
            @unlink($tmp);
            $this->log_import('Sideload error: ' . $id->get_error_message(), 'error');
            return false;
        }

        // Store original URL in meta
        update_post_meta($id, '_webflow_source_url', $url);

        return $id;
    }

    private function find_existing_media($url) {
        global $wpdb;
        
        $query = $wpdb->prepare(
            "SELECT post_id FROM $wpdb->postmeta WHERE meta_key = '_webflow_source_url' AND meta_value = %s LIMIT 1",
            $url
        );
        
        return $wpdb->get_var($query);
    }

    // 5. PROGRESS TRACKING
    public function ajax_import_progress() {
        check_ajax_referer('webflow_import_progress');
        
        $response = [
            'success' => true,
            'data' => self::$import_progress
        ];
        
        // Clear log after sending to avoid duplicates
        self::$import_progress['log'] = [];
        
        wp_send_json($response);
    }

    public function ajax_import_cancel() {
        check_ajax_referer('webflow_import_cancel');
        set_transient('webflow_import_cancelled', true, 60 * 5); // 5 minute expiration
        wp_send_json_success();
    }

    private function update_progress($message = false, $progress = false) {
        if ($message !== false) {
            self::$import_progress['message'] = $message;
        }
        if ($progress !== false) {
            self::$import_progress['progress'] = $progress;
        }
    }

    private function log_import($message, $type = 'info') {
        self::$import_progress['log'][] = [
            'message' => $message,
            'type' => $type
        ];
    }

    // 6. ADMIN NOTICES
    public function show_admin_notices() {
        if (!empty($this->debug_log)) {
            echo '<div class="notice notice-warning">';
            echo '<h3>Webflow Importer Debug</h3>';
            echo '<ul>';
            foreach ($this->debug_log as $log) {
                echo '<li>' . esc_html($log) . '</li>';
            }
            echo '</ul>';
            echo '</div>';
        }
    }
}

new Webflow_Importer_Complete();