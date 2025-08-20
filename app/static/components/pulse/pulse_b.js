/**
 * Enhanced Pulse Analytics Component with Filter Dialog & Multi-Space Support
 */

class PulseAnalytics {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.data = null;
    this.selectedDate = new Date().toISOString().split("T")[0];
    this.debugMode = false;
    this.currentModal = null;
    this.filterModal = null;

    // Status filters - default checked statuses
    this.statusFilters = {
      "to do": true,
      planning: true,
      "in progress": true,
      bugs: true,
      "for qa": false,
      "for viewing": false,
      grammar: false,
    };

    // Team member filters - default all checked
    this.memberFilters = {
      Arif: true,
      Jan: true,
      wiktor: true,
      Kendra: true,
      Calum: true,
      Tricia: true,
      Rick: true,
    };

    // NEW: Space filters - add your actual ClickUp spaces here
    this.spaceFilters = {
      90132462540: { name: "Web Design and App Development", checked: true },
      90134767504: { name: "Design & Creative Services", checked: false },
      90138214659: { name: "Digital Marketing", checked: false },
      90138873649: { name: "Production", checked: false },
      // Add more spaces as needed - get these from ClickUp API
    };

    this.init();
  }

  init() {
    this.render();
    this.loadAvailableSpaces();
    // this.loadData();
  }

  async loadData() {
    try {
      this.showLoading();

      // Build URL with parameters including all filters
      const params = new URLSearchParams();

      if (this.selectedDate !== new Date().toISOString().split("T")[0]) {
        params.append("date", this.selectedDate);
      }

      if (this.debugMode) {
        params.append("debug", "true");
      }

      // Add status filters
      const activeStatuses = Object.entries(this.statusFilters)
        .filter(([status, isActive]) => isActive)
        .map(([status, isActive]) => status);

      if (activeStatuses.length > 0) {
        activeStatuses.forEach((status) => {
          params.append("status_filter", status);
        });
      }

      // Add team member filters
      const activeMembers = Object.entries(this.memberFilters)
        .filter(([member, isActive]) => isActive)
        .map(([member, isActive]) => member);

      if (activeMembers.length > 0) {
        activeMembers.forEach((member) => {
          params.append("member_filter", member);
        });
      }

      // NEW: Add space filters
      const activeSpaces = Object.entries(this.spaceFilters)
        .filter(([spaceId, config]) => config.checked)
        .map(([spaceId, config]) => spaceId);

      if (activeSpaces.length > 0) {
        activeSpaces.forEach((spaceId) => {
          params.append("space_filter", spaceId);
        });
      }

      const url = `/api/pulse-data${params.toString() ? "?" + params.toString() : ""}`;
      console.log("📡 Fetching pulse data from:", url);
      console.log("🔍 Active status filters:", activeStatuses);
      console.log("👥 Active member filters:", activeMembers);
      console.log("🏢 Active space filters:", activeSpaces);

      const response = await fetch(url);
      const data = await response.json();

      if (data.error && !data.demo_data) {
        throw new Error(data.error);
      }

      this.data = data;
      console.log("📊 Received data:", this.data);
      this.render();

      if (this.debugMode && data.debug_info) {
        console.log("🐛 DEBUG INFO:", data.debug_info);
      }
    } catch (error) {
      console.error("Error loading pulse data:", error);
      this.showError(error.message);
    }
  }
  async loadAvailableSpaces() {
    try {
      const response = await fetch("/api/available-spaces");
      const data = await response.json();

      if (data.spaces) {
        // Update space filters with real data from ClickUp
        this.spaceFilters = {};

        Object.entries(data.spaces).forEach(([spaceId, spaceInfo]) => {
          this.spaceFilters[spaceId] = {
            name: spaceInfo.name,
            checked: spaceId === "90132462540", // Default: main space
          };
        });

        console.log("✅ Loaded available spaces:", this.spaceFilters);
      }
    } catch (error) {
      console.error("❌ Error loading available spaces:", error);
      // Keep default spaces if API fails
    }
  }
  showLoading() {
    this.container.innerHTML = `
                <div class="pulse-loading">
                    <div class="pulse-loading-spinner"></div>
                    <span>Loading workload analytics...</span>
                </div>
            `;
  }

  showError(message) {
    this.container.innerHTML = `
                <div class="pulse-container">
                    <div class="error-card">
                        <div class="error-icon">⚠️</div>
                        <h3>Unable to Load Pulse Data</h3>
                        <div class="error-message">${message}</div>
                        <div class="error-suggestions">
                            <h4>Possible Solutions:</h4>
                            <ul>
                                <li>• Try selecting a weekday instead of weekend</li>
                                <li>• Enable Debug Mode to see detailed error info</li>
                                <li>• Check if ClickUp API key is configured</li>
                                <li>• Verify team member usernames match ClickUp</li>
                                <li>• Check browser console for more details</li>
                            </ul>
                        </div>
                        <div class="error-actions">
                            <button onclick="location.reload()" class="retry-btn">🔄 Reload Page</button>
                            <button onclick="this.closest('.pulse-container').parentElement.querySelector('.pulse-analytics').loadData()" class="retry-btn">📡 Retry API Call</button>
                        </div>
                    </div>
                </div>
            `;
  }

  render() {
    if (!this.data) {
      console.log("❌ No data available for rendering");
      return;
    }

    console.log("🎨 Starting render with data:", {
      member_workloads: Object.keys(this.data.member_workloads || {}),
      project_analytics: Object.keys(this.data.project_analytics || {}),
      load_balance_insights: !!this.data.load_balance_insights,
      recommendations: this.data.recommendations?.length || 0,
    });

    try {
      // Render each section individually to catch errors
      const controls = this.renderControls();
      console.log("✅ Controls rendered");

      const overviewStats = this.renderOverviewStats();
      console.log("✅ Overview stats rendered");

      const memberWorkloads = this.renderMemberWorkloads();
      console.log("✅ Member workloads rendered");

      const projectDistribution = this.renderProjectDistribution();
      console.log("✅ Project distribution rendered");

      const loadBalanceInsights = this.renderLoadBalanceInsights();
      console.log("✅ Load balance insights rendered");

      const recommendations = this.renderRecommendations();
      console.log("✅ Recommendations rendered");

      this.container.innerHTML = `
                <div class="pulse-container">
                    ${controls}
                    ${overviewStats}
                    <div class="pulse-main-content">
                        <div class="pulse-left-column">
                            ${memberWorkloads}
                            ${projectDistribution}
                        </div>
                        <div class="pulse-right-column">
                            ${loadBalanceInsights}
                            ${recommendations}
                        </div>
                    </div>
                    ${this.debugMode && this.data.debug_info ? this.renderDebugInfo() : ""}
                </div>
            `;

      console.log("✅ Main container rendered successfully");
      this.setupControlEvents();
      this.setupClickableWorkloadStats();
    } catch (error) {
      console.error("❌ Error during rendering:", error);
      this.container.innerHTML = `
        <div class="pulse-container">
          <div class="error-card">
            <h3>Rendering Error</h3>
            <p>Error: ${error.message}</p>
            <p>Check console for details</p>
          </div>
        </div>
      `;
    }
  }

  renderControls() {
    try {
      const isToday = this.selectedDate === new Date().toISOString().split("T")[0];
      const dateObj = new Date(this.selectedDate);
      const isWeekend = dateObj.getDay() === 0 || dateObj.getDay() === 6;
      const isHistorical = this.data.cache_info?.is_historical;

      // Count active filters for summary
      const activeStatusCount = Object.values(this.statusFilters).filter(Boolean).length;
      const totalStatusCount = Object.keys(this.statusFilters).length;

      const activeMemberCount = Object.values(this.memberFilters).filter(Boolean).length;
      const totalMemberCount = Object.keys(this.memberFilters).length;

      const activeSpaceCount = Object.values(this.spaceFilters).filter(
        (config) => config.checked
      ).length;
      const totalSpaceCount = Object.keys(this.spaceFilters).length;

      return `
                <div class="pulse-controls">
                    <div class="pulse-header">
                        <h2>
                            <span>⚖️</span>
                            Team Pulse Analytics
                            ${this.data.demo_data ? '<span class="demo-badge">DEMO</span>' : ""}
                            ${
                              isHistorical ? '<span class="historical-badge">HISTORICAL</span>' : ""
                            }
                        </h2>
                        <div class="pulse-subtitle">
                            ${
                              isHistorical
                                ? `Historical workload data from ${
                                    this.data.cache_info?.source_file || "cache"
                                  } • Generated: ${
                                    this.data.cache_info?.generated_date || "unknown"
                                  }`
                                : `Workload distribution and load balancing insights${
                                    this.data.data_source
                                      ? ` • Source: ${this.data.data_source}`
                                      : ""
                                  }`
                            }
                        </div>
                    </div>
                    
                    <div class="control-row">
                        <div class="date-controls">
                            <label for="pulse-date-picker">📅 Analysis Date</label>
                            
                            <div class="date-picker-group">
                                <div class="date-picker-container">
                                    <input type="date" 
                                           id="pulse-date-picker" 
                                           value="${this.selectedDate}"
                                           max="${new Date().toISOString().split("T")[0]}"
                                           class="date-picker">
                                </div>
                                
                                <div class="quick-date-buttons">
                                    <button id="pulse-today-btn" class="control-btn ${
                                      isToday ? "active" : ""
                                    }">Today</button>
                                    <button id="pulse-yesterday-btn" class="control-btn">Yesterday</button>
                                </div>
                            </div>
                            
                            ${
                              isWeekend
                                ? `
                                <div class="date-status-notices">
                                    <div class="weekend-notice">Weekend selected - limited data expected</div>
                                </div>
                            `
                                : ""
                            }
                        </div>
                        
                        <div class="filter-and-debug-controls">
                            <!-- NEW: Filter Button -->
                            <button id="open-filters-btn" class="filter-btn">
                                <span class="filter-icon">🎛️</span>
                                <span class="filter-text">Filters</span>
                                <span class="filter-summary">
                                    ${activeStatusCount}/${totalStatusCount} statuses • 
                                    ${activeMemberCount}/${totalMemberCount} members • 
                                    ${activeSpaceCount}/${totalSpaceCount} spaces
                                </span>
                            </button>
                            
                            <label class="debug-toggle">
                                <input type="checkbox" id="pulse-debug-toggle" ${
                                  this.debugMode ? "checked" : ""
                                }>
                                <span class="toggle-slider"></span>
                                🐛 Debug Mode
                            </label>
                            <button id="pulse-refresh-btn" class="control-btn">🔄 Refresh</button>
                        </div>
                    </div>
                </div>
            `;
    } catch (error) {
      console.error("❌ Error rendering controls:", error);
      return `<div class="error">Error rendering controls: ${error.message}</div>`;
    }
  }

  renderFilterModal() {
    const activeStatusCount = Object.values(this.statusFilters).filter(Boolean).length;
    const totalStatusCount = Object.keys(this.statusFilters).length;

    const activeMemberCount = Object.values(this.memberFilters).filter(Boolean).length;
    const totalMemberCount = Object.keys(this.memberFilters).length;

    const activeSpaceCount = Object.values(this.spaceFilters).filter(
      (config) => config.checked
    ).length;
    const totalSpaceCount = Object.keys(this.spaceFilters).length;

    return `
      <div class="filter-modal-overlay" id="filter-modal">
        <div class="filter-modal-content">
          <div class="filter-modal-header">
            <h3>🎛️ Pulse Analytics Filters</h3>
            <button class="filter-modal-close" id="close-filters-btn">×</button>
          </div>
          
          <div class="filter-modal-body">
            <!-- Status Filters Section -->
            <div class="filter-section">
              <div class="filter-section-header">
                <div class="filter-section-title">
                  <span class="filter-icon">🎯</span>
                  <span>Task Status Filters</span>
                  <span class="filter-count">(${activeStatusCount}/${totalStatusCount} selected)</span>
                </div>
                <div class="filter-section-actions">
                  <button class="filter-action-btn" data-action="select-all" data-type="status">All</button>
                  <button class="filter-action-btn" data-action="default" data-type="status">Default</button>
                  <button class="filter-action-btn" data-action="clear" data-type="status">Clear</button>
                </div>
              </div>
              
              <div class="filter-grid">
                ${Object.entries(this.statusFilters)
                  .map(
                    ([status, isChecked]) => `
                    <label class="filter-item ${isChecked ? "checked" : ""}">
                      <input type="checkbox" 
                             class="filter-checkbox"
                             data-filter-type="status"
                             data-filter-value="${status}"
                             ${isChecked ? "checked" : ""}>
                      <span class="filter-checkmark"></span>
                      <span class="filter-label">${this.formatStatusName(status)}</span>
                      <span class="filter-badge">${status}</span>
                    </label>
                  `
                  )
                  .join("")}
              </div>
            </div>

            <!-- Team Member Filters Section -->
            <div class="filter-section">
              <div class="filter-section-header">
                <div class="filter-section-title">
                  <span class="filter-icon">👥</span>
                  <span>Team Member Filters</span>
                  <span class="filter-count">(${activeMemberCount}/${totalMemberCount} selected)</span>
                </div>
                <div class="filter-section-actions">
                  <button class="filter-action-btn" data-action="select-all" data-type="member">All</button>
                  <button class="filter-action-btn" data-action="default" data-type="member">Default</button>
                  <button class="filter-action-btn" data-action="clear" data-type="member">Clear</button>
                </div>
              </div>
              
              <div class="filter-grid">
                ${Object.entries(this.memberFilters)
                  .map(
                    ([member, isChecked]) => `
                    <label class="filter-item ${isChecked ? "checked" : ""}">
                      <input type="checkbox" 
                             class="filter-checkbox"
                             data-filter-type="member"
                             data-filter-value="${member}"
                             ${isChecked ? "checked" : ""}>
                      <span class="filter-checkmark"></span>
                      <span class="filter-label">${member}</span>
                      <span class="filter-badge">@${member.toLowerCase()}</span>
                    </label>
                  `
                  )
                  .join("")}
              </div>
            </div>

            <!-- NEW: Space Filters Section -->
            <div class="filter-section">
              <div class="filter-section-header">
                <div class="filter-section-title">
                  <span class="filter-icon">🏢</span>
                  <span>ClickUp Space Filters</span>
                  <span class="filter-count">(${activeSpaceCount}/${totalSpaceCount} selected)</span>
                </div>
                <div class="filter-section-actions">
                  <button class="filter-action-btn" data-action="select-all" data-type="space">All</button>
                  <button class="filter-action-btn" data-action="default" data-type="space">Default</button>
                  <button class="filter-action-btn" data-action="clear" data-type="space">Clear</button>
                </div>
              </div>
              
              <div class="filter-grid">
                ${Object.entries(this.spaceFilters)
                  .map(
                    ([spaceId, config]) => `
                    <label class="filter-item ${config.checked ? "checked" : ""}">
                      <input type="checkbox" 
                             class="filter-checkbox"
                             data-filter-type="space"
                             data-filter-value="${spaceId}"
                             ${config.checked ? "checked" : ""}>
                      <span class="filter-checkmark"></span>
                      <span class="filter-label">${config.name}</span>
                      <span class="filter-badge">${spaceId}</span>
                    </label>
                  `
                  )
                  .join("")}
              </div>
            </div>
          </div>
          
          <div class="filter-modal-footer">
            <div class="filter-info">
              <span>ℹ️ Only selected items will be included in workload calculations</span>
            </div>
            <div class="filter-modal-actions">
              <button class="filter-cancel-btn" id="cancel-filters-btn">Cancel</button>
              <button class="filter-apply-btn" id="apply-filters-btn">Apply Filters & Refresh</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  formatStatusName(status) {
    return status
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  }

  setupControlEvents() {
    // Date picker
    const datePicker = this.container.querySelector("#pulse-date-picker");
    if (datePicker) {
      datePicker.addEventListener("change", (e) => {
        this.selectedDate = e.target.value;
        this.loadData();
      });
    }

    // Today button
    const todayBtn = this.container.querySelector("#pulse-today-btn");
    if (todayBtn) {
      todayBtn.addEventListener("click", () => {
        this.selectedDate = new Date().toISOString().split("T")[0];
        this.loadData();
      });
    }

    // Yesterday button
    const yesterdayBtn = this.container.querySelector("#pulse-yesterday-btn");
    if (yesterdayBtn) {
      yesterdayBtn.addEventListener("click", () => {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        this.selectedDate = yesterday.toISOString().split("T")[0];
        this.loadData();
      });
    }

    // Debug toggle
    const debugToggle = this.container.querySelector("#pulse-debug-toggle");
    if (debugToggle) {
      debugToggle.addEventListener("change", (e) => {
        this.debugMode = e.target.checked;
        this.loadData();
      });
    }

    // Refresh button
    const refreshBtn = this.container.querySelector("#pulse-refresh-btn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        this.loadData();
      });
    }

    // NEW: Filter button
    const filterBtn = this.container.querySelector("#open-filters-btn");
    if (filterBtn) {
      filterBtn.addEventListener("click", () => {
        this.showFilterModal();
      });
    }
  }

  showFilterModal() {
    // Create modal if it doesn't exist
    const oldModal = document.getElementById("filter-modal");
    if (oldModal) {
      oldModal.remove();
    }

    if (!this.filterModal) {
      this.filterModal = document.createElement("div");
      this.filterModal.innerHTML = this.renderFilterModal();
      document.body.appendChild(this.filterModal.firstElementChild);
      this.filterModal = document.getElementById("filter-modal");
    } else {
      // Update existing modal content

      this.filterModal.innerHTML = this.renderFilterModal()
        .replace('<div class="filter-modal-overlay" id="filter-modal">', "")
        .replace("</div>", "");
      document.body.insertAdjacentHTML("beforeend", this.renderFilterModal());
    }
    this.bindFilterModalEvents();
    // Show modal
    this.filterModal.style.display = "flex";

    // Setup modal events
    this.setupFilterModalEvents();
  }
  bindFilterModalEvents() {
    const closeBtn = document.getElementById("close-filters-btn");
    const cancelBtn = document.getElementById("cancel-filters-btn");

    [closeBtn, cancelBtn].forEach((btn) => {
      if (btn) {
        btn.addEventListener("click", () => {
          const modal = document.getElementById("filter-modal");
          if (modal) modal.remove();
        });
      }
    });
  }
  hideFilterModal() {
    if (this.filterModal) {
      this.filterModal.style.display = "none";
    }
  }

  setupFilterModalEvents() {
    const modal = this.filterModal;

    // Close buttons
    const closeBtn = modal.querySelector("#close-filters-btn");
    const cancelBtn = modal.querySelector("#cancel-filters-btn");

    if (closeBtn) {
      closeBtn.addEventListener("click", () => this.hideFilterModal());
    }

    if (cancelBtn) {
      cancelBtn.addEventListener("click", () => this.hideFilterModal());
    }

    // Click outside to close
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        this.hideFilterModal();
      }
    });

    // Filter checkboxes
    const filterCheckboxes = modal.querySelectorAll(".filter-checkbox");
    filterCheckboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", (e) => {
        const filterType = e.target.getAttribute("data-filter-type");
        const filterValue = e.target.getAttribute("data-filter-value");
        const isChecked = e.target.checked;

        // Update filter state
        if (filterType === "status") {
          this.statusFilters[filterValue] = isChecked;
        } else if (filterType === "member") {
          this.memberFilters[filterValue] = isChecked;
        } else if (filterType === "space") {
          this.spaceFilters[filterValue].checked = isChecked;
        }

        // Update visual state
        const filterItem = e.target.closest(".filter-item");
        if (isChecked) {
          filterItem.classList.add("checked");
        } else {
          filterItem.classList.remove("checked");
        }

        // Update counts
        this.updateFilterCounts(modal);

        console.log(`${filterType} filter "${filterValue}" ${isChecked ? "enabled" : "disabled"}`);
      });
    });

    // Filter action buttons
    const actionButtons = modal.querySelectorAll(".filter-action-btn");
    actionButtons.forEach((button) => {
      button.addEventListener("click", (e) => {
        const action = e.target.getAttribute("data-action");
        const type = e.target.getAttribute("data-type");

        this.handleFilterAction(action, type, modal);
      });
    });

    // Apply button
    const applyBtn = modal.querySelector("#apply-filters-btn");
    if (applyBtn) {
      applyBtn.addEventListener("click", () => {
        this.hideFilterModal();
        this.loadData(); // Refresh data with new filters
      });
    }
  }

  handleFilterAction(action, type, modal) {
    let targetFilters;

    if (type === "status") {
      targetFilters = this.statusFilters;
    } else if (type === "member") {
      targetFilters = this.memberFilters;
    } else if (type === "space") {
      targetFilters = this.spaceFilters;
    }

    if (action === "select-all") {
      if (type === "space") {
        Object.values(targetFilters).forEach((config) => (config.checked = true));
      } else {
        Object.keys(targetFilters).forEach((key) => (targetFilters[key] = true));
      }
    } else if (action === "clear") {
      if (type === "space") {
        Object.values(targetFilters).forEach((config) => (config.checked = false));
      } else {
        Object.keys(targetFilters).forEach((key) => (targetFilters[key] = false));
      }
    } else if (action === "default") {
      if (type === "status") {
        this.statusFilters = {
          "to do": true,
          planning: true,
          "in progress": true,
          bugs: true,
          "for qa": false,
          "for viewing": false,
          grammar: false,
        };
      } else if (type === "member") {
        Object.keys(this.memberFilters).forEach((key) => (this.memberFilters[key] = true));
      } else if (type === "space") {
        // Default: only main workspace
        Object.entries(this.spaceFilters).forEach(([spaceId, config]) => {
          config.checked = spaceId === "90132462540"; // Set your main space ID
        });
      }
    }

    // Update UI
    this.updateFilterModalUI(modal);
    this.updateFilterCounts(modal);
  }

  updateFilterModalUI(modal) {
    // Update status checkboxes
    const statusCheckboxes = modal.querySelectorAll('[data-filter-type="status"]');
    statusCheckboxes.forEach((checkbox) => {
      const status = checkbox.getAttribute("data-filter-value");
      checkbox.checked = this.statusFilters[status];

      const filterItem = checkbox.closest(".filter-item");
      if (this.statusFilters[status]) {
        filterItem.classList.add("checked");
      } else {
        filterItem.classList.remove("checked");
      }
    });

    // Update member checkboxes
    const memberCheckboxes = modal.querySelectorAll('[data-filter-type="member"]');
    memberCheckboxes.forEach((checkbox) => {
      const member = checkbox.getAttribute("data-filter-value");
      checkbox.checked = this.memberFilters[member];

      const filterItem = checkbox.closest(".filter-item");
      if (this.memberFilters[member]) {
        filterItem.classList.add("checked");
      } else {
        filterItem.classList.remove("checked");
      }
    });

    // Update space checkboxes
    const spaceCheckboxes = modal.querySelectorAll('[data-filter-type="space"]');
    spaceCheckboxes.forEach((checkbox) => {
      const spaceId = checkbox.getAttribute("data-filter-value");
      checkbox.checked = this.spaceFilters[spaceId].checked;

      const filterItem = checkbox.closest(".filter-item");
      if (this.spaceFilters[spaceId].checked) {
        filterItem.classList.add("checked");
      } else {
        filterItem.classList.remove("checked");
      }
    });
  }

  updateFilterCounts(modal) {
    // Update status count
    const activeStatusCount = Object.values(this.statusFilters).filter(Boolean).length;
    const totalStatusCount = Object.keys(this.statusFilters).length;
    const statusCountEl = modal.querySelector(".filter-section:nth-child(1) .filter-count");
    if (statusCountEl) {
      statusCountEl.textContent = `(${activeStatusCount}/${totalStatusCount} selected)`;
    }

    // Update member count
    const activeMemberCount = Object.values(this.memberFilters).filter(Boolean).length;
    const totalMemberCount = Object.keys(this.memberFilters).length;
    const memberCountEl = modal.querySelector(".filter-section:nth-child(2) .filter-count");
    if (memberCountEl) {
      memberCountEl.textContent = `(${activeMemberCount}/${totalMemberCount} selected)`;
    }

    // Update space count
    const activeSpaceCount = Object.values(this.spaceFilters).filter(
      (config) => config.checked
    ).length;
    const totalSpaceCount = Object.keys(this.spaceFilters).length;
    const spaceCountEl = modal.querySelector(".filter-section:nth-child(3) .filter-count");
    if (spaceCountEl) {
      spaceCountEl.textContent = `(${activeSpaceCount}/${totalSpaceCount} selected)`;
    }

    // Update main filter button summary
    const filterBtn = this.container.querySelector("#open-filters-btn .filter-summary");
    if (filterBtn) {
      filterBtn.textContent = `${activeStatusCount}/${totalStatusCount} statuses • ${activeMemberCount}/${totalMemberCount} members • ${activeSpaceCount}/${totalSpaceCount} spaces`;
    }
  }

  // Keep all existing render methods (renderOverviewStats, renderMemberWorkloads, etc.)
  renderOverviewStats() {
    try {
      const stats = this.data.overview_stats || {};
      const healthScore = stats.health_score || 0;
      let healthClass = "excellent";

      if (healthScore < 50) {
        healthClass = "poor";
      } else if (healthScore < 70) {
        healthClass = "fair";
      } else if (healthScore < 85) {
        healthClass = "good";
      }

      return `
                <div class="pulse-overview">
                    <div class="pulse-metric-card">
                        <div class="pulse-metric-icon">👥</div>
                        <div class="pulse-metric-value">${stats.total_members || 0}</div>
                        <div class="pulse-metric-label">Active Members</div>
                    </div>
                    
                    <div class="pulse-metric-card">
                        <div class="pulse-metric-icon">📊</div>
                        <div class="pulse-metric-value">${stats.total_projects || 0}</div>
                        <div class="pulse-metric-label">Active Projects</div>
                    </div>
                    
                    <div class="pulse-metric-card">
                        <div class="pulse-metric-icon">✅</div>
                        <div class="pulse-metric-value">${stats.total_active_tasks || 0}</div>
                        <div class="pulse-metric-label">Active Tasks</div>
                    </div>
                    
                    <div class="pulse-metric-card">
                        <div class="pulse-metric-icon">⚖️</div>
                        <div class="pulse-metric-value">${stats.avg_tasks_per_member || 0}</div>
                        <div class="pulse-metric-label">Avg Tasks/Member</div>
                    </div>
                    
                    <div class="pulse-metric-card team-health-card">
                        <div class="pulse-metric-icon">💓</div>
                        <div class="pulse-metric-value health-score ${healthClass}">${healthScore}</div>
                        <div class="pulse-metric-label">Team Health</div>
                        <div class="health-indicator ${healthClass}" style="width: ${healthScore}%"></div>
                    </div>
                    
                    <div class="pulse-metric-card">
                        <div class="pulse-metric-icon">📈</div>
                        <div class="pulse-metric-value">${stats.avg_workload_score || 0}</div>
                        <div class="pulse-metric-label">Avg Workload Score</div>
                    </div>
                </div>
            `;
    } catch (error) {
      console.error("❌ Error rendering overview stats:", error);
      return `<div class="error">Error rendering overview stats: ${error.message}</div>`;
    }
  }

  renderMemberWorkloads() {
    try {
      const workloads = this.data.member_workloads || {};
      console.log("🔍 Rendering member workloads:", Object.keys(workloads));

      if (Object.keys(workloads).length === 0) {
        const activeStatuses = Object.entries(this.statusFilters)
          .filter(([status, isActive]) => isActive)
          .map(([status, isActive]) => status);

        const activeMembers = Object.entries(this.memberFilters)
          .filter(([member, isActive]) => isActive)
          .map(([member, isActive]) => member);

        const activeSpaces = Object.entries(this.spaceFilters)
          .filter(([spaceId, config]) => config.checked)
          .map(([spaceId, config]) => config.name);

        return `
                    <div class="workload-section">
                        <div class="section-header">
                            <h2 class="section-title">
                                <span>👥</span>
                                Member Workloads
                            </h2>
                        </div>
                        <div class="no-workloads">
                            <div style="text-align: center; padding: 40px; color: #64748b;">
                                <div style="font-size: 3rem; margin-bottom: 16px;">📊</div>
                                <h3>No Workload Data Available</h3>
                                <p>This could be because:</p>
                                <ul style="text-align: left; max-width: 500px; margin: 16px auto;">
                                    <li>• It's a weekend day</li>
                                    <li>• No team members have tasks with selected criteria</li>
                                    <li>• Selected status filters: ${activeStatuses.join(", ")}</li>
                                    <li>• Selected team members: ${activeMembers.join(", ")}</li>
                                    <li>• Selected spaces: ${activeSpaces.join(", ")}</li>
                                    <li>• API configuration issue</li>
                                </ul>
                                <p style="margin-top: 16px;">
                                    Try adjusting the filters using the <strong>🎛️ Filters</strong> button, or enabling Debug Mode for more info.
                                </p>
                            </div>
                        </div>
                    </div>
                `;
      }

      const sortedMembers = Object.entries(workloads).sort(
        ([, a], [, b]) => (b.workload_score || 0) - (a.workload_score || 0)
      );

      const memberCards = sortedMembers
        .map(([username, workload]) => {
          const remainingHours = Math.round(((workload.remaining_time || 0) / 60) * 10) / 10;

          return `
                    <div class="member-workload-card">
                        <div class="workload-score ${workload.status || "unknown"}">
                            ${workload.workload_score || 0}
                        </div>
                        
                        <div class="member-header">
                            <div class="member-info">
                                <h3>${workload.username || username}</h3>
                                <div class="member-summary">
                                    ${workload.active_tasks || 0} tasks across ${
            workload.projects_count || 0
          } project${(workload.projects_count || 0) !== 1 ? "s" : ""}
                                </div>
                            </div>
                            <span class="workload-status ${workload.status || "unknown"}">
                                ${workload.status || "unknown"}
                            </span>
                        </div>
                        
                        <div class="workload-details">
                            <div class="workload-stat clickable-stat" 
                                 data-clickable="true" 
                                 data-username="${username}" 
                                 data-task-type="all"
                                 title="Click to view all active tasks">
                                <div class="workload-stat-value">${workload.active_tasks || 0}</div>
                                <div class="workload-stat-label">Active Tasks</div>
                            </div>
                            <div class="workload-stat clickable-stat" 
                                 data-clickable="true" 
                                 data-username="${username}" 
                                 data-task-type="urgent"
                                 title="Click to view urgent tasks">
                                <div class="workload-stat-value">${workload.urgent_tasks || 0}</div>
                                <div class="workload-stat-label">Urgent</div>
                            </div>
                            <div class="workload-stat clickable-stat" 
                                 data-clickable="true" 
                                 data-username="${username}" 
                                 data-task-type="due_soon"
                                 title="Click to view due soon tasks">
                                <div class="workload-stat-value">${
                                  workload.due_soon_tasks || 0
                                }</div>
                                <div class="workload-stat-label">Due Soon</div>
                            </div>
                            <div class="workload-stat">
                                <div class="workload-stat-value">${remainingHours}h</div>
                                <div class="workload-stat-label">Remaining</div>
                            </div>
                        </div>
                    </div>
                `;
        })
        .join("");

      return `
                <div class="workload-section">
                    <div class="section-header">
                        <h2 class="section-title">
                            <span>👥</span>
                            Member Workloads
                            <span class="section-subtitle">Click on numbers to view task details</span>
                        </h2>
                    </div>
                    <div class="workload-grid">
                        ${memberCards}
                    </div>
                </div>
            `;
    } catch (error) {
      console.error("❌ Error rendering member workloads:", error);
      return `<div class="error">Error rendering member workloads: ${error.message}</div>`;
    }
  }

  renderLoadBalanceInsights() {
    try {
      const insights = this.data.load_balance_insights || {};
      console.log("🔍 Rendering load balance insights:", insights);

      const highestWorkload = insights.highest_workload;
      const lowestWorkload = insights.lowest_workload;

      const transferSuggestions = (insights.transfer_suggestions || [])
        .map(
          (suggestion) => `
          <div class="transfer-suggestion">
            <div class="transfer-header">
              <span class="transfer-members">
                ${suggestion.from_member || "Unknown"} 
                <span class="transfer-arrow">→</span> 
                ${suggestion.to_member || "Unknown"}
              </span>
            </div>
            <div class="transfer-task">
              <strong>Task:</strong> ${
                (suggestion.task && suggestion.task.name) || "Task redistribution"
              }
            </div>
            <div class="transfer-reason">
              ${suggestion.reason || "No reason provided"}
            </div>
          </div>
        `
        )
        .join("");

      return `
        <div class="insights-panel">
          <div class="section-header">
            <h3 class="section-title">
              <span>⚖️</span>
              Load Balance Insights
            </h3>
          </div>
          
          ${
            highestWorkload && lowestWorkload
              ? `
            <div class="insight-comparison">
              <div class="insight-card highest">
                <div class="insight-label">Highest Workload</div>
                <div class="insight-member">${highestWorkload.username || "Unknown"}</div>
                <div class="insight-score ${highestWorkload.status || "unknown"}">
                  Score: ${highestWorkload.score || 0}
                </div>
              </div>
              
              <div class="insight-card lowest">
                <div class="insight-label">Lowest Workload</div>
                <div class="insight-member">${lowestWorkload.username || "Unknown"}</div>
                <div class="insight-score ${lowestWorkload.status || "unknown"}">
                  Score: ${lowestWorkload.score || 0}
                </div>
              </div>
            </div>
          `
              : `
            <div class="no-insights">
              <p style="color: #64748b; text-align: center; padding: 20px;">
                📊 No workload comparison available yet
                ${this.debugMode ? "<br><small>Enable debug mode to see why</small>" : ""}
              </p>
            </div>
          `
          }
          
          ${
            insights.overloaded_members && insights.overloaded_members.length > 0
              ? `
            <div class="overloaded-alert">
              <h4>⚠️ Overloaded Members</h4>
              <ul>
                ${insights.overloaded_members
                  .map(
                    (member) => `
                    <li>${member.username || "Unknown"} - ${
                      member.workload?.active_tasks || 0
                    } tasks, score: ${member.workload?.workload_score || 0}</li>
                  `
                  )
                  .join("")}
              </ul>
            </div>
          `
              : ""
          }
          
          ${
            transferSuggestions
              ? `
            <div class="transfer-suggestions">
              <h4>💡 Transfer Suggestions</h4>
              ${transferSuggestions}
            </div>
          `
              : `
            <div class="no-suggestions">
              <p style="color: #64748b; text-align: center; padding: 16px; font-style: italic;">
                💡 No transfer suggestions available
              </p>
            </div>
          `
          }
        </div>
      `;
    } catch (error) {
      console.error("❌ Error rendering load balance insights:", error);
      return `<div class="error">Error rendering load balance insights: ${error.message}</div>`;
    }
  }

  renderRecommendations() {
    try {
      const recommendations = this.data.recommendations || [];
      console.log("🔍 Rendering recommendations:", recommendations.length);

      const recommendationItems = recommendations
        .map(
          (rec) => `
          <div class="recommendation-item ${rec.priority || "medium"}">
            <div class="recommendation-header">
              <span class="recommendation-type ${rec.priority || "medium"}">
                ${(rec.type || "general").replace("_", " ")}
              </span>
            </div>
            <div class="recommendation-message">
              ${rec.message || "No message provided"}
            </div>
            <div class="recommendation-action">
              <strong>Action:</strong> ${rec.action || "No action specified"}
            </div>
          </div>
        `
        )
        .join("");

      return `
        <div class="recommendations-panel">
          <div class="section-header">
            <h3 class="section-title">
              <span>💡</span>
              Recommendations
            </h3>
          </div>
          
          ${
            recommendations.length > 0
              ? recommendationItems
              : `
            <div class="no-recommendations">
              <p style="color: #22c55e; text-align: center; padding: 20px;">
                ✅ All good! No immediate actions needed.
                ${this.debugMode ? "<br><small>No workload issues detected</small>" : ""}
              </p>
            </div>
          `
          }
        </div>
      `;
    } catch (error) {
      console.error("❌ Error rendering recommendations:", error);
      return `<div class="error">Error rendering recommendations: ${error.message}</div>`;
    }
  }

  renderProjectDistribution() {
    try {
      const projects = this.data.project_analytics || {};
      console.log("🔍 Rendering project distribution:", Object.keys(projects));

      if (Object.keys(projects).length === 0) {
        return `
          <div class="project-distribution">
            <div class="section-header">
              <h3 class="section-title">
                <span>📊</span>
                Project Distribution
              </h3>
            </div>
            
            <div class="no-projects">
              <p style="color: #64748b; text-align: center; padding: 20px;">
                📋 No project data available
                ${this.debugMode ? "<br><small>Check debug console for details</small>" : ""}
              </p>
            </div>
          </div>
        `;
      }

      const projectCards = Object.entries(projects)
        .map(([projectId, project]) => {
          let dueDate = null;
          let daysUntilDue = null;
          let isDueSoon = false;

          try {
            if (project.due_date && project.due_date !== null) {
              dueDate = new Date(project.due_date);
              daysUntilDue = (dueDate - new Date()) / (1000 * 60 * 60 * 24);
              isDueSoon = daysUntilDue !== null && daysUntilDue <= 7;
            }
          } catch (dateError) {
            console.warn("Invalid date format for project:", project.name, project.due_date);
          }

          const estimatedHours = Math.round(((project.total_time_estimate || 0) / 60) * 10) / 10;

          const memberChips = (project.assigned_members || [])
            .map((member) => `<span class="project-member-chip">${member}</span>`)
            .join("");

          return `
            <div class="project-load-card">
              <div class="project-header">
                <div>
                  <div class="project-name">${project.name || "Unknown Project"}</div>
                  ${
                    dueDate
                      ? `
                    <div class="project-deadline ${isDueSoon ? "due-soon" : ""}">
                      Due: ${dueDate.toLocaleDateString()}
                      ${isDueSoon ? " (Soon!)" : ""}
                    </div>
                  `
                      : ""
                  }
                </div>
                <span class="project-priority ${project.priority || "medium"}">
                  ${project.priority || "medium"}
                </span>
              </div>
              
              <div class="project-stats">
                <div class="project-stat">
                  <div class="project-stat-value">${project.active_tasks || 0}</div>
                  <div class="project-stat-label">Tasks</div>
                </div>
                <div class="project-stat">
                  <div class="project-stat-value">${
                    project.member_count || project.assigned_members?.length || 0
                  }</div>
                  <div class="project-stat-label">Members</div>
                </div>
                <div class="project-stat">
                  <div class="project-stat-value">${estimatedHours}h</div>
                  <div class="project-stat-label">Estimated</div>
                </div>
              </div>
              
              ${
                (project.assigned_members || []).length > 0
                  ? `
                <div class="project-members">
                  ${memberChips}
                </div>
              `
                  : ""
              }
            </div>
          `;
        })
        .join("");

      return `
        <div class="project-distribution">
          <div class="section-header">
            <h3 class="section-title">
              <span>📊</span>
              Project Distribution
            </h3>
          </div>
          
          <div class="project-grid">
            ${projectCards}
          </div>
        </div>
      `;
    } catch (error) {
      console.error("❌ Error rendering project distribution:", error);
      return `<div class="error">Error rendering project distribution: ${error.message}</div>`;
    }
  }

  renderDebugInfo() {
    try {
      if (!this.data.debug_info) return "";

      return `
        <div class="debug-info-panel">
          <h3>🐛 Debug Information</h3>
          <div class="debug-content">
            <div class="debug-row">
              <strong>Analysis Date:</strong> ${this.data.debug_info.analysis_date || "N/A"}
            </div>
            <div class="debug-row">
              <strong>Is Weekend:</strong> ${this.data.debug_info.is_weekend ? "Yes" : "No"}
            </div>
            <div class="debug-row">
              <strong>Is Backdate:</strong> ${this.data.debug_info.is_backdate ? "Yes" : "No"}
            </div>
            <div class="debug-row">
              <strong>Total Team Members:</strong> ${
                this.data.debug_info.total_team_members || "N/A"
              }
            </div>
            ${
              this.data.debug_info.message
                ? `
              <div class="debug-row">
                <strong>Message:</strong> ${this.data.debug_info.message}
              </div>
            `
                : ""
            }
            <div class="debug-row">
              <strong>Data Source:</strong> ${this.data.data_source || "Unknown"}
            </div>
            ${
              this.data.cache_info
                ? `
              <div class="debug-row">
                <strong>Cache Source:</strong> ${this.data.cache_info.source_file || "N/A"}
              </div>
              <div class="debug-row">
                <strong>Generated Date:</strong> ${this.data.cache_info.generated_date || "N/A"}
              </div>
            `
                : ""
            }
            <div class="debug-row">
              <strong>Last Updated:</strong> ${new Date(this.data.last_updated).toLocaleString()}
            </div>
            ${
              this.data.filter_info
                ? `
              <div class="debug-row">
                <strong>Status Filters Applied:</strong> ${this.data.filter_info.status_filters_applied.join(
                  ", "
                )}
              </div>
              ${
                this.data.filter_info.member_filters_applied
                  ? `
                <div class="debug-row">
                  <strong>Member Filters Applied:</strong> ${this.data.filter_info.member_filters_applied.join(
                    ", "
                  )}
                </div>
              `
                  : ""
              }
              ${
                this.data.filter_info.space_filters_applied
                  ? `
                <div class="debug-row">
                  <strong>Space Filters Applied:</strong> ${this.data.filter_info.space_filters_applied.join(
                    ", "
                  )}
                </div>
              `
                  : ""
              }
            `
                : ""
            }
          </div>
        </div>
      `;
    } catch (error) {
      console.error("❌ Error rendering debug info:", error);
      return `<div class="error">Error rendering debug info: ${error.message}</div>`;
    }
  }

  setupClickableWorkloadStats() {
    this.container
      .querySelectorAll('.workload-stat[data-clickable="true"]')
      .forEach((statElement) => {
        statElement.addEventListener("click", (e) => {
          const username = statElement.getAttribute("data-username");
          const taskType = statElement.getAttribute("data-task-type");
          this.showTaskDetailsModal(username, taskType);
        });
      });
  }

  showTaskDetailsModal(username, taskType) {
    const workload = this.data.member_workloads[username];
    if (!workload) return;

    const allTasks = workload.tasks || [];
    let filteredTasks = [];
    let modalTitle = "";

    switch (taskType) {
      case "all":
        filteredTasks = allTasks;
        modalTitle = `${username}'s All Active Tasks`;
        break;
      case "urgent":
        filteredTasks = allTasks.filter((task) => task.priority?.priority === "urgent");
        modalTitle = `${username}'s Urgent Tasks`;
        break;
      case "due_soon":
        filteredTasks = allTasks.filter((task) => {
          if (!task.due_date) return false;
          const dueDate = new Date(parseInt(task.due_date));
          const daysUntilDue = Math.ceil((dueDate - new Date()) / (1000 * 60 * 60 * 24));
          return daysUntilDue <= 2 && daysUntilDue >= 0;
        });
        modalTitle = `${username}'s Due Soon Tasks`;
        break;
      default:
        filteredTasks = allTasks.filter((task) => task.status === taskType);
        modalTitle = `${username}'s ${taskType.charAt(0).toUpperCase() + taskType.slice(1)} Tasks`;
    }

    const modal = document.createElement("div");
    modal.className = "task-details-modal";
    modal.innerHTML = `
          <div class="task-details-content">
            <div class="task-details-header">
              <h3>${modalTitle} (${filteredTasks.length})</h3>
              <button class="task-details-close">×</button>
            </div>
            
            <div class="task-details-list">
              ${
                filteredTasks.length === 0
                  ? `<div class="task-details-empty">
                    <p>No ${taskType === "all" ? "" : taskType + " "}tasks found</p>
                  </div>`
                  : filteredTasks
                      .map(
                        (task) => `
                      <div class="task-item-modal">
                        <div class="task-item-header">
                          <h4 class="task-item-title">${task.name || "Unnamed Task"}</h4>
                          <div class="task-item-badges">
                            ${
                              task.priority
                                ? `
                              <span class="task-priority-badge task-priority-${
                                task.priority.priority
                              }">
                                ${task.priority.priority.toUpperCase()}
                              </span>
                            `
                                : ""
                            }
                            <span class="task-status-badge">${task.status || "unknown"}</span>
                          </div>
                        </div>
                        
                        <div class="task-item-meta">
                          <p>📁 Project: ${task.project_name || "Unknown"}</p>
                          ${
                            task.due_date
                              ? `
                            <p>📅 Due: ${new Date(parseInt(task.due_date)).toLocaleDateString()}</p>
                          `
                              : ""
                          }
                          ${
                            task.url
                              ? `
                            <p>🔗 <a href="${task.url}" target="_blank">Open in ClickUp</a></p>
                          `
                              : ""
                          }
                        </div>
                      </div>
                    `
                      )
                      .join("")
              }
            </div>
          </div>
        `;

    document.body.appendChild(modal);
    this.currentModal = modal;

    const closeBtn = modal.querySelector(".task-details-close");
    closeBtn.addEventListener("click", () => this.closeTaskDetailsModal());

    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        this.closeTaskDetailsModal();
      }
    });

    document.addEventListener("keydown", this.handleModalKeydown.bind(this));
  }

  closeTaskDetailsModal() {
    if (this.currentModal) {
      document.body.removeChild(this.currentModal);
      this.currentModal = null;
      document.removeEventListener("keydown", this.handleModalKeydown.bind(this));
    }
  }

  handleModalKeydown(e) {
    if (e.key === "Escape" && this.currentModal) {
      this.closeTaskDetailsModal();
    }
  }

  refresh() {
    this.loadData();
  }
}
