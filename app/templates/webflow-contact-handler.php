<?php
/**
 * Plugin Name: {{PLUGIN_NAME}}
 * Description: Universal contact form handler for all forms on contact pages with admin management
 * Version: 1.0.0
 * Author: SourceSelect.ca
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class WebflowContactFormHandler
{
    private $plugin_name = 'webflow_contact_handler';

    public function __construct()
    {
        add_action('init', array($this, 'init'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_action('admin_notices', array($this, 'admin_notices'));

        // AJAX handlers for form submissions
        add_action('wp_ajax_webflow_contact_submit', array($this, 'handle_contact_form'));
        add_action('wp_ajax_nopriv_webflow_contact_submit', array($this, 'handle_contact_form'));

        // Auto-installation hooks
        register_activation_hook(__FILE__, array($this, 'activate_plugin'));
        add_action('admin_init', array($this, 'auto_setup_check'));
    }

    public function init()
    {
        // Register custom post type for storing form submissions
        $this->register_contact_forms_post_type();
    }

    public function activate_plugin()
    {
        // Set flag for auto-setup
        update_option('webflow_contact_handler_do_setup', true);

        // Set default settings
        $default_settings = array(
            'on_send_form' => 'both', // both, only_save, only_send
            'email_to' => get_option('admin_email'),
            'email_subject' => 'New message from ' . get_bloginfo('name'),
            'auto_detect_contact_pages' => true,
            'trigger_keywords' => 'contact,contact-us,get-in-touch,reach-out'
        );

        update_option('webflow_contact_handler_settings', $default_settings);

        // Register post type
        $this->register_contact_forms_post_type();
        flush_rewrite_rules();

        // Add success message
        set_transient('webflow_contact_handler_activated', true, 30);
    }

    public function auto_setup_check()
    {
        if (get_option('webflow_contact_handler_do_setup')) {
            delete_option('webflow_contact_handler_do_setup');
            $this->run_auto_setup();
        }
    }

    public function run_auto_setup()
    {
        // Auto-setup completed
        set_transient('webflow_contact_handler_setup_complete', array(
            'message' => 'Contact Form Handler is now active and monitoring all contact forms!',
            'status' => 'success'
        ), 60);
    }

    public function register_contact_forms_post_type()
    {
        register_post_type('webflow_contact_forms', array(
            'labels' => array(
                'name' => __('Contact Forms'),
                'singular_name' => __('Contact Form'),
                'menu_name' => __('Contact Forms'),
                'all_items' => __('All Submissions'),
                'view_item' => __('View Submission'),
                'search_items' => __('Search Submissions'),
                'not_found' => __('No submissions found'),
                'not_found_in_trash' => __('No submissions found in Trash')
            ),
            'public' => false,
            'show_ui' => true,
            'show_in_menu' => true,
            'show_in_admin_bar' => true,
            'exclude_from_search' => true,
            'has_archive' => false,
            'show_in_rest' => false,
            'supports' => array('title'),
            'menu_icon' => 'dashicons-email-alt',
            'capability_type' => 'post',
            'capabilities' => array(
                'create_posts' => false, // Remove "Add New" button
            ),
            'map_meta_cap' => true,
        ));

        // Add meta box for form data display
        add_action('add_meta_boxes', array($this, 'add_form_data_meta_box'));
    }

    public function add_form_data_meta_box()
    {
        add_meta_box(
            'webflow_contact_form_data',
            'Form Submission Data',
            array($this, 'display_form_data_meta_box'),
            'webflow_contact_forms',
            'normal',
            'default'
        );
    }

    public function display_form_data_meta_box($post)
    {
        $form_data = get_post_meta($post->ID, '_form_data', true);
        $submission_page = get_post_meta($post->ID, '_submission_page', true);
        $submission_time = get_post_meta($post->ID, '_submission_time', true);

        echo '<div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 15px;">';
        echo '<strong>Submission Details:</strong><br>';
        echo '<strong>Page:</strong> ' . esc_html($submission_page) . '<br>';
        echo '<strong>Time:</strong> ' . esc_html($submission_time) . '<br>';
        echo '</div>';

        if ($form_data) {
            echo '<table class="widefat" style="margin-top: 10px;">';
            echo '<thead><tr><th>Field</th><th>Value</th></tr></thead>';
            echo '<tbody>';

            foreach ($form_data as $key => $value) {
                if (is_array($value)) {
                    $value = implode(', ', $value);
                }
                echo '<tr>';
                echo '<td><strong>' . esc_html(ucfirst(str_replace('_', ' ', $key))) . '</strong></td>';
                echo '<td>' . esc_html($value) . '</td>';
                echo '</tr>';
            }

            echo '</tbody></table>';

            // Add reply button if email exists
            if (isset($form_data['email'])) {
                echo '<div style="margin-top: 15px;">';
                echo '<a href="mailto:' . esc_attr($form_data['email']) . '" class="button button-primary">Reply to ' . esc_html($form_data['email']) . '</a>';
                echo '</div>';
            }
        } else {
            echo '<p>No form data available.</p>';
        }
    }

    public function enqueue_scripts()
    {
        // Only load on pages that might have contact forms
        if ($this->should_load_contact_handler()) {
            wp_enqueue_script('jquery');
            wp_localize_script('jquery', 'webflowContactHandler', array(
                'ajax_url' => admin_url('admin-ajax.php'),
                'nonce' => wp_create_nonce('webflow_contact_nonce'),
                'current_page' => get_permalink()
            ));

            // Add inline JavaScript for form handling
            add_action('wp_footer', array($this, 'add_contact_form_script'));
        }
    }

    private function should_load_contact_handler()
    {
        $settings = get_option('webflow_contact_handler_settings', array());

        if (!isset($settings['auto_detect_contact_pages']) || !$settings['auto_detect_contact_pages']) {
            return false;
        }

        $current_url = $_SERVER['REQUEST_URI'] ?? '';
        $keywords = explode(',', $settings['trigger_keywords'] ?? 'contact');

        foreach ($keywords as $keyword) {
            if (stripos($current_url, trim($keyword)) !== false) {
                return true;
            }
        }

        return false;
    }

    public function add_contact_form_script()
    {
        ?>
        <script type="text/javascript">
            jQuery(document).ready(function ($) {
                // Intercept all form submissions on contact pages
                $('form').on('submit', function (e) {
                    var form = $(this);
                    var formData = new FormData(this);

                    // Check if form has email field (indicates it's a contact form)
                    var hasEmail = form.find('input[type="email"], input[name*="email"], input[id*="email"]').length > 0;

                    if (hasEmail) {
                        // Prevent default form submission
                        e.preventDefault();

                        // Collect all form data
                        var contactData = {};
                        formData.forEach(function (value, key) {
                            contactData[key] = value;
                        });

                        // Add current page URL
                        contactData['_referrer'] = window.location.href;

                        // Submit via AJAX
                        $.ajax({
                            url: webflowContactHandler.ajax_url,
                            type: 'POST',
                            data: {
                                action: 'webflow_contact_submit',
                                nonce: webflowContactHandler.nonce,
                                contact_data: contactData,
                                referrer: window.location.href
                            },
                            success: function (response) {
                                if (response.success) {
                                    // Show success message
                                    var successMsg = '<div style="background: #d4edda; color: #155724; padding: 15px; border: 1px solid #c3e6cb; border-radius: 4px; margin: 10px 0;">Thank you! Your message has been sent successfully.</div>';
                                    form.before(successMsg);
                                    form[0].reset();

                                    // Remove success message after 5 seconds
                                    setTimeout(function () {
                                        form.prev().fadeOut();
                                    }, 5000);
                                } else {
                                    alert('Error: ' + (response.data || 'Failed to send message'));
                                }
                            },
                            error: function () {
                                alert('Error: Failed to send message. Please try again.');
                            }
                        });
                    }
                });
            });
        </script>
        <?php
    }

    public function handle_contact_form()
    {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'webflow_contact_nonce')) {
            wp_send_json_error('Security check failed');
            return;
        }

        $contact_data = $_POST['contact_data'] ?? array();
        $referrer = sanitize_text_field($_POST['referrer'] ?? '');

        if (empty($contact_data)) {
            wp_send_json_error('No form data received');
            return;
        }

        // Sanitize form data
        $sanitized_data = array();
        foreach ($contact_data as $key => $value) {
            $key = sanitize_key($key);
            if (is_array($value)) {
                $value = array_map('sanitize_textarea_field', $value);
                $sanitized_data[$key] = implode(', ', $value);
            } else {
                $sanitized_data[$key] = sanitize_textarea_field($value);
            }
        }

        $settings = get_option('webflow_contact_handler_settings', array());

        try {
            switch ($settings['on_send_form'] ?? 'both') {
                case 'only_save':
                    $this->save_form_data($sanitized_data, $referrer);
                    break;
                case 'only_send':
                    $this->send_form_email($sanitized_data, $settings);
                    break;
                default: // 'both'
                    $this->save_form_data($sanitized_data, $referrer);
                    $this->send_form_email($sanitized_data, $settings);
                    break;
            }

            wp_send_json_success('Form submitted successfully');

        } catch (Exception $e) {
            wp_send_json_error($e->getMessage());
        }
    }

    private function save_form_data($form_data, $referrer)
    {
        // Determine post title
        $post_title = 'New Contact Submission';
        if (isset($form_data['name'])) {
            $post_title = 'Message from ' . $form_data['name'];
        } elseif (isset($form_data['email'])) {
            $post_title = 'Message from ' . $form_data['email'];
        }

        $post_id = wp_insert_post(array(
            'post_title' => $post_title,
            'post_type' => 'webflow_contact_forms',
            'post_status' => 'publish',
            'post_content' => '', // We'll store data in meta
        ));

        if (is_wp_error($post_id)) {
            throw new Exception('Failed to save form data: ' . $post_id->get_error_message());
        }

        // Store form data and metadata
        update_post_meta($post_id, '_form_data', $form_data);
        update_post_meta($post_id, '_submission_page', $referrer);
        update_post_meta($post_id, '_submission_time', current_time('mysql'));
    }

    private function send_form_email($form_data, $settings)
    {
        $to = $settings['email_to'] ?? get_option('admin_email');
        $subject = $settings['email_subject'] ?? 'New message from ' . get_bloginfo('name');

        // Build email message
        $message = "Someone sent a message from " . get_bloginfo('name') . ":\n\n";

        foreach ($form_data as $key => $value) {
            if ($key !== '_referrer') {
                $message .= ucfirst(str_replace('_', ' ', $key)) . ": " . $value . "\n";
            }
        }

        if (isset($form_data['_referrer'])) {
            $message .= "\nSubmitted from: " . $form_data['_referrer'];
        }

        // Set up headers
        $headers = array(
            'Content-Type: text/plain; charset=UTF-8',
            'From: ' . get_bloginfo('name') . ' <' . get_option('admin_email') . '>'
        );

        // Add reply-to if email provided
        if (isset($form_data['email'])) {
            $name = isset($form_data['name']) ? $form_data['name'] : $form_data['email'];
            $headers[] = 'Reply-To: ' . $name . ' <' . $form_data['email'] . '>';
        }

        if (!wp_mail($to, $subject, $message, $headers)) {
            throw new Exception('Failed to send email');
        }
    }

    public function add_admin_menu()
    {
        // Add settings page as submenu under Contact Forms
        add_submenu_page(
            'edit.php?post_type=webflow_contact_forms',
            'Contact Form Settings',
            'Settings',
            'manage_options',
            'webflow-contact-settings',
            array($this, 'admin_settings_page')
        );
    }

    public function admin_settings_page()
    {
        // Handle form submission
        if (isset($_POST['submit']) && wp_verify_nonce($_POST['_wpnonce'], 'webflow_contact_settings-options')) {
            $settings = array(
                'on_send_form' => sanitize_text_field($_POST['on_send_form']),
                'email_to' => sanitize_email($_POST['email_to']),
                'email_subject' => sanitize_text_field($_POST['email_subject']),
                'auto_detect_contact_pages' => !empty($_POST['auto_detect_contact_pages']),
                'trigger_keywords' => sanitize_text_field($_POST['trigger_keywords'])
            );

            update_option('webflow_contact_handler_settings', $settings);
            set_transient('webflow_contact_settings_saved', true, 30);
        }

        $settings = get_option('webflow_contact_handler_settings', array());
        ?>
        <div class="wrap">
            <h1>Contact Form Handler Settings</h1>

            <div class="notice notice-info">
                <p><strong>Auto-Detection Active:</strong> This plugin automatically handles forms on pages containing
                    contact-related keywords.</p>
                <p><strong>Supported Forms:</strong> Any HTML form with an email field on detected pages.</p>
            </div>

            <form method="post" action="">
                <?php wp_nonce_field('webflow_contact_settings-options'); ?>

                <table class="form-table">
                    <tr>
                        <th scope="row">Auto-Detect Contact Pages</th>
                        <td>
                            <label>
                                <input type="checkbox" name="auto_detect_contact_pages" value="1" <?php checked($settings['auto_detect_contact_pages'] ?? true, 1); ?>>
                                Automatically handle forms on contact pages
                            </label>
                            <p class="description">When enabled, forms will be handled on pages containing trigger keywords</p>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row">Trigger Keywords</th>
                        <td>
                            <input type="text" name="trigger_keywords" class="regular-text"
                                value="<?php echo esc_attr($settings['trigger_keywords'] ?? 'contact,contact-us,get-in-touch,reach-out'); ?>">
                            <p class="description">Comma-separated keywords to detect in page URLs (e.g., contact, contact-us,
                                get-in-touch)</p>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row">Form Action</th>
                        <td>
                            <select name="on_send_form">
                                <option value="both" <?php selected($settings['on_send_form'] ?? 'both', 'both'); ?>>Save form
                                    data and send email</option>
                                <option value="only_save" <?php selected($settings['on_send_form'] ?? 'both', 'only_save'); ?>>
                                    Only save form data</option>
                                <option value="only_send" <?php selected($settings['on_send_form'] ?? 'both', 'only_send'); ?>>
                                    Only send email</option>
                            </select>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row">Email To</th>
                        <td>
                            <input type="email" name="email_to" class="regular-text"
                                value="<?php echo esc_attr($settings['email_to'] ?? get_option('admin_email')); ?>">
                            <p class="description">Email address to receive form submissions</p>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row">Email Subject</th>
                        <td>
                            <input type="text" name="email_subject" class="regular-text"
                                value="<?php echo esc_attr($settings['email_subject'] ?? 'New message from ' . get_bloginfo('name')); ?>">
                        </td>
                    </tr>
                </table>

                <?php submit_button('Save Settings'); ?>
            </form>

            <div class="card" style="margin-top: 20px;">
                <h2>How It Works</h2>
                <ul>
                    <li><strong>Automatic Detection:</strong> Plugin monitors pages with contact-related URLs</li>
                    <li><strong>Form Handling:</strong> Intercepts forms with email fields using JavaScript</li>
                    <li><strong>Data Storage:</strong> Saves submissions to WordPress admin for review</li>
                    <li><strong>Email Notifications:</strong> Sends instant email alerts for new submissions</li>
                    <li><strong>No Configuration:</strong> Works with any HTML form automatically</li>
                </ul>
            </div>
        </div>
        <?php
    }

    public function admin_notices()
    {
        // Show activation notice
        if (get_transient('webflow_contact_handler_activated')) {
            echo '<div class="notice notice-success is-dismissible">';
            echo '<p><strong>Contact Form Handler Activated!</strong> ';
            echo 'All contact forms on pages containing contact keywords will now be handled automatically. ';
            echo '<a href="' . admin_url('edit.php?post_type=webflow_contact_forms&page=webflow-contact-settings') . '">Configure settings →</a>';
            echo '</p>';
            echo '</div>';
            delete_transient('webflow_contact_handler_activated');
        }

        // Show setup complete notice
        if ($setup_result = get_transient('webflow_contact_handler_setup_complete')) {
            $class = $setup_result['status'] === 'success' ? 'notice-success' : 'notice-error';
            echo '<div class="notice ' . $class . ' is-dismissible">';
            echo '<p><strong>Contact Form Setup:</strong> ' . esc_html($setup_result['message']);
            if ($setup_result['status'] === 'success') {
                echo ' <a href="' . admin_url('edit.php?post_type=webflow_contact_forms&page=webflow-contact-settings') . '">Configure settings →</a>';
            }
            echo '</p>';
            echo '</div>';
            delete_transient('webflow_contact_handler_setup_complete');
        }

        // Show settings saved notice
        if (get_transient('webflow_contact_settings_saved')) {
            echo '<div class="notice notice-success is-dismissible">';
            echo '<p><strong>✅ Settings Saved!</strong> Contact form handler configuration updated.</p>';
            echo '</div>';
            delete_transient('webflow_contact_settings_saved');
        }
    }
}

// Initialize the plugin
new WebflowContactFormHandler();
?>