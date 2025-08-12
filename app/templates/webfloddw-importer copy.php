<?php
/*
Plugin Name: Webflow Magic
Description: Automatically imports Webflow CMS content into WordPress with progress tracking
Version: 2.2
Author: Swordfish
*/

defined('ABSPATH') or die('Direct access not allowed');

class Webflow_Importer
{
    public function __construct()
    {
        $this->setup_hooks();
    }

    private function setup_hooks()
    {
        register_activation_hook(__FILE__, [$this, 'auto_install']);
        add_action('admin_menu', [$this, 'admin_menu']);
        add_action('admin_notices', [$this, 'admin_notices']);
        add_action('admin_init', [$this, 'maybe_run_import']); // New hook
    }

    public function auto_install()
    {
        if (!get_option('webflow_importer_installed')) {
            update_option('webflow_importer_do_import', true);
            update_option('webflow_importer_installed', time());
        }
    }

    public function maybe_run_import()
    {
        if (get_option('webflow_importer_do_import')) {
            $this->import_all_content();
            delete_option('webflow_importer_do_import');
        }
    }

    public function admin_assets($hook)
    {
        if ($hook !== 'toplevel_page_webflow-importer')
            return;

        // Inline CSS
        echo '<style>
        .webflow-importer-card {
            background:#fff; padding:20px; margin-bottom:20px;
            border-radius:4px; box-shadow:0 1px 1px rgba(0,0,0,0.04);
        }
        .progress-bar-container {
            background:#f1f1f1; height:20px; border-radius:3px;
            margin:10px 0; overflow:hidden;
        }
        .progress-bar {
            background:#2271b1; height:100%; width:0;
            transition:width 0.3s ease;
        }
        .progress-status {
            display:flex; justify-content:space-between;
            margin-bottom:15px;
        }
        #import-results.hidden { display:none; }
        </style>';

        // Inline JS
        echo '<script>
        jQuery(document).ready(function($) {
            $("#start-import").click(function(e) {
                e.preventDefault();
                var $btn = $(this).prop("disabled", true).text("Importing...");
                var $progress = $(".progress-bar");
                var $status = $(".current-action");
                
                function checkProgress() {
                    $.ajax({
                        url: ajaxurl,
                        data: {
                            action: "webflow_check_progress",
                            _wpnonce: "' . wp_create_nonce('webflow_import_nonce') . '"
                        },
                        success: function(res) {
                            if (res.data.complete) {
                                $progress.css("width", "100%");
                                $status.text("Import complete!");
                                location.reload();
                            } else {
                                $progress.css("width", res.data.progress.percent + "%");
                                $status.text(res.data.progress.message);
                                setTimeout(checkProgress, 1000);
                            }
                        }
                    });
                }
                
                $.post(ajaxurl, {
                    action: "webflow_start_import",
                    _wpnonce: "' . wp_create_nonce('webflow_import_nonce') . '"
                }, function() {
                    checkProgress();
                });
            });
        });
        </script>';
    }

    public function admin_menu()
    {
        add_menu_page(
            'Webflow Importer',
            'Webflow Import',
            'manage_options',
            'webflow-importer',
            [$this, 'import_page'],
            'dashicons-database-import'
        );
    }

    public function admin_notices()
    {
        if ($results = get_transient('webflow_import_results')) {
            $class = $results['error'] ? 'error' : 'success';
            echo '<div class="notice notice-' . $class . ' is-dismissible">';
            if ($results['error']) {
                echo '<p><strong>Import Error:</strong> ' . esc_html($results['message']) . '</p>';
            } else {
                echo '<p><strong>Import Complete!</strong></p>';
                foreach ($results['counts'] as $cpt => $count) {
                    echo '<p>Imported ' . $count . ' items to ' . $cpt . '</p>';
                }
                echo '<p>Time taken: ' . number_format($results['time'], 2) . ' seconds</p>';
            }
            echo '</div>';
            delete_transient('webflow_import_results');
        }

        if (get_option('webflow_importer_do_import')) {
            echo '<div class="notice notice-info">
                <p>Webflow CMS Importer: <a href="' . admin_url('admin.php?page=webflow-importer') . '">Run the initial import</a></p>
            </div>';
        }
    }

    public function import_page()
    {
        echo '<div class="wrap">
            <h1>Webflow CMS Importer</h1>
            <div class="webflow-importer-card">
                <h2>Import Status</h2>
                <div id="webflow-import-progress">
                    <div class="progress-bar-container">
                        <div class="progress-bar" style="width:0%"></div>
                    </div>
                    <div class="progress-status">
                        <span class="percentage">0%</span>
                        <span class="current-action">Ready to start</span>
                    </div>
                </div>
                <button id="start-import" class="button button-primary">Start Import</button>
            </div>
            <div class="webflow-importer-card">
                <h2>Current Collections</h2>';

        $cpts = get_post_types(['_builtin' => false], 'objects');
        if ($cpts) {
            echo '<table class="wp-list-table widefat striped">
                <thead><tr><th>Collection</th><th>Items</th><th>Last Import</th></tr></thead>
                <tbody>';
            foreach ($cpts as $cpt) {
                $count = wp_count_posts($cpt->name);
                $last_import = get_option("webflow_{$cpt->name}_last_import", 'Never');
                echo "<tr><td>{$cpt->label}</td><td>{$count->publish}</td><td>{$last_import}</td></tr>";
            }
            echo '</tbody></table>';
        } else {
            echo '<p>No collections imported yet</p>';
        }

        echo '</div></div>';
    }

