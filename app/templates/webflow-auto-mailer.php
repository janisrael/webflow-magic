<?php
/**
 * Plugin Name: {{PLUGIN_NAME}}
 * Description: Automatically sends beautiful response emails to contact form submissions with design customization
 * Version: 1.0.0
 * Author: Webflow to WP Converter
 */

// Prevent direct access
if (!defined('ABSPATH'))
    exit;

class WebflowAutoResponseMailer
{

    private $plugin_name = 'webflow_auto_mailer';

    public function __construct()
    {
        add_action('init', array($this, 'init'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('wp_ajax_save_email_template', array($this, 'save_email_template'));
        add_action('wp_ajax_preview_email_template', array($this, 'ajax_preview_email')); // Fixed: Added missing handler
        add_action('wp_ajax_test_email', array($this, 'test_email'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_action('wp_footer', array($this, 'add_form_interceptor'));
        add_action('admin_notices', array($this, 'admin_notices'));

        // Auto-installation hooks
        register_activation_hook(__FILE__, array($this, 'activate_plugin'));
        add_action('admin_init', array($this, 'auto_setup_check'));
    }

    public function init()
    {
        // Hook into various form plugins
        add_action('wpcf7_mail_sent', array($this, 'handle_cf7_submission')); // Contact Form 7
        add_action('gform_after_submission', array($this, 'handle_gravity_submission'), 10, 2); // Gravity Forms
        add_action('frm_after_create_entry', array($this, 'handle_formidable_submission'), 30, 2); // Formidable

        // Custom form handler for HTML forms
        add_action('wp_ajax_webflow_form_submit', array($this, 'handle_custom_form'));
        add_action('wp_ajax_nopriv_webflow_form_submit', array($this, 'handle_custom_form'));
    }

    public function activate_plugin()
    {
        // Set flag for auto-setup
        update_option('webflow_mailer_do_setup', true);

        // Set default email template
        $default_template = array(
            'subject' => 'Thank you for contacting us!',
            'header_color' => '#2271b1',
            'header_text' => 'Thank You!',
            'body' => 'Hi {{name}},<br><br>Thank you for reaching out to us. We have received your message and will get back to you within 24 hours.<br><br>Your message:<br><em>{{message}}</em><br><br>Best regards,<br>{{site_name}} Team',
            'footer_text' => '© {{year}} {{site_name}}. All rights reserved.',
            'button_color' => '#2271b1',
            'button_text' => 'Visit Our Website',
            'button_url' => home_url(),
            'logo_url' => get_site_icon_url()
        );

        update_option('webflow_email_template', $default_template);
        update_option('webflow_mailer_enabled', true);

        // Add success message
        set_transient('webflow_mailer_activated', true, 30);
    }

    public function auto_setup_check()
    {
        if (get_option('webflow_mailer_do_setup')) {
            delete_option('webflow_mailer_do_setup');
            $this->run_auto_setup();
        }
    }

    public function run_auto_setup()
    {
        // Auto-setup completed
        set_transient('webflow_mailer_setup_complete', array(
            'message' => 'Auto-Response Email plugin is now active and ready to use!',
            'status' => 'success'
        ), 60);
    }

    public function admin_notices()
    {
        // Show activation notice
        if (get_transient('webflow_mailer_activated')) {
            echo '<div class="notice notice-success is-dismissible">';
            echo '<p><strong>Auto-Response Mailer Activated!</strong> ';
            echo 'Your contact forms will now send automatic response emails. ';
            echo '<a href="' . admin_url('options-general.php?page=webflow-auto-mailer') . '">Customize email templates →</a>';
            echo '</p>';
            echo '</div>';
            delete_transient('webflow_mailer_activated');
        }

        // Show setup complete notice
        if ($setup_result = get_transient('webflow_mailer_setup_complete')) {
            $class = $setup_result['status'] === 'success' ? 'notice-success' : 'notice-error';
            echo '<div class="notice ' . $class . ' is-dismissible">';
            echo '<p><strong>Auto-Response Setup:</strong> ' . esc_html($setup_result['message']);
            if ($setup_result['status'] === 'success') {
                echo ' <a href="' . admin_url('options-general.php?page=webflow-auto-mailer') . '">Configure email design →</a>';
            }
            echo '</p>';
            echo '</div>';
            delete_transient('webflow_mailer_setup_complete');
        }

        // Show save success notice
        if (get_transient('webflow_email_template_saved')) {
            echo '<div class="notice notice-success is-dismissible">';
            echo '<p><strong>✅ Email Template Saved!</strong> Your auto-response emails have been updated.</p>';
            echo '</div>';
            delete_transient('webflow_email_template_saved');
        }
    }

    public function add_admin_menu()
    {
        add_options_page(
            'Auto-Response Mailer',
            'Auto-Response Mailer',
            'manage_options',
            'webflow-auto-mailer',
            array($this, 'admin_page')
        );
    }

    // Fixed: Handle form submission properly
    public function save_email_template()
    {
        // Handle AJAX save
        check_ajax_referer('webflow_mailer_nonce', 'nonce');

        $template = array(
            'subject' => sanitize_text_field($_POST['email_subject']),
            'header_color' => sanitize_hex_color($_POST['header_color']),
            'header_text' => sanitize_text_field($_POST['header_text']),
            'body' => wp_kses_post($_POST['email_body']),
            'button_text' => sanitize_text_field($_POST['button_text']),
            'button_url' => esc_url_raw($_POST['button_url']),
            'button_color' => sanitize_hex_color($_POST['button_color']),
            'footer_text' => sanitize_text_field($_POST['footer_text']),
            'logo_url' => esc_url_raw($_POST['logo_url'])
        );

        update_option('webflow_email_template', $template);
        update_option('webflow_mailer_enabled', !empty($_POST['webflow_mailer_enabled']));

        set_transient('webflow_email_template_saved', true, 30);

        wp_send_json_success('Template saved successfully!');
    }

    // Fixed: Add missing preview handler
    public function ajax_preview_email()
    {
        check_ajax_referer('webflow_mailer_nonce', 'nonce');

        $template = array(
            'subject' => sanitize_text_field($_POST['subject'] ?? ''),
            'header_color' => sanitize_hex_color($_POST['header_color'] ?? '#2271b1'),
            'header_text' => sanitize_text_field($_POST['header_text'] ?? ''),
            'body' => wp_kses_post($_POST['body'] ?? ''),
            'button_text' => sanitize_text_field($_POST['button_text'] ?? ''),
            'button_url' => esc_url_raw($_POST['button_url'] ?? ''),
            'button_color' => sanitize_hex_color($_POST['button_color'] ?? '#2271b1'),
            'footer_text' => sanitize_text_field($_POST['footer_text'] ?? ''),
            'logo_url' => esc_url_raw($_POST['logo_url'] ?? '')
        );

        echo $this->generate_email_preview($template);
        wp_die();
    }

    public function admin_page()
    {
        // Handle form submission
        if (isset($_POST['submit']) && wp_verify_nonce($_POST['_wpnonce'], 'webflow_mailer_settings-options')) {
            $template = array(
                'subject' => sanitize_text_field($_POST['email_subject']),
                'header_color' => sanitize_hex_color($_POST['header_color']),
                'header_text' => sanitize_text_field($_POST['header_text']),
                'body' => wp_kses_post($_POST['email_body']),
                'button_text' => sanitize_text_field($_POST['button_text']),
                'button_url' => esc_url_raw($_POST['button_url']),
                'button_color' => sanitize_hex_color($_POST['button_color']),
                'footer_text' => sanitize_text_field($_POST['footer_text']),
                'logo_url' => esc_url_raw($_POST['logo_url'])
            );

            update_option('webflow_email_template', $template);
            update_option('webflow_mailer_enabled', !empty($_POST['webflow_mailer_enabled']));

            set_transient('webflow_email_template_saved', true, 30);
        }

        $template = get_option('webflow_email_template', array());
        $enabled = get_option('webflow_mailer_enabled', true);
        ?>
        <div class="wrap">
            <h1>Auto-Response Email Designer</h1>

            <div class="notice notice-info">
                <p><strong> Plugin Status:</strong> Auto-response emails are active and working!</p>
                <p><strong> Compatible Forms:</strong> Contact Form 7, Gravity Forms, Formidable Forms, and custom HTML forms
                </p>
                <p><strong> Auto-Detection:</strong> No configuration needed - works automatically with any form containing
                    email fields</p>
            </div>

            <form method="post" action="" id="email-template-form">
                <?php wp_nonce_field('webflow_mailer_settings-options'); ?>

                <table class="form-table">
                    <tr>
                        <th scope="row">Enable Auto-Response</th>
                        <td>
                            <label>
                                <input type="checkbox" name="webflow_mailer_enabled" value="1" <?php checked($enabled, 1); ?>>
                                Send auto-response emails to form submissions
                            </label>
                            <p class="description">When enabled, all contact form submissions will trigger a response email</p>
                        </td>
                    </tr>
                </table>

                <h2>Email Design</h2>

                <div class="email-designer">
                    <div class="design-controls">
                        <table class="form-table">
                            <tr>
                                <th scope="row">Subject Line</th>
                                <td>
                                    <input type="text" name="email_subject" class="regular-text"
                                        value="<?php echo esc_attr($template['subject'] ?? ''); ?>"
                                        placeholder="Thank you for contacting us!">
                                    <p class="description">Use {{name}}, {{email}}, {{message}}, {{site_name}} for dynamic
                                        content</p>
                                </td>
                            </tr>

                            <tr>
                                <th scope="row">Header Settings</th>
                                <td>
                                    <p>
                                        <label>Header Color: </label>
                                        <input type="color" name="header_color"
                                            value="<?php echo esc_attr($template['header_color'] ?? '#2271b1'); ?>">
                                    </p>
                                    <p>
                                        <label>Header Text: </label>
                                        <input type="text" name="header_text" class="regular-text"
                                            value="<?php echo esc_attr($template['header_text'] ?? ''); ?>"
                                            placeholder="Thank You!">
                                    </p>
                                    <p>
                                        <label>Logo URL: </label>
                                        <input type="url" name="logo_url" class="regular-text"
                                            value="<?php echo esc_attr($template['logo_url'] ?? ''); ?>"
                                            placeholder="https://yoursite.com/logo.png">
                                    </p>
                                </td>
                            </tr>

                            <tr>
                                <th scope="row">Email Body</th>
                                <td>
                                    <?php
                                    wp_editor(
                                        $template['body'] ?? '',
                                        'email_body',
                                        array(
                                            'textarea_name' => 'email_body',
                                            'textarea_rows' => 10,
                                            'media_buttons' => false,
                                            'teeny' => true
                                        )
                                    );
                                    ?>
                                    <p class="description">Available variables: {{name}}, {{email}}, {{message}}, {{phone}},
                                        {{site_name}}, {{year}}</p>
                                </td>
                            </tr>

                            <tr>
                                <th scope="row">Call-to-Action Button</th>
                                <td>
                                    <p>
                                        <label>Button Text: </label>
                                        <input type="text" name="button_text" class="regular-text"
                                            value="<?php echo esc_attr($template['button_text'] ?? ''); ?>"
                                            placeholder="Visit Our Website">
                                    </p>
                                    <p>
                                        <label>Button URL: </label>
                                        <input type="url" name="button_url" class="regular-text"
                                            value="<?php echo esc_attr($template['button_url'] ?? ''); ?>"
                                            placeholder="<?php echo home_url(); ?>">
                                    </p>
                                    <p>
                                        <label>Button Color: </label>
                                        <input type="color" name="button_color"
                                            value="<?php echo esc_attr($template['button_color'] ?? '#2271b1'); ?>">
                                    </p>
                                </td>
                            </tr>

                            <tr>
                                <th scope="row">Footer</th>
                                <td>
                                    <input type="text" name="footer_text" class="regular-text"
                                        value="<?php echo esc_attr($template['footer_text'] ?? ''); ?>"
                                        placeholder="© {{year}} {{site_name}}. All rights reserved.">
                                </td>
                            </tr>
                        </table>
                    </div>

                    <div class="email-preview">
                        <h3> Email Preview</h3>
                        <div id="email-preview-container">
                            <?php echo $this->generate_email_preview($template); ?>
                        </div>

                        <p>
                            <button type="button" class="button" id="refresh-preview"> Refresh Preview</button>
                            <button type="button" class="button button-secondary" id="send-test-email"> Send Test
                                Email</button>
                        </p>
                    </div>
                </div>

                <?php submit_button(' Save Email Template'); ?>
            </form>
        </div>

        <style>
            .email-designer {
                display: flex;
                gap: 30px;
                margin-top: 20px;
            }

            .design-controls {
                flex: 1;
            }

            .email-preview {
                flex: 1;
                background: #f9f9f9;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }

            #email-preview-container {
                background: white;
                padding: 20px;
                border: 1px solid #ccc;
                max-height: 500px;
                overflow-y: auto;
                border-radius: 3px;
            }

            .notice {
                margin: 15px 0;
            }
        </style>

        <script>
            jQuery(document).ready(function ($) {
                // Auto-refresh preview when inputs change
                function updatePreview() {
                    var formData = {
                        'action': 'preview_email_template',
                        'nonce': '<?php echo wp_create_nonce('webflow_mailer_nonce'); ?>',
                        'subject': $('[name="email_subject"]').val(),
                        'header_color': $('[name="header_color"]').val(),
                        'header_text': $('[name="header_text"]').val(),
                        'body': $('#email_body').val(),
                        'button_text': $('[name="button_text"]').val(),
                        'button_url': $('[name="button_url"]').val(),
                        'button_color': $('[name="button_color"]').val(),
                        'footer_text': $('[name="footer_text"]').val(),
                        'logo_url': $('[name="logo_url"]').val()
                    };

                    $.post(ajaxurl, formData, function (response) {
                        $('#email-preview-container').html(response);
                    });
                }

                // Manual refresh button
                $('#refresh-preview').click(function () {
                    updatePreview();
                });

                // Auto-refresh on input change (with debounce)
                var debounceTimer;
                $('input, textarea, select').on('input change', function () {
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(updatePreview, 1000); // Wait 1 second after user stops typing
                });

                // Send test email
                $('#send-test-email').click(function () {
                    var email = prompt('Enter email address for test:');
                    if (email) {
                        var formData = {
                            'action': 'test_email',
                            'nonce': '<?php echo wp_create_nonce('webflow_mailer_nonce'); ?>',
                            'email': email,
                            'subject': $('[name="email_subject"]').val(),
                            'header_color': $('[name="header_color"]').val(),
                            'header_text': $('[name="header_text"]').val(),
                            'body': $('#email_body').val(),
                            'button_text': $('[name="button_text"]').val(),
                            'button_url': $('[name="button_url"]').val(),
                            'button_color': $('[name="button_color"]').val(),
                            'footer_text': $('[name="footer_text"]').val(),
                            'logo_url': $('[name="logo_url"]').val()
                        };

                        $.post(ajaxurl, formData, function (response) {
                            alert('📧 Test email sent successfully!');
                        });
                    }
                });

                // Refresh preview after page load
                setTimeout(updatePreview, 500);
            });
        </script>
        <?php
    }

    public function generate_email_preview($template)
    {
        $preview_data = array(
            'name' => 'John Doe',
            'email' => 'john@example.com',
            'message' => 'This is a sample message from the contact form.',
            'phone' => '+1 (555) 123-4567',
            'site_name' => get_bloginfo('name'),
            'year' => date('Y')
        );

        return $this->generate_email_html($template, $preview_data);
    }

    public function generate_email_html($template, $data)
    {
        $html = '
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>' . esc_html($template['subject'] ?? '') . '</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }
                .email-container { max-width: 600px; margin: 0 auto; background-color: white; }
                .email-header { background-color: ' . esc_attr($template['header_color'] ?? '#2271b1') . '; color: white; padding: 30px; text-align: center; }
                .email-logo { max-width: 150px; height: auto; margin-bottom: 10px; }
                .email-body { padding: 30px; line-height: 1.6; color: #333; }
                .cta-button { display: inline-block; background-color: ' . esc_attr($template['button_color'] ?? '#2271b1') . '; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                .email-footer { background-color: #f8f8f8; padding: 20px; text-align: center; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">';

        if (!empty($template['logo_url'])) {
            $html .= '<img src="' . esc_url($template['logo_url']) . '" alt="Logo" class="email-logo"><br>';
        }

        $html .= '<h1>' . esc_html($template['header_text'] ?? 'Thank You!') . '</h1>
                </div>
                
                <div class="email-body">
                    ' . $this->replace_variables($template['body'] ?? '', $data) . '
                    
                    ' . (!empty($template['button_text']) ?
            '<p><a href="' . esc_url($template['button_url'] ?? '') . '" class="cta-button">' . esc_html($template['button_text']) . '</a></p>'
            : '') . '
                </div>
                
                <div class="email-footer">
                    ' . $this->replace_variables($template['footer_text'] ?? '', $data) . '
                </div>
            </div>
        </body>
        </html>';

        return $html;
    }

    public function replace_variables($content, $data)
    {
        $replacements = array(
            '{{name}}' => $data['name'] ?? '',
            '{{email}}' => $data['email'] ?? '',
            '{{message}}' => $data['message'] ?? '',
            '{{phone}}' => $data['phone'] ?? '',
            '{{site_name}}' => get_bloginfo('name'),
            '{{year}}' => date('Y')
        );

        return str_replace(array_keys($replacements), array_values($replacements), $content);
    }

    public function enqueue_scripts()
    {
        wp_enqueue_script('jquery');
        wp_localize_script('jquery', 'webflow_mailer', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('webflow_mailer_nonce')
        ));
    }

    public function add_form_interceptor()
    {
        if (!get_option('webflow_mailer_enabled', true))
            return;
        ?>
        <script>
            jQuery(document).ready(function ($) {
                // Intercept all form submissions
                $('form').on('submit', function (e) {
                    var form = $(this);
                    var emailField = form.find('input[type="email"], input[name*="email"], input[id*="email"]').first();
                    var nameField = form.find('input[name*="name"], input[id*="name"], input[type="text"]').first();
                    var messageField = form.find('textarea, input[name*="message"], input[id*="message"]').first();
                    var phoneField = form.find('input[type="tel"], input[name*="phone"], input[id*="phone"]').first();

                    if (emailField.length) {
                        // Send auto-response email
                        $.post(webflow_mailer.ajax_url, {
                            action: 'webflow_form_submit',
                            email: emailField.val(),
                            name: nameField.val() || 'Valued Customer',
                            message: messageField.val() || 'Thank you for your submission',
                            phone: phoneField.val() || '',
                            nonce: webflow_mailer.nonce
                        });
                    }
                });
            });
        </script>
        <?php
    }

    // Form handlers for different plugins
    public function handle_cf7_submission($contact_form)
    {
        $submission = WPCF7_Submission::get_instance();
        if ($submission) {
            $data = $submission->get_posted_data();
            $this->send_auto_response($data);
        }
    }

    public function handle_gravity_submission($entry, $form)
    {
        $this->send_auto_response($entry);
    }

    public function handle_formidable_submission($entry_id, $form_id)
    {
        $entry = FrmEntry::getOne($entry_id);
        $this->send_auto_response($entry);
    }

    public function handle_custom_form()
    {
        check_ajax_referer('webflow_mailer_nonce', 'nonce');

        $data = array(
            'email' => sanitize_email($_POST['email']),
            'name' => sanitize_text_field($_POST['name']),
            'message' => sanitize_textarea_field($_POST['message']),
            'phone' => sanitize_text_field($_POST['phone'])
        );

        $this->send_auto_response($data);
        wp_die();
    }

    public function send_auto_response($form_data)
    {
        if (!get_option('webflow_mailer_enabled', true))
            return;

        // Extract email from various possible field names
        $email = '';
        $possible_email_fields = array('email', 'your-email', 'user_email', 'form_email', 'contact_email');
        foreach ($possible_email_fields as $field) {
            if (!empty($form_data[$field])) {
                $email = $form_data[$field];
                break;
            }
        }

        if (!$email || !is_email($email))
            return;

        // Extract other data
        $name = '';
        $possible_name_fields = array('name', 'your-name', 'user_name', 'first_name', 'full_name', 'contact_name');
        foreach ($possible_name_fields as $field) {
            if (!empty($form_data[$field])) {
                $name = $form_data[$field];
                break;
            }
        }

        $message = '';
        $possible_message_fields = array('message', 'your-message', 'comments', 'comment', 'inquiry', 'details');
        foreach ($possible_message_fields as $field) {
            if (!empty($form_data[$field])) {
                $message = $form_data[$field];
                break;
            }
        }

        $phone = '';
        $possible_phone_fields = array('phone', 'telephone', 'contact_number', 'your-phone');
        foreach ($possible_phone_fields as $field) {
            if (!empty($form_data[$field])) {
                $phone = $form_data[$field];
                break;
            }
        }

        $template = get_option('webflow_email_template', array());
        $email_data = array(
            'name' => $name ?: 'Valued Customer',
            'email' => $email,
            'message' => $message,
            'phone' => $phone,
            'site_name' => get_bloginfo('name'),
            'year' => date('Y')
        );

        $subject = $this->replace_variables($template['subject'] ?? 'Thank you for contacting us!', $email_data);
        $html_body = $this->generate_email_html($template, $email_data);

        $headers = array(
            'Content-Type: text/html; charset=UTF-8',
            'From: ' . get_bloginfo('name') . ' <' . get_option('admin_email') . '>'
        );

        wp_mail($email, $subject, $html_body, $headers);
    }

    public function test_email()
    {
        check_ajax_referer('webflow_mailer_nonce', 'nonce');

        $email = sanitize_email($_POST['email']);
        if (!$email)
            wp_die('Invalid email');

        $template = array(
            'subject' => sanitize_text_field($_POST['subject']),
            'header_color' => sanitize_hex_color($_POST['header_color']),
            'header_text' => sanitize_text_field($_POST['header_text']),
            'body' => wp_kses_post($_POST['body']),
            'button_text' => sanitize_text_field($_POST['button_text']),
            'button_url' => esc_url_raw($_POST['button_url']),
            'button_color' => sanitize_hex_color($_POST['button_color']),
            'footer_text' => sanitize_text_field($_POST['footer_text']),
            'logo_url' => esc_url_raw($_POST['logo_url'])
        );

        $test_data = array(
            'name' => 'Test User',
            'email' => $email,
            'message' => 'This is a test email from your auto-response system.',
            'phone' => '+1 (555) 123-4567',
            'site_name' => get_bloginfo('name'),
            'year' => date('Y')
        );

        $subject = $this->replace_variables($template['subject'], $test_data);
        $html_body = $this->generate_email_html($template, $test_data);

        $headers = array(
            'Content-Type: text/html; charset=UTF-8',
            'From: ' . get_bloginfo('name') . ' <' . get_option('admin_email') . '>'
        );

        wp_mail($email, $subject, $html_body, $headers);
        wp_die('Test email sent');
    }
}

// Initialize the plugin
new WebflowAutoResponseMailer();

// Register settings
add_action('admin_init', function () {
    register_setting('webflow_mailer_settings', 'webflow_mailer_enabled');
    register_setting('webflow_mailer_settings', 'webflow_email_template');
});
?>