// settings_modal.js - Complete JavaScript Code
class SettingsModal {
  constructor() {
    this.isOpen = false;
    this.activeTab = "automation";
    this.modalElement = null;
    this.emailConfig = {
      email: "",
      smtpHost: "",
      smtpPort: "587",
      smtpUser: "",
      smtpPassword: "",
      enableSSL: true,
      sendOnInactivity: false,
      inactivityHours: "3",
    };
    this.calendarConfig = {
      apiKey: "",
      clientId: "",
      clientSecret: "",
      refreshToken: "",
      calendarId: "",
      syncEnabled: false,
    };
    this.init();
  }

  init() {
    this.createModal();
    this.setupEventListeners();
    // Make sure modal starts hidden
    this.hide();
  }

  createModal() {
    // Check if modal already exists
    if (document.getElementById("settingsModalOverlay")) {
      return;
    }

    const modalHTML = `
            <div class="settings-modal-overlay" id="settingsModalOverlay">
                <div class="settings-modal-backdrop" id="settingsBackdrop"></div>
                <div class="settings-modal" id="settingsModalContent">
                    <!-- Header -->
                    <div class="settings-header">
                        <div class="settings-header-content">
                            <h2 class="settings-title">Settings</h2>
                            <button class="settings-close-btn" id="settingsCloseBtn">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <!-- Tabs -->
                    <div class="settings-tabs" id="settingsTabs">
                        <button class="settings-tab active" data-tab="automation">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                            Automation
                        </button>
                        <button class="settings-tab" data-tab="notifications">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                            </svg>
                            Notifications
                        </button>
                        <button class="settings-tab" data-tab="security">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                            </svg>
                            Security
                        </button>
                        <button class="settings-tab" data-tab="appearance">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="3"></circle>
                                <path d="M12 1v6m0 6v6m4.22-13.78l4.24 4.24M1.54 1.54l4.24 4.24"></path>
                            </svg>
                            Appearance
                        </button>
                    </div>

                    <!-- Content -->
                    <div class="settings-content" id="settingsContent">
                        <!-- Content will be rendered here -->
                    </div>

                    <!-- Footer -->
                    <div class="settings-footer">
                        <button class="btn-cancel" id="settingsCancelBtn">Cancel</button>
                        <button class="btn-save" id="settingsSaveBtn">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                                <polyline points="17 21 17 13 7 13 7 21"></polyline>
                                <polyline points="7 3 7 8 15 8"></polyline>
                            </svg>
                            Save Changes
                        </button>
                    </div>
                </div>
            </div>
        `;

    // Add modal to body
    document.body.insertAdjacentHTML("beforeend", modalHTML);
    this.modalElement = document.getElementById("settingsModalOverlay");

    // Render initial content
    this.renderContent();
  }

  renderContent() {
    const contentElement = document.getElementById("settingsContent");
    if (contentElement) {
      contentElement.innerHTML = this.renderTabContent(this.activeTab);
    }
  }

  renderTabContent(tab) {
    switch (tab) {
      case "automation":
        return this.renderAutomationTab();
      case "notifications":
        return `<div style="display: flex; align-items: center; justify-content: center; height: 256px; color: #94a3b8;">Notification settings coming soon...</div>`;
      case "security":
        return `<div style="display: flex; align-items: center; justify-content: center; height: 256px; color: #94a3b8;">Security settings coming soon...</div>`;
      case "appearance":
        return `<div style="display: flex; align-items: center; justify-content: center; height: 256px; color: #94a3b8;">Appearance settings coming soon...</div>`;
      default:
        return "";
    }
  }