    public function ajax_start_import()
    {
        check_ajax_referer('webflow_import_nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error('Unauthorized', 403);
        }

        delete_option('webflow_importer_do_import');
        $this->import_all_content(true);
        wp_send_json_success();
    }

    public function ajax_check_progress()
    {
        check_ajax_referer('webflow_import_nonce');

        $progress = get_transient('webflow_import_progress') ?: [
            'percent' => 0,
            'message' => 'Starting import...'
        ];

        $results = get_transient('webflow_import_results');

        wp_send_json_success([
            'progress' => $progress,
            'complete' => (bool) $results
        ]);
    }

    public function import_all_content($background = false)
    {
        // Verify requirements
        if (!function_exists('acf_add_local_field_group')) {
            $this->log_error('ACF Pro is required');
            return false;
        }

        $cms_file = get_template_directory() . '/cms-data/collections.json';
        if (!file_exists($cms_file)) {
            $this->log_error('collections.json not found');
            return false;
        }

        $start_time = microtime(true);
        $collections = json_decode(file_get_contents($cms_file), true);
        $results = ['counts' => [], 'time' => 0, 'error' => false];
        $total = count($collections);

        try {
            foreach ($collections as $index => $collection) {
                $current = $index + 1;
                $percent = round(($current / $total) * 100);

                set_transient('webflow_import_progress', [
                    'percent' => $percent,
                    'current' => $current,
                    'total' => $total,
                    'message' => "Importing {$collection['name']}...",
                    'collection' => $collection['slug']
                ], 300);

                $imported = $this->process_collection($collection);
                $results['counts'][$collection['slug']] = $imported;
                update_option("webflow_{$collection['slug']}_last_import", current_time('mysql'));

                if (!$background)
                    sleep(1);
            }

            $results['time'] = microtime(true) - $start_time;
            set_transient('webflow_import_results', $results, 3600);
            delete_transient('webflow_import_progress');
            return $results;

        } catch (Exception $e) {
            $this->log_error($e->getMessage());
            return false;
        }
    }

    private function process_collection($collection)
    {
        $post_type = $collection['slug'];
        $imported = 0;

        // Register CPT
        if (!post_type_exists($post_type)) {
            register_post_type($post_type, [
                'label' => $collection['name'],
                'public' => true,
                'show_in_rest' => true,
                'supports' => ['title', 'editor', 'thumbnail', 'custom-fields'],
                'rewrite' => ['slug' => $post_type]
            ]);
        }

        // Register ACF fields
        $fields = array_map(function ($field) use ($post_type) {
            return [
                'key' => "field_{$post_type}_{$field['slug']}",
                'label' => $field['name'],
                'name' => $field['slug'],
                'type' => $this->map_field_type($field['type'])
            ];
        }, $collection['fields']);

        acf_add_local_field_group([
            'key' => "group_$post_type",
            'title' => "{$collection['name']} Fields",
            'fields' => $fields,
            'location' => [
                [
                    [
                        'param' => 'post_type',
                        'operator' => '==',
                        'value' => $post_type
                    ]
                ]
            ]
        ]);

        // Import items
        foreach ($collection['items'] as $item) {
            $post_id = wp_insert_post([
                'post_title' => $item['name'] ?? 'Untitled',
                'post_content' => $item['content'] ?? '',
                'post_type' => $post_type,
                'post_status' => 'publish',
                'meta_input' => $this->prepare_meta_input($item, $collection)
            ]);

            if ($post_id && !is_wp_error($post_id)) {
                $imported++;
            }
        }

        return $imported;
    }

    private function prepare_meta_input($item, $collection)
    {
        $meta = [];
        foreach ($collection['fields'] as $field) {
            $slug = $field['slug'];
            if (isset($item[$slug])) {
                $meta[$slug] = $item[$slug];
                $meta["_$slug"] = "field_{$collection['slug']}_{$slug}";
            }
        }
        return $meta;
    }

    private function map_field_type($type)
    {
        $map = [
            'text' => 'text',
            'textarea' => 'textarea',
            'richtext' => 'wysiwyg',
            'image' => 'image',
            'file' => 'file',
            'number' => 'number',
            'date' => 'date_picker',
            'switch' => 'true_false',
            'option' => 'select',
            'multiselect' => 'checkbox',
            'color' => 'color_picker',
            'url' => 'url'
        ];
        return $map[$type] ?? 'text';
    }

    private function log_error($message)
    {
        error_log("Webflow Importer: $message");
        set_transient('webflow_import_results', [
            'error' => true,
            'message' => $message,
            'time' => 0
        ], 3600);
    }
}

new Webflow_Importer();