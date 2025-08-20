<?php
/*
Plugin Name: Webflow Magic
Description: Guaranteed to show imported content in admin menu
Version: 4.0
By: SourceSelect.ca
*/

class Webflow_Importer_Complete
{
    private $debug_log = [];

    public function __construct()
    {
        // Initialize everything
        add_action('admin_menu', [$this, 'add_admin_page']);
        add_action('wp_ajax_webflow_import', [$this, 'ajax_import']);
        register_activation_hook(__FILE__, [$this, 'flush_rewrites_on_activate']);
        add_action('init', [$this, 'force_register_post_types']);
    }

    // 1. FLUSH REWRITES ON ACTIVATION
    public function flush_rewrites_on_activate()
    {
        $this->force_register_post_types();
        flush_rewrite_rules();
    }

    // 2. FORCE REGISTER POST TYPES
    public function force_register_post_types()
    {
        // Hardcoded post types we know you need
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
                'show_in_menu' => true, // Changed from true to 'webflow-import' if you want submenu
                'show_in_nav_menus' => true,
                'show_in_admin_bar' => true,
                'menu_position' => 25,
                'menu_icon' => $args['icon'],
                'capability_type' => 'post',
                'hierarchical' => false,
                'supports' => $args['supports'],
                'has_archive' => true,
                'rewrite' => ['slug' => str_replace('webflow_', '', $slug)],
                'query_var' => true
            ]);
        }
    }

    // 3. ADMIN PAGE
    public function add_admin_page()
    {
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

    public function render_admin_page()
    {
        ?>
                <div class="wrap">
                    <h1>Webflow CMS Importer</h1>
                    <div id="webflow-importer">
                        <div class="progress-container">
                            <div class="progress-bar" style="width:0%"></div>
                        </div>
                        <button id="start-import" class="button button-primary">Start Import</button>
                        <div id="import-results"></div>
                    </div>
                </div>

                <style>
                    .progress-container {
                        background: #f3f3f3;
                        height: 20px;
                        margin: 20px 0;
                        border-radius: 4px;
                    }

                    .progress-bar {
                        background: #2271b1;
                        height: 100%;
                        transition: width 0.3s;
                    }
                </style>

                <script>
                    jQuery(document).ready(function ($) {
                        $('#start-import').click(function () {
                            var $btn = $(this).prop('disabled', true);
                            var $progress = $('.progress-bar');
                            var $results = $('#import-results').empty();

                            function updateProgress(percent, message) {
                                $progress.css('width', percent + '%');
                                $results.append('<p>' + message + '</p>');
                            }

                            $.ajax({
                                url: ajaxurl,
                                method: 'POST',
                                data: {
                                    action: 'webflow_import',
                                    _wpnonce: '<?php echo wp_create_nonce('webflow_import'); ?>'
                                },
                                success: function (response) {
                                    if (response.success) {
                                        updateProgress(100, 'Import complete! Refreshing...');
                                        setTimeout(function () {
                                            location.reload();
                                        }, 1500);
                                    } else {
                                        updateProgress(0, 'Error: ' + response.data);
                                    }
                                },
                                complete: function () {
                                    $btn.prop('disabled', false);
                                }
                            });
                        });
                    });
                </script>
                <?php
    }

    // 4. AJAX IMPORT HANDLER
    public function ajax_import()
    {
        check_ajax_referer('webflow_import');

        try {
            $json_path = get_template_directory() . '/cms-data/collections.json';

            if (!file_exists($json_path)) {
                throw new Exception("JSON file not found");
            }

            $json = json_decode(file_get_contents($json_path), true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new Exception("Invalid JSON: " . json_last_error_msg());
            }

            $results = [];
            foreach ($json as $collection) {
                if (empty($collection['name']) || empty($collection['items']))
                    continue;

                $post_type = 'webflow_' . sanitize_title($collection['name']);
                $imported = 0;

                foreach ($collection['items'] as $item) {
                    $data = $item['fieldData'] ?? $item;

                    $post_id = wp_insert_post([
                        'post_title' => $data['name'] ?? $data['title'] ?? 'Untitled',
                        'post_type' => $post_type,
                        'post_status' => 'publish',
                        'meta_input' => $data
                    ]);

                    if ($post_id && !is_wp_error($post_id)) {
                        $imported++;

                        // Handle image if exists
                        if (!empty($data['main-image']['url'])) {
                            $image_id = $this->import_media($data['main-image']['url']);
                            if ($image_id)
                                set_post_thumbnail($post_id, $image_id);
                        }
                    }
                }

                $results[] = [
                    'name' => $collection['name'],
                    'count' => $imported,
                    'post_type' => $post_type
                ];
            }

            wp_send_json_success($results);

        } catch (Exception $e) {
            wp_send_json_error($e->getMessage());
        }
    }

    // 5. MEDIA IMPORT
    private function import_media($url)
    {
        require_once(ABSPATH . 'wp-admin/includes/image.php');
        require_once(ABSPATH . 'wp-admin/includes/file.php');
        require_once(ABSPATH . 'wp-admin/includes/media.php');

        $url = esc_url_raw($url);
        if (!$url)
            return false;

        $tmp = download_url($url);
        if (is_wp_error($tmp))
            return false;

        $file_array = [
            'name' => basename($url),
            'tmp_name' => $tmp
        ];

        $id = media_handle_sideload($file_array, 0);
        if (is_wp_error($id)) {
            @unlink($tmp);
            return false;
        }

        return $id;
    }
}

new Webflow_Importer_Complete();