  renderAutomationTab() {
    return `
            <div class="automation-content">
                <!-- Email Report Configuration -->
                <div class="settings-section email-section">
                    <div class="section-header">
                        <div class="section-icon email">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                                <polyline points="22,6 12,13 2,6"></polyline>
                            </svg>
                        </div>
                        <div class="section-info">
                            <h3>Email Report Configuration</h3>
                            <p>Configure SMTP settings for automated email reports</p>
                        </div>
                    </div>

                    <div class="form-grid">
                        <div class="form-group full-width">
                            <label class="form-label">Recipient Email</label>
                            <input type="email" class="form-input" id="emailRecipient" placeholder="admin@example.com" value="${
                              this.emailConfig.email
                            }">
                        </div>

                        <div class="form-group">
                            <label class="form-label">SMTP Host</label>
                            <input type="text" class="form-input" id="smtpHost" placeholder="smtp.gmail.com" value="${
                              this.emailConfig.smtpHost
                            }">
                        </div>

                        <div class="form-group">
                            <label class="form-label">SMTP Port</label>
                            <input type="text" class="form-input" id="smtpPort" placeholder="587" value="${
                              this.emailConfig.smtpPort
                            }">
                        </div>

                        <div class="form-group">
                            <label class="form-label">SMTP Username</label>
                            <input type="text" class="form-input" id="smtpUser" placeholder="username" value="${
                              this.emailConfig.smtpUser
                            }">
                        </div>

                        <div class="form-group">
                            <label class="form-label">SMTP Password</label>
                            <input type="password" class="form-input" id="smtpPassword" placeholder="••••••••" value="${
                              this.emailConfig.smtpPassword
                            }">
                        </div>
                    </div>

                    <div style="margin-top: 24px;">
                        <div class="toggle-item">
                            <div class="toggle-info">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="12" y1="8" x2="12" y2="12"></line>
                                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                </svg>
                                <div class="toggle-text">
                                    <h4>Enable SSL/TLS</h4>
                                    <p>Use secure connection for SMTP</p>
                                </div>
                            </div>
                            <button class="toggle-switch ${
                              this.emailConfig.enableSSL ? "active" : ""
                            }" data-toggle="enableSSL">
                                <div class="toggle-switch-handle"></div>
                            </button>
                        </div>

                        <div class="toggle-item">
                            <div class="toggle-info">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2">
                                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                                </svg>
                                <div class="toggle-text">
                                    <h4>Send email on inactivity</h4>
                                    <p>Alert when no activity for ${
                                      this.emailConfig.inactivityHours
                                    } hours</p>
                                </div>
                            </div>
                            <button class="toggle-switch ${
                              this.emailConfig.sendOnInactivity ? "active" : ""
                            }" data-toggle="sendOnInactivity">
                                <div class="toggle-switch-handle"></div>
                            </button>
                        </div>
                    </div>

                    <div class="section-actions">
                        <button class="btn-test" id="testEmailConnection">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                                <line x1="16" y1="13" x2="8" y2="13"></line>
                                <line x1="16" y1="17" x2="8" y2="17"></line>
                                <polyline points="10 9 9 9 8 9"></polyline>
                            </svg>
                            Test Connection
                        </button>
                    </div>
                </div>

                <!-- Google Calendar Settings -->
                <div class="settings-section calendar-section">
                    <div class="section-header">
                        <div class="section-icon calendar">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                        </div>
                        <div class="section-info">
                            <h3>Google Calendar Integration</h3>
                            <p>Connect your Google Calendar for synchronization</p>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">API Key</label>
                        <input type="text" class="form-input" id="calApiKey" placeholder="AIzaSy..." value="${
                          this.calendarConfig.apiKey
                        }">
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Client ID</label>
                            <input type="text" class="form-input" id="calClientId" placeholder="xxxx.apps.googleusercontent.com" value="${
                              this.calendarConfig.clientId
                            }">
                        </div>

                        <div class="form-group">
                            <label class="form-label">Client Secret</label>
                            <input type="password" class="form-input" id="calClientSecret" placeholder="••••••••" value="${
                              this.calendarConfig.clientSecret
                            }">
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Calendar ID</label>
                        <input type="text" class="form-input" id="calendarId" placeholder="primary or calendar@group.calendar.google.com" value="${
                          this.calendarConfig.calendarId
                        }">
                    </div>

                    <div class="toggle-item" style="margin-top: 24px;">
                        <div class="toggle-info">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2">
                                <polyline points="9 11 12 14 22 4"></polyline>
                                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                            </svg>
                            <div class="toggle-text">
                                <h4>Enable Sync</h4>
                                <p>Automatically sync calendar events</p>
                            </div>
                        </div>
                        <button class="toggle-switch ${
                          this.calendarConfig.syncEnabled ? "active" : ""
                        }" data-toggle="syncEnabled">
                            <div class="toggle-switch-handle"></div>
                        </button>
                    </div>

                    <div class="section-actions">
                        <button class="btn-authorize" id="authorizeCalendar">Authorize Access</button>
                        <button class="btn-refresh" id="refreshToken">Refresh Token</button>
                    </div>
                </div>
            </div>
        `;
  }

  setupEventListeners() {
    // Settings button in header - Main trigger
    const settingsBtn = document.getElementById("settings-btn");
    if (settingsBtn) {
      settingsBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.open();
      });
    }

    // Delegate event listeners for dynamically created elements
    document.addEventListener("click", (e) => {
      // Close button
      if (e.target.closest("#settingsCloseBtn")) {
        e.preventDefault();
        this.close();
      }

      // Cancel button
      if (e.target.closest("#settingsCancelBtn")) {
        e.preventDefault();
        this.close();
      }

      // Save button
      if (e.target.closest("#settingsSaveBtn")) {
        e.preventDefault();
        this.save();
      }

      // Backdrop click
      if (e.target.id === "settingsBackdrop") {
        this.close();
      }

      // Tab switching
      if (e.target.closest(".settings-tab")) {
        e.preventDefault();
        const tab = e.target.closest(".settings-tab");
        this.switchTab(tab.dataset.tab);
      }

      // Toggle switches
      if (e.target.closest(".toggle-switch")) {
        e.preventDefault();
        const toggle = e.target.closest(".toggle-switch");
        toggle.classList.toggle("active");
        this.updateToggleValue(toggle.dataset.toggle, toggle.classList.contains("active"));
      }

      // Test email connection
      if (e.target.closest("#testEmailConnection")) {
        e.preventDefault();
        this.testEmailConnection();
      }

      // Authorize calendar
      if (e.target.closest("#authorizeCalendar")) {
        e.preventDefault();
        this.authorizeCalendar();
      }

      // Refresh token
      if (e.target.closest("#refreshToken")) {
        e.preventDefault();
        this.refreshCalendarToken();
      }
    });

    // Input field updates with delegation
    document.addEventListener("input", (e) => {
      if (e.target.id === "emailRecipient") {
        this.emailConfig.email = e.target.value;
      } else if (e.target.id === "smtpHost") {
        this.emailConfig.smtpHost = e.target.value;
      } else if (e.target.id === "smtpPort") {
        this.emailConfig.smtpPort = e.target.value;
      } else if (e.target.id === "smtpUser") {
        this.emailConfig.smtpUser = e.target.value;
      } else if (e.target.id === "smtpPassword") {
        this.emailConfig.smtpPassword = e.target.value;
      } else if (e.target.id === "calApiKey") {
        this.calendarConfig.apiKey = e.target.value;
      } else if (e.target.id === "calClientId") {
        this.calendarConfig.clientId = e.target.value;
      } else if (e.target.id === "calClientSecret") {
        this.calendarConfig.clientSecret = e.target.value;
      } else if (e.target.id === "calendarId") {
        this.calendarConfig.calendarId = e.target.value;
      }
    });

    // Escape key to close
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && this.isOpen) {
        this.close();
      }
    });
  }

  switchTab(tab) {
    this.activeTab = tab;

    // Update tab buttons
    document.querySelectorAll(".settings-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tab);
    });

    // Update content
    this.renderContent();
  }

  updateToggleValue(toggle, value) {
    if (toggle === "enableSSL") {
      this.emailConfig.enableSSL = value;
    } else if (toggle === "sendOnInactivity") {
      this.emailConfig.sendOnInactivity = value;
    } else if (toggle === "syncEnabled") {
      this.calendarConfig.syncEnabled = value;
    }
  }

  show() {
    if (this.modalElement) {
      this.modalElement.style.display = "flex";
      this.modalElement.classList.add("active");
      this.isOpen = true;
      document.body.style.overflow = "hidden"; // Prevent background scrolling
    }
  }

  hide() {
    if (this.modalElement) {
      this.modalElement.style.display = "none";
      this.modalElement.classList.remove("active");
      this.isOpen = false;
      document.body.style.overflow = ""; // Restore scrolling
    }
  }

  open() {
    this.show();
    console.log("Settings modal opened");
  }

  close() {
    this.hide();
    console.log("Settings modal closed");
  }

  save() {
    // Collect all settings
    const settings = {
      email: this.emailConfig,
      calendar: this.calendarConfig,
    };

    // Log for debugging
    console.log("Saving settings:", settings);

    // Show saving state
    const saveBtn = document.getElementById("settingsSaveBtn");
    if (saveBtn) {
      const originalHTML = saveBtn.innerHTML;
      saveBtn.classList.add("saved");
      saveBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Saved
            `;

      setTimeout(() => {
        saveBtn.classList.remove("saved");
        saveBtn.innerHTML = originalHTML;
      }, 2000);
    }

    // Send to backend - uncomment and modify as needed
    /*
        fetch('/api/settings/automation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Settings saved successfully:', data);
            // You can add success notification here
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            // You can add error notification here
        });
        */
  }

  testEmailConnection() {
    console.log("Testing email connection with:", this.emailConfig);

    // Show testing state
    const testBtn = document.getElementById("testEmailConnection");
    if (testBtn) {
      const originalText = testBtn.innerHTML;
      testBtn.innerHTML = "Testing...";
      testBtn.disabled = true;

      // Simulate API call - replace with actual implementation
      setTimeout(() => {
        testBtn.innerHTML = originalText;
        testBtn.disabled = false;
        alert("Email connection test completed!");
      }, 2000);
    }

    // Actual API call - uncomment and modify as needed
    /*
        fetch('/api/settings/test-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(this.emailConfig)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Email connection successful!');
            } else {
                alert('Email connection failed: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error testing email:', error);
            alert('Error testing email connection');
        });
        */
  }

  authorizeCalendar() {
    console.log("Authorizing calendar with:", this.calendarConfig);

    // Implement OAuth flow
    alert("Opening Google authorization...\n\nThis would redirect to Google OAuth");

    // Actual implementation would involve:
    // 1. Redirect to Google OAuth URL
    // 2. Handle callback with authorization code
    // 3. Exchange code for tokens
    // 4. Store tokens securely

    /*
        window.location.href = `/api/calendar/authorize?client_id=${this.calendarConfig.clientId}`;
        */
  }

  refreshCalendarToken() {
    console.log("Refreshing calendar token");

    // Show refreshing state
    const refreshBtn = document.getElementById("refreshToken");
    if (refreshBtn) {
      const originalText = refreshBtn.innerHTML;
      refreshBtn.innerHTML = "Refreshing...";
      refreshBtn.disabled = true;

      setTimeout(() => {
        refreshBtn.innerHTML = originalText;
        refreshBtn.disabled = false;
        alert("Token refreshed successfully!");
      }, 1500);
    }

    // Actual API call - uncomment and modify as needed
    /*
        fetch('/api/calendar/refresh-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                refreshToken: this.calendarConfig.refreshToken
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.calendarConfig.refreshToken = data.newToken;
                alert('Token refreshed successfully!');
            } else {
                alert('Failed to refresh token: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error refreshing token:', error);
            alert('Error refreshing token');
        });
        */
  }

  // Method to load saved settings from backend
  loadSettings() {
    // Uncomment and modify as needed
    /*
        fetch('/api/settings/automation')
        .then(response => response.json())
        .then(data => {
            if (data.email) {
                this.emailConfig = { ...this.emailConfig, ...data.email };
            }
            if (data.calendar) {
                this.calendarConfig = { ...this.calendarConfig, ...data.calendar };
            }
            this.renderContent(); // Re-render with loaded data
        })
        .catch(error => {
            console.error('Error loading settings:', error);
        });
        */
  }
}

// Initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    window.settingsModal = new SettingsModal();
  });
} else {
  // DOM is already loaded
  window.settingsModal = new SettingsModal();
}
