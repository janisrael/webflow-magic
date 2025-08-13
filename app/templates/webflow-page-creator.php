<?php
/**
 * Plugin Name: {{PLUGIN_NAME}}
 * Description: Automatically creates WordPress pages for all converted Webflow pages
 * Version: 1.0.0
 * Author: SourceSelect.ca
 */

// Prevent direct access
if (!defined('ABSPATH'))
    exit;

// Enable error logging for debugging
if (!function_exists('webflow_log_error')) {
    function webflow_log_error($message)
    {
        error_log('[Webflow Page Creator] ' . $message);
    }
}

class WebflowAutoPageCreator
{

    private $pages_data;

    public function __construct()
    {
        try {
            $this->pages_data = json_decode('{{PAGES_JSON}}', true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                webflow_log_error('JSON decode error: ' . json_last_error_msg());
                $this->pages_data = array();
            }
        } catch (Exception $e) {
            webflow_log_error('Constructor error: ' . $e->getMessage());
            $this->pages_data = array();
        }

        add_action('init', array($this, 'init'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_notices', array($this, 'admin_notices'));
        register_activation_hook(__FILE__, array($this, 'activate_plugin'));

        // Add AJAX handlers
        add_action('wp_ajax_webflow_create_pages', array($this, 'ajax_create_pages'));
        add_action('wp_ajax_webflow_create_single_page', array($this, 'ajax_create_single_page'));
    }

    public function init()
    {
        add_action('admin_init', array($this, 'maybe_create_pages'));
    }

    public function activate_plugin()
    {
        try {
            update_option('webflow_create_pages_needed', true);
            update_option('webflow_pages_data', $this->pages_data);
            update_option('webflow_pages_activation_time', time());
            webflow_log_error('Plugin activated successfully');
        } catch (Exception $e) {
            webflow_log_error('Activation error: ' . $e->getMessage());
        }
    }

    public function maybe_create_pages()
    {
        if (get_option('webflow_create_pages_needed') && current_user_can('manage_options')) {
            $activation_time = get_option('webflow_pages_activation_time', 0);
            if (time() - $activation_time < 300) {
                delete_option('webflow_create_pages_needed');
                $this->create_all_pages();
            } else {
                delete_option('webflow_create_pages_needed');
            }
        }
    }

    public function create_all_pages()
    {
        $start_time = microtime(true);
        $results = array(
            'created' => 0,
            'skipped' => 0,
            'errors' => array(),
            'success' => true,
            'created_pages' => array(),
            'skipped_pages' => array()
        );

        try {
            $pages_data = get_option('webflow_pages_data', $this->pages_data);

            if (empty($pages_data)) {
                throw new Exception('No pages data found');
            }

            webflow_log_error('Starting page creation for ' . count($pages_data) . ' pages');

            foreach ($pages_data as $index => $page_data) {
                try {
                    // Update progress
                    set_transient('webflow_pages_progress', array(
                        'current' => $index + 1,
                        'total' => count($pages_data),
                        'page' => $page_data['title'] ?? 'Unknown'
                    ), 300);

                    $result = $this->create_single_page($page_data);

                    if ($result['success']) {
                        $results['created']++;
                        $results['created_pages'][] = $page_data['title'] ?? 'Unknown';
                        webflow_log_error('Created page: ' . ($page_data['title'] ?? 'Unknown'));
                    } else {
                        if ($result['reason'] === 'exists') {
                            $results['skipped']++;
                            $results['skipped_pages'][] = $page_data['title'] ?? 'Unknown';
                        } else {
                            $results['errors'][] = $result['message'];
                            webflow_log_error('Error creating page: ' . $result['message']);
                        }
                    }

                    // Small delay to prevent issues
                    usleep(100000); // 0.1 second

                } catch (Exception $e) {
                    $results['errors'][] = 'Exception for page ' . ($page_data['title'] ?? 'Unknown') . ': ' . $e->getMessage();
                    webflow_log_error('Exception creating page: ' . $e->getMessage());
                }
            }

            // Set front page
            $this->set_front_page($pages_data);

            $results['time'] = microtime(true) - $start_time;
            webflow_log_error('Page creation completed. Created: ' . $results['created'] . ', Skipped: ' . $results['skipped'] . ', Errors: ' . count($results['errors']));

        } catch (Exception $e) {
            $results['success'] = false;
            $results['error'] = $e->getMessage();
            $results['time'] = microtime(true) - $start_time;
            webflow_log_error('Fatal error in create_all_pages: ' . $e->getMessage());
        }

        set_transient('webflow_pages_results', $results, 300);
        delete_transient('webflow_pages_progress');

        return $results;
    }

    public function create_single_page($page_data)
    {
        try {
            // Validate input data
            if (empty($page_data) || !is_array($page_data)) {
                return array(
                    'success' => false,
                    'reason' => 'error',
                    'message' => 'Invalid page data provided'
                );
            }

            $title = sanitize_text_field($page_data['title'] ?? 'Untitled Page');
            $slug = sanitize_title($page_data['slug'] ?? '');

            if (empty($slug)) {
                return array(
                    'success' => false,
                    'reason' => 'error',
                    'message' => 'Invalid slug for page: ' . $title
                );
            }

            // Check if page exists
            $existing_page = get_page_by_path($slug);
            if ($existing_page) {
                return array(
                    'success' => false,
                    'reason' => 'exists',
                    'message' => 'Page already exists: ' . $title
                );
            }

            // Prepare content
            $content = wp_kses_post($page_data['content'] ?? '');
            if (empty($content)) {
                $content = '<p>This page was automatically created from your Webflow design.</p>';
                $content .= '<p>Content will be displayed using the template: <code>' . esc_html($page_data['template'] ?? 'default') . '</code></p>';
            }

            // Create page
            $page_args = array(
                'post_title' => $title,
                'post_name' => $slug,
                'post_content' => $content,
                'post_status' => 'publish',
                'post_type' => 'page',
                'post_author' => get_current_user_id() ?: 1,
                'comment_status' => 'closed',
                'ping_status' => 'closed'
            );

            $page_id = wp_insert_post($page_args, true);

            if (is_wp_error($page_id)) {
                return array(
                    'success' => false,
                    'reason' => 'error',
                    'message' => 'WordPress error: ' . $page_id->get_error_message()
                );
            }

            if (!$page_id) {
                return array(
                    'success' => false,
                    'reason' => 'error',
                    'message' => 'Failed to create page: ' . $title
                );
            }

            // Add meta data
            if (!empty($page_data['filename'])) {
                update_post_meta($page_id, '_webflow_original_file', sanitize_text_field($page_data['filename']));
            }

            if (!empty($page_data['template'])) {
                update_post_meta($page_id, '_wp_page_template', sanitize_text_field($page_data['template']));
            }

            if (!empty($page_data['meta_description'])) {
                update_post_meta($page_id, '_meta_description', sanitize_textarea_field($page_data['meta_description']));
            }

            // Verify creation
            $created_page = get_post($page_id);
            if (!$created_page || $created_page->post_type !== 'page') {
                return array(
                    'success' => false,
                    'reason' => 'error',
                    'message' => 'Page creation verification failed: ' . $title
                );
            }

            return array(
                'success' => true,
                'page_id' => $page_id,
                'message' => 'Successfully created page: ' . $title . ' (ID: ' . $page_id . ')'
            );

        } catch (Exception $e) {
            webflow_log_error('Exception in create_single_page: ' . $e->getMessage());
            return array(
                'success' => false,
                'reason' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            );
        }
    }

    public function set_front_page($pages_data)
    {
        try {
            foreach ($pages_data as $page_data) {
                if (!empty($page_data['is_front_page'])) {
                    $front_page = get_page_by_path($page_data['slug']);
                    if ($front_page && $front_page->post_type === 'page') {
                        update_option('show_on_front', 'page');
                        update_option('page_on_front', $front_page->ID);
                        webflow_log_error('Set front page: ' . $front_page->ID);
                        break;
                    }
                }
            }
        } catch (Exception $e) {
            webflow_log_error('Error setting front page: ' . $e->getMessage());
        }
    }

    public function ajax_create_pages()
    {
        try {
            // Verify nonce
            if (!check_ajax_referer('webflow_pages_nonce', 'nonce', false)) {
                wp_send_json_error('Security check failed');
                return;
            }

            if (!current_user_can('manage_options')) {
                wp_send_json_error('Insufficient permissions');
                return;
            }

            $results = $this->create_all_pages();
            wp_send_json_success($results);

        } catch (Exception $e) {
            webflow_log_error('AJAX error: ' . $e->getMessage());
            wp_send_json_error('Error: ' . $e->getMessage());
        }
    }

    public function ajax_create_single_page()
    {
        try {
            if (!check_ajax_referer('webflow_pages_nonce', 'nonce', false)) {
                wp_send_json_error('Security check failed');
                return;
            }

            if (!current_user_can('manage_options')) {
                wp_send_json_error('Insufficient permissions');
                return;
            }

            $slug = sanitize_text_field($_POST['slug'] ?? '');
            if (empty($slug)) {
                wp_send_json_error('Invalid slug');
                return;
            }

            $pages_data = get_option('webflow_pages_data', array());

            foreach ($pages_data as $page_data) {
                if ($page_data['slug'] === $slug) {
                    $result = $this->create_single_page($page_data);
                    if ($result['success']) {
                        wp_send_json_success($result);
                    } else {
                        wp_send_json_error($result['message']);
                    }
                    return;
                }
            }

            wp_send_json_error('Page data not found');

        } catch (Exception $e) {
            webflow_log_error('AJAX single page error: ' . $e->getMessage());
            wp_send_json_error('Error: ' . $e->getMessage());
        }
    }

    public function add_admin_menu()
    {
        add_management_page(
            'Webflow Pages',
            'Webflow Pages',
            'manage_options',
            'webflow-pages',
            array($this, 'admin_page')
        );
    }

    public function admin_page()
    {
        $pages_data = get_option('webflow_pages_data', $this->pages_data);
        ?>
        <div class="wrap">
            <h1>Webflow Auto Page Creator</h1>

            <div class="card">
                <h2>Page Creation Status</h2>

                <?php if ($results = get_transient('webflow_pages_results')): ?>
                    <div class="notice notice-<?php echo $results['success'] ? 'success' : 'error'; ?>">
                        <?php if ($results['success']): ?>
                            <p><strong> Pages Created Successfully!</strong></p>
                            <p>Created: <?php echo $results['created']; ?> pages</p>
                            <p>Skipped: <?php echo $results['skipped']; ?> pages</p>
                            <p>Time: <?php echo number_format($results['time'], 2); ?> seconds</p>

                            <?php if (!empty($results['created_pages'])): ?>
                                <p><strong>Created:</strong> <?php echo implode(', ', $results['created_pages']); ?></p>
                            <?php endif; ?>
                        <?php else: ?>
                            <p><strong> Error:</strong> <?php echo esc_html($results['error'] ?? 'Unknown error'); ?></p>
                        <?php endif; ?>

                        <?php if (!empty($results['errors'])): ?>
                            <p><strong>Errors:</strong></p>
                            <ul>
                                <?php foreach ($results['errors'] as $error): ?>
                                    <li><?php echo esc_html($error); ?></li>
                                <?php endforeach; ?>
                            </ul>
                        <?php endif; ?>
                    </div>
                <?php endif; ?>

                <?php if ($progress = get_transient('webflow_pages_progress')): ?>
                    <?php $percent = round(($progress['current'] / $progress['total']) * 100); ?>
                    <div class="notice notice-info">
                        <p><strong>Creating Pages:</strong> <?php echo $percent; ?>% complete</p>
                        <p>Current: <?php echo esc_html($progress['page']); ?></p>
                        <div style="background:#f1f1f1;height:20px;width:100%;border-radius:10px;">
                            <div style="background:#2271b1;height:100%;width:<?php echo $percent; ?>%;border-radius:10px;"></div>
                        </div>
                    </div>
                <?php endif; ?>

                <p>
                    <button type="button" class="button button-primary" onclick="createPages()">
                        Create Pages Now
                    </button>
                    <button type="button" class="button" onclick="location.reload()">
                        Refresh Status
                    </button>
                    <a href="<?php echo admin_url('edit.php?post_type=page'); ?>" class="button">
                        View All Pages
                    </a>
                </p>
            </div>

            <div class="card">
                <h2>Detected Webflow Pages</h2>
                <table class="widefat fixed">
                    <thead>
                        <tr>
                            <th>Page Title</th>
                            <th>Slug</th>
                            <th>Template</th>
                            <th>WordPress Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if (!empty($pages_data)): ?>
                            <?php foreach ($pages_data as $page): ?>
                                <?php
                                $wp_page = get_page_by_path($page['slug']);
                                $status = $wp_page ? ' Created' : ' Not Created';
                                $status_class = $wp_page ? 'success' : 'error';
                                ?>
                                <tr>
                                    <td><strong><?php echo esc_html($page['title']); ?></strong></td>
                                    <td><code><?php echo esc_html($page['slug']); ?></code></td>
                                    <td><code><?php echo esc_html($page['template']); ?></code></td>
                                    <td>
                                        <span class="notice notice-<?php echo $status_class; ?> inline">
                                            <?php echo $status; ?>
                                            <?php if ($wp_page): ?>
                                                <small>(ID: <?php echo $wp_page->ID; ?>)</small>
                                            <?php endif; ?>
                                        </span>
                                    </td>
                                    <td>
                                        <?php if ($wp_page): ?>
                                            <a href="<?php echo get_edit_post_link($wp_page->ID); ?>" class="button button-small">Edit</a>
                                            <a href="<?php echo get_permalink($wp_page->ID); ?>" class="button button-small"
                                                target="_blank">View</a>
                                        <?php else: ?>
                                            <button class="button button-small"
                                                onclick="createSinglePage('<?php echo esc_js($page['slug']); ?>')">Create</button>
                                        <?php endif; ?>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        <?php else: ?>
                            <tr>
                                <td colspan="5">No pages data found.</td>
                            </tr>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h2>Debug Information</h2>
                <p><strong>Pages Data Count:</strong> <?php echo count($pages_data); ?></p>
                <p><strong>WordPress Pages:</strong> <?php echo wp_count_posts('page')->publish; ?></p>
                <p><strong>Front Page Setting:</strong> <?php echo get_option('show_on_front'); ?></p>
                <?php if (get_option('show_on_front') === 'page'): ?>
                    <p><strong>Front Page ID:</strong> <?php echo get_option('page_on_front'); ?></p>
                <?php endif; ?>
                <p><strong>PHP Memory:</strong> <?php echo ini_get('memory_limit'); ?></p>
                <p><strong>WordPress Version:</strong> <?php echo get_bloginfo('version'); ?></p>
            </div>
        </div>

        <style>
            .notice.inline {
                display: inline-block;
                padding: 5px 10px;
                margin: 0;
            }

            .card {
                background: #fff;
                border: 1px solid #ccd0d4;
                padding: 20px;
                margin: 20px 0;
            }
        </style>

        <script>
            function createPages() {
                if (confirm('Create WordPress pages for all Webflow pages?')) {
                    var button = event.target;
                    button.disabled = true;
                    button.textContent = 'Creating...';

                    jQuery.post(ajaxurl, {
                        action: 'webflow_create_pages',
                        nonce: '<?php echo wp_create_nonce('webflow_pages_nonce'); ?>'
                    })
                        .done(function (response) {
                            if (response.success) {
                                alert('Pages created successfully!');
                            } else {
                                alert('Error: ' + (response.data || 'Unknown error'));
                            }
                        })
                        .fail(function (xhr, status, error) {
                            alert('AJAX Error: ' + error);
                            console.log('Full error:', xhr.responseText);
                        })
                        .always(function () {
                            location.reload();
                        });
                }
            }

            function createSinglePage(slug) {
                if (confirm('Create page: ' + slug + '?')) {
                    jQuery.post(ajaxurl, {
                        action: 'webflow_create_single_page',
                        slug: slug,
                        nonce: '<?php echo wp_create_nonce('webflow_pages_nonce'); ?>'
                    }, function (response) {
                        if (response.success) {
                            alert('Page created successfully!');
                        } else {
                            alert('Error: ' + (response.data || 'Unknown error'));
                        }
                        location.reload();
                    });
                }
            }

            // Auto-refresh during progress
            <?php if (get_transient('webflow_pages_progress')): ?>
                setTimeout(function () {
                    location.reload();
                }, 2000);
            <?php endif; ?>
        </script>
        <?php
    }

    public function admin_notices()
    {
        if ($results = get_transient('webflow_pages_results')) {
            if ($results['success'] && $results['created'] > 0) {
                echo '<div class="notice notice-success is-dismissible">';
                echo '<p><strong> Webflow Pages Created!</strong></p>';
                echo '<p> Created: ' . $results['created'] . ' pages</p>';
                echo '<p><a href="' . admin_url('edit.php?post_type=page') . '" class="button">View Pages →</a></p>';
                echo '</div>';
            }
        }
    }
}

// Initialize the plugin
new WebflowAutoPageCreator();
?>