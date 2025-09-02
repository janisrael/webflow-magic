/**
 * Enhanced Pulse Analytics Component - Combined Version
 * - Large filter controls with detailed preview
 * - Fixed responsive modal with animations
 * - Big "Generate Data" button
 * - Improved filter management
 */

console.log('📜 pulse.js script loaded successfully!');

class PulseAnalytics {
  constructor(containerId) {
    console.log('🚀 PulseAnalytics constructor called with containerId:', containerId);
    this.container = document.getElementById(containerId);
    console.log('📦 Container element:', this.container);
    this.data = null;
    this.selectedDate = new Date().toISOString().split("T")[0];
    this.debugMode = false;
    this.currentModal = null;
    this.filterModal = null;
    this.dataLoaded = false;

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

    // Space filters
    this.spaceFilters = {
      90132462540: { name: "Web Design and App Development", checked: true },
      90134767504: { name: "Design & Creative Services", checked: false },
      90138214659: { name: "Digital Marketing", checked: false },
      90138873649: { name: "Production", checked: false },
    };

    this.init();
  }

  init() {
    console.log('🎯 PulseAnalytics init() called');
    // REMOVED: Auto-load data on initialization
    // this.loadData();
    // this.checkForData();
    
    // NEW: Only render initial state, wait for tab activation
    this.renderInitialState();
    
    // Listen for tab activation events
    this.setupTabActivationListener();
  }

  async generateAssessment() {
    console.log('🚀 generateAssessment method called!');
    try {
      console.log('🔍 Generating comprehensive assessment...');
      
      // Show loading state
      const assessmentBtn = this.container.querySelector("#generate-assessment-btn");
      if (assessmentBtn) {
        assessmentBtn.innerHTML = '<span class="material-icons">hourglass_empty</span> Generating...';
        assessmentBtn.disabled = true;
      }
      
      // Build parameters for assessment report URL
      const params = new URLSearchParams();
      
      // Add current filters as URL parameters
      const activeStatuses = Object.entries(this.statusFilters)
        .filter(([status, isActive]) => isActive)
        .map(([status, isActive]) => status);
      
      const activeMembers = Object.entries(this.memberFilters)
        .filter(([member, isActive]) => isActive)
        .map(([member, isActive]) => member);
      
      const activeSpaces = Object.entries(this.spaceFilters)
        .filter(([spaceId, config]) => config.checked)
        .map(([spaceId, config]) => spaceId);
      
      console.log('📊 Active members:', activeMembers);
      console.log('📊 Active spaces:', activeSpaces);
      console.log('📊 Selected date:', this.selectedDate);
      
      // Build assessment report URL
      const assessmentUrl = `/assessment_report?` + 
        `team_id=${encodeURIComponent(activeMembers.join(','))}&` +
        `space_ids=${encodeURIComponent(activeSpaces.join(','))}&` +
        `list_ids=&` +
        `member_ids=${encodeURIComponent(activeMembers.join(','))}&` +
        `date_from=${this.selectedDate}&` +
        `date_to=${this.selectedDate}`;
      
      console.log('📊 Opening assessment report:', assessmentUrl);
      
      // Open assessment report in new tab
      window.open(assessmentUrl, '_blank');
      
    } catch (error) {
      console.error('Error generating assessment:', error);
      alert('❌ Error generating assessment: ' + error.message);
    } finally {
      // Reset button state
      const assessmentBtn = this.container.querySelector("#generate-assessment-btn");
      if (assessmentBtn) {
        assessmentBtn.innerHTML = '<span class="material-icons">assessment</span> Generate Assessment';
        assessmentBtn.disabled = false;
      }
    }
  }

  setupTabActivationListener() {
    // Listen for when this tab becomes active
    document.addEventListener('pulseTabActivated', () => {
      console.log('🎯 Pulse tab activated - checking for data...');
      this.onTabActivated();
    });
    
    // Also listen for general tab changes
    document.addEventListener('tabChanged', (event) => {
      if (event.detail.tab === 'pulse') {
        console.log('🎯 Pulse tab changed to active - checking for data...');
        this.onTabActivated();
      }
    });
  }

  onTabActivated() {
    // Only load data if we haven't already or if data is stale
    if (!this.dataLoaded || this.isDataStale()) {
      console.log('🔄 Tab activated - loading pulse data...');
      this.checkForData();
    } else {
      console.log('✅ Tab activated - using existing data');
      this.render(); // Re-render with existing data
    }
  }

  isDataStale() {
    // Check if data is older than 3 hours
    if (!this.data || !this.data.last_updated) {
      return true;
    }
    
    const lastUpdated = new Date(this.data.last_updated);
    const threeHoursAgo = new Date(Date.now() - (3 * 60 * 60 * 1000));
    
    return lastUpdated < threeHoursAgo;
  }

  refreshUI() {
    // Refresh the UI without loading new data
    if (this.dataLoaded && this.data) {
      console.log("🔄 Refreshing UI with existing data...");
      this.render();
    } else {
      console.log("📝 No data loaded - showing initial state...");
      this.renderInitialState();
    }
  }

  async checkForData() {
    try {
      console.log("🔍 Checking for pulse data using smart caching...");
      
      // FIRST: Check if we have cached data that's less than 3 hours old
      const cachedData = await this.checkForRecentCachedData();
      
      if (cachedData) {
        console.log("✅ Using recent cached data (< 3 hours old)");
        this.data = cachedData;
        this.dataLoaded = true;
        this.render();
        return;
      }
      
      // SECOND: Check if we have any data from today (even if older than 3 hours)
      const todayData = await this.checkForTodayCachedData();
      
      if (todayData) {
        console.log("📁 Using today's cached data (> 3 hours old)");
        this.data = todayData;
        this.dataLoaded = true;
        this.render();
        return;
      }
      
      // THIRD: No cached data available, show generate data section
      console.log("📝 No cached data found - showing generate data section");
      this.renderInitialState();
      
    } catch (error) {
      console.error("❌ Error checking for data:", error);
      this.renderInitialState();
    }
  }

  async checkForRecentCachedData() {
    try {
      // Check for data less than 3 hours old
      const params = new URLSearchParams();
      if (this.selectedDate !== new Date().toISOString().split("T")[0]) {
        params.append("date", this.selectedDate);
      }
      
      // Add a flag to check for recent cache only
      params.append("check_cache_only", "true");
      
      const url = `/api/pulse-data${params.toString() ? "?" + params.toString() : ""}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        return null;
      }
      
      const data = await response.json();
      
      // Check if we have valid member workload data
      const hasValidData = data && 
                          data.member_workloads && 
                          Object.keys(data.member_workloads).length > 0;
      
      if (hasValidData) {
        console.log("📊 Found recent cached data with valid workloads");
        return data;
      }
      
      return null;
      
    } catch (error) {
      console.error("Error checking for recent cached data:", error);
      return null;
    }
  }

  async checkForTodayCachedData() {
    try {
      // Check for any data from today (even if older than 3 hours)
      const params = new URLSearchParams();
      if (this.selectedDate !== new Date().toISOString().split("T")[0]) {
        params.append("date", this.selectedDate);
      }
      
      // Add a flag to check for today's cache only
      params.append("check_today_cache", "true");
      
      const url = `/api/pulse-data${params.toString() ? "?" + params.toString() : ""}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        return null;
      }
      
      const data = await response.json();
      
      // Check if we have valid member workload data
      const hasValidData = data && 
                          data.member_workloads && 
                          Object.keys(data.member_workloads).length > 0;
      
      if (hasValidData) {
        console.log("📁 Found today's cached data with valid workloads");
        return data;
      }
      
      return null;
      
    } catch (error) {
      console.error("Error checking for today's cached data:", error);
      return null;
    }
  }

  renderInitialState() {
    console.log('🎨 Rendering initial state with assessment button');
    this.container.innerHTML = `
      <div class="pulse-container">
        <div class="pulse-controls">
          <div class="pulse-header">
            <h2>Team Pulse Analytics</h2>
            <div class="pulse-subtitle">Workload distribution and load balancing insights</div>
          </div>
          
          <div class="control-row">
            <div class="debug-controls">
              <label class="debug-toggle">
                <input type="checkbox" id="pulse-debug-toggle" ${this.debugMode ? "checked" : ""}>
                <span class="toggle-slider"></span>
                Debug Mode
              </label>
              <button id="generate-assessment-btn" class="control-btn assessment-btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;">
                <span class="material-icons">assessment</span> Generate Assessment
              </button>
            </div>
          </div>
        </div>
        
        <div class="pulse-main-content">
          <div class="pulse-message">
            <h3>No Data Available</h3>
            <p>Click "Generate Assessment" to create a comprehensive team assessment report.</p>
          </div>
        </div>
      </div>
    `;
    
    this.setupInitialEvents();
  }

  setupInitialEvents() {
    // Date picker
    const datePicker = this.container.querySelector("#pulse-date-picker");
    if (datePicker) {
      datePicker.addEventListener("change", (e) => {
        this.selectedDate = e.target.value;
        this.updateDateButtons();
      });
    }

    // Today button
    const todayBtn = this.container.querySelector("#pulse-today-btn");
    if (todayBtn) {
      todayBtn.addEventListener("click", () => {
        this.selectedDate = new Date().toISOString().split("T")[0];
        datePicker.value = this.selectedDate;
        this.updateDateButtons();
      });
    }

    // Yesterday button
    const yesterdayBtn = this.container.querySelector("#pulse-yesterday-btn");
    if (yesterdayBtn) {
      yesterdayBtn.addEventListener("click", () => {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        this.selectedDate = yesterday.toISOString().split("T")[0];
        datePicker.value = this.selectedDate;
        this.updateDateButtons();
      });
    }

    // Debug toggle
    const debugToggle = this.container.querySelector("#pulse-debug-toggle");
    if (debugToggle) {
      debugToggle.addEventListener("change", (e) => {
        this.debugMode = e.target.checked;
      });
    }

    // Filter button
    const filterBtn = this.container.querySelector("#open-filters-btn");
    if (filterBtn) {
      filterBtn.addEventListener("click", () => {
        this.showFilterModal();
      });
    }

    // Reset filters button
    const resetBtn = this.container.querySelector("#reset-filters-btn");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        this.resetAllFilters();
        this.renderInitialState();
      });
    }

    // Default filters button
    const defaultBtn = this.container.querySelector("#default-filters-btn");
    if (defaultBtn) {
      defaultBtn.addEventListener("click", () => {
        this.setDefaultFilters();
        this.renderInitialState();
      });
    }

    // Generate data button
    const generateBtn = this.container.querySelector("#generate-data-btn");
    if (generateBtn) {
      generateBtn.addEventListener("click", () => {
        this.loadData();
      });
    }

    // Generate assessment button
    const assessmentBtn = this.container.querySelector("#generate-assessment-btn");
    if (assessmentBtn) {
      console.log('🔘 Assessment button found, adding event listener');
      console.log('🔍 this context:', this);
      console.log('🔍 this.generateAssessment:', typeof this.generateAssessment);
      assessmentBtn.addEventListener("click", function(e) {
        console.log('🔘 Assessment button clicked!');
        console.log('🔍 this context in click handler:', this);
        console.log('🔍 this.generateAssessment in click handler:', typeof this.generateAssessment);
        e.preventDefault();
        e.stopPropagation();
        this.generateAssessment();
      }.bind(this));
    } else {
      console.log('❌ Assessment button not found');
    }

    // Force real data button
    const forceRealDataBtn = this.container.querySelector("#force-real-data-btn");
    if (forceRealDataBtn) {
      forceRealDataBtn.addEventListener("click", () => {
        this.loadDataForceReal();
      });
    }
  }

  resetAllFilters() {
    // Reset to all enabled
    Object.keys(this.statusFilters).forEach((key) => (this.statusFilters[key] = true));
    Object.keys(this.memberFilters).forEach((key) => (this.memberFilters[key] = true));
    Object.values(this.spaceFilters).forEach((config) => (config.checked = true));
  }

  setDefaultFilters() {
    // Set default configuration
    this.statusFilters = {
      "to do": true,
      planning: true,
      "in progress": true,
      bugs: true,
      "for qa": false,
      "for viewing": false,
      grammar: false,
    };
    Object.keys(this.memberFilters).forEach((key) => (this.memberFilters[key] = true));
    Object.entries(this.spaceFilters).forEach(([spaceId, config]) => {
      config.checked = spaceId === "90132462540"; // Main space only
    });
  }

  updateDateButtons() {
    const isToday = this.selectedDate === new Date().toISOString().split("T")[0];
    const todayBtn = this.container.querySelector("#pulse-today-btn");
    const yesterdayBtn = this.container.querySelector("#pulse-yesterday-btn");

    if (todayBtn && yesterdayBtn) {
      todayBtn.classList.toggle("active", isToday);

      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const isYesterday = this.selectedDate === yesterday.toISOString().split("T")[0];
      yesterdayBtn.classList.toggle("active", isYesterday);
    }
  }

  async loadData() {
    try {
      this.showLoading();

      const params = new URLSearchParams();

      if (this.selectedDate !== new Date().toISOString().split("T")[0]) {
        params.append("date", this.selectedDate);
      }

      if (this.debugMode) {
        params.append("debug", "true");
      }

      // Add cache-busting parameter
      params.append("_t", Date.now());

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

      // Add space filters
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

      const response = await fetch(url);
      const data = await response.json();

      if (data.error && !data.demo_data) {
        throw new Error(data.error);
      }

      this.data = data;
      this.dataLoaded = true;
      this.render();

      // Trigger event to show assessment button
      document.dispatchEvent(new CustomEvent('pulseDataLoaded', { detail: this.data }));

      if (this.debugMode && data.debug_info) {
        console.log("🐛 DEBUG INFO:", data.debug_info);
      }
    } catch (error) {
      console.error("Error loading pulse data:", error);
      this.showError(error.message);
    }
  }

  async loadDataWithRefresh() {
    try {
      this.showLoading();

      const params = new URLSearchParams();

      if (this.selectedDate !== new Date().toISOString().split("T")[0]) {
        params.append("date", this.selectedDate);
      }

      if (this.debugMode) {
        params.append("debug", "true");
      }

      // IMPORTANT: Add force_refresh parameter
      params.append("force_refresh", "true");
      // Add cache-busting parameter
      params.append("_t", Date.now());

      // Add all existing filters
      const activeStatuses = Object.entries(this.statusFilters)
        .filter(([status, isActive]) => isActive)
        .map(([status]) => status);

      activeStatuses.forEach((status) => {
        params.append("status_filter", status);
      });

      const activeMembers = Object.entries(this.memberFilters)
        .filter(([member, isActive]) => isActive)
        .map(([member]) => member);

      activeMembers.forEach((member) => {
        params.append("member_filter", member);
      });

      const activeSpaces = Object.entries(this.spaceFilters)
        .filter(([spaceId, config]) => config.checked)
        .map(([spaceId]) => spaceId);

      activeSpaces.forEach((spaceId) => {
        params.append("space_filter", spaceId);
      });

      const url = `/api/pulse-data?${params.toString()}`;
              console.log("Force refresh - fetching fresh data from:", url);

      const response = await fetch(url);
      const data = await response.json();

      if (data.error && !data.demo_data) {
        throw new Error(data.error);
      }

      this.data = data;
      this.dataLoaded = true;
      this.render();

      // Trigger event to show assessment button
      document.dispatchEvent(new CustomEvent('pulseDataLoaded', { detail: this.data }));

              console.log("Fresh data generated and new JSON file created");

      if (this.debugMode && data.debug_info) {
        console.log("🐛 DEBUG INFO:", data.debug_info);
      }
    } catch (error) {
      console.error("Error loading fresh pulse data:", error);
      this.showError(error.message);
    }
  }

  async loadDataForceReal() {
    try {
      this.showLoading();
      console.log("🚀 Force Real Data - bypassing all restrictions...");

      const params = new URLSearchParams();

      if (this.selectedDate !== new Date().toISOString().split("T")[0]) {
        params.append("date", this.selectedDate);
      }

      if (this.debugMode) {
        params.append("debug", "true");
      }

      // CRITICAL: Force real data generation
      params.append("force_refresh", "true");
      params.append("bypass_working_hours", "true");
      params.append("force_real_data", "true");
      // Add cache-busting parameter
      params.append("_t", Date.now());

      // Add all existing filters
      const activeStatuses = Object.entries(this.statusFilters)
        .filter(([status, isActive]) => isActive)
        .map(([status]) => status);

      activeStatuses.forEach((status) => {
        params.append("status_filter", status);
      });

      const activeMembers = Object.entries(this.memberFilters)
        .filter(([member, isActive]) => isActive)
        .map(([member]) => member);

      activeMembers.forEach((member) => {
        params.append("member_filter", member);
      });

      const activeSpaces = Object.entries(this.spaceFilters)
        .filter(([spaceId, config]) => config.checked)
        .map(([spaceId]) => spaceId);

      activeSpaces.forEach((spaceId) => {
        params.append("space_filter", spaceId);
      });

      const url = `/api/pulse-data${params.toString() ? "?" + params.toString() : ""}`;
      console.log("🚀 Force Real Data - fetching from:", url);

      const response = await fetch(url);
      const data = await response.json();

      if (data.error && !data.demo_data) {
        throw new Error(data.error);
      }

      // Check if we got real data or still demo data
      if (data.data_source === 'demo_data') {
        console.warn("⚠️ Still got demo data despite force real data request");
        this.showWarning("Got demo data - check API connection and permissions");
      } else {
        console.log("✅ Successfully got real data from ClickUp API");
      }

      this.data = data;
      this.dataLoaded = true;
      this.render();

      // Trigger event to show assessment button
      document.dispatchEvent(new CustomEvent('pulseDataLoaded', { detail: this.data }));

      if (this.debugMode && data.debug_info) {
        console.log("🐛 DEBUG INFO:", data.debug_info);
      }
    } catch (error) {
      console.error("Error loading force real data:", error);
      this.showError(error.message);
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
          <div class="error-icon"><span class="material-icons">warning</span></div>
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
            <button onclick="location.reload()" class="retry-btn"><span class="material-icons">refresh</span> Reload Page</button>
            <button id="retry-generate-btn" class="retry-btn"><span class="material-icons">satellite</span> Try Generate Again</button>
          </div>
        </div>
      </div>
    `;

    const retryBtn = this.container.querySelector("#retry-generate-btn");
    if (retryBtn) {
      retryBtn.addEventListener("click", () => {
        this.renderInitialState();
      });
    }
  }

  showWarning(message) {
    // Show warning as a toast notification instead of replacing the entire content
    const warningToast = document.createElement('div');
    warningToast.className = 'warning-toast';
    warningToast.innerHTML = `
      <div class="warning-content">
        <span class="material-icons">warning</span>
        <span class="warning-message">${message}</span>
        <button class="warning-close" onclick="this.parentElement.parentElement.remove()">
          <span class="material-icons">close</span>
        </button>
      </div>
    `;
    
    // Add to the page
    document.body.appendChild(warningToast);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
      if (warningToast.parentElement) {
        warningToast.remove();
      }
    }, 10000);
  }

  render() {
    if (!this.data) {
      this.renderInitialState();
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
      console.log("Controls rendered");

      const overviewStats = this.renderOverviewStats();
      console.log("Overview stats rendered");

      const memberWorkloads = this.renderMemberWorkloads();
      console.log("Member workloads rendered");

      const projectDistribution = this.renderProjectDistribution();
      console.log("Project distribution rendered");

      const loadBalanceInsights = this.renderLoadBalanceInsights();
      console.log("Load balance insights rendered");

      const recommendations = this.renderRecommendations();
      console.log("Recommendations rendered");

      this.container.innerHTML = `
        <div class="pulse-container">
          ${this.renderControls()}
          ${this.renderOverviewStats()}
          <div class="pulse-main-content">
            <div class="pulse-left-column">
              ${this.renderMemberWorkloads()}
              ${this.renderProjectDistribution()}
            </div>
            <div class="pulse-right-column">
              ${this.renderLoadBalanceInsights()}
              ${this.renderRecommendations()}
            </div>
          </div>
          ${this.debugMode && this.data.debug_info ? this.renderDebugInfo() : ""}
        </div>
      `;

      console.log("Main container rendered successfully");
      
      // Trigger event to show assessment button
      document.dispatchEvent(new CustomEvent('pulseDataLoaded', { detail: this.data }));
      
      this.setupControlEvents();
      this.setupClickableWorkloadStats();
    } catch (error) {
      console.error("Error during rendering:", error);
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

    this.setupControlEvents();
    this.setupClickableWorkloadStats();
  }

  // FIXED: Filter modal management with animations
  showFilterModal() {
    // this.hideFilterModal();

    const modalHTML = this.renderFilterModal();
    document.body.insertAdjacentHTML("beforeend", modalHTML);

    this.filterModal = document.getElementById("filter-modal");
    this.filterModal.style.display = "flex";

    // Add animation class after a brief delay
    setTimeout(() => {
      this.filterModal.classList.add("show");
    }, 10);

    this.setupFilterModalEvents();
  }

  hideFilterModal() {
    const existingModal = document.getElementById("filter-modal");
    if (existingModal) {
      existingModal.classList.add("hide");
      setTimeout(() => {
        existingModal.remove();
      }, 300);
    }
    this.filterModal = null;
  }

  setupFilterModalEvents() {
    if (!this.filterModal) return;

    const modal = this.filterModal;

    // Close buttons
    const closeBtn = modal.querySelector("#close-filters-btn");
    const cancelBtn = modal.querySelector("#cancel-filters-btn");

    [closeBtn, cancelBtn].forEach((btn) => {
      if (btn) {
        btn.addEventListener("click", () => this.hideFilterModal());
      }
    });

    // Click outside to close
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        this.hideFilterModal();
      }
    });

    // Escape key to close
    const escapeHandler = (e) => {
      if (e.key === "Escape") {
        this.hideFilterModal();
        document.removeEventListener("keydown", escapeHandler);
      }
    };
    document.addEventListener("keydown", escapeHandler);

    // Filter checkboxes
    const filterCheckboxes = modal.querySelectorAll(".filter-checkbox");
    filterCheckboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", (e) => {
        const filterType = e.target.getAttribute("data-filter-type");
        const filterValue = e.target.getAttribute("data-filter-value");
        const isChecked = e.target.checked;

        if (filterType === "status") {
          this.statusFilters[filterValue] = isChecked;
        } else if (filterType === "member") {
          this.memberFilters[filterValue] = isChecked;
        } else if (filterType === "space") {
          this.spaceFilters[filterValue].checked = isChecked;
        }

        const filterItem = e.target.closest(".filter-item");
        filterItem.classList.toggle("checked", isChecked);

        this.updateFilterCounts(modal);
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
        if (this.dataLoaded) {
          this.loadData();
        }
        this.updateFilterDisplay();
      });
    }
  }

  updateFilterDisplay() {
    // Re-render initial state to update filter summary
    if (!this.dataLoaded) {
      this.renderInitialState();
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
                  <span class="material-icons">target</span>
                  <span>Task Status Filters</span>
                  <span class="filter-count">(${activeStatusCount}/${totalStatusCount} selected)</span>
                </div>
                <div class="filter-section-actions">
                  <button class="filter-action-btn" data-action="select-all" data-type="status">All</button>
                  <button class="filter-action-btn" data-action="default" data-type="status">Default</button>
                  <button class="filter-action-btn" data-action="clear" data-type="status">Clear</button>
                </div>

                  <div class="quick-filter-buttons">
                    <button id="reset-filters-btn" class="control-btn"><span class="material-icons">refresh</span> Reset</button>
                    <button id="default-filters-btn" class="control-btn active">Default</button>
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
                      <span class="filter-label">${status}</span>
                      <span class="filter-badge">${status}</span>
                    </label>
                  `
                  )
                  .join("")}
              </div>
            </div>

            <!-- Member Filters Section -->
            <div class="filter-section">
              <div class="filter-section-header">
                <div class="filter-section-title">
                  <span class="material-icons">group</span>
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
                      <span class="filter-label">${member}</span>
                      <span class="filter-badge">${member}</span>
                    </label>
                  `
                  )
                  .join("")}
              </div>
            </div>

            <!-- Space Filters Section -->
            <div class="filter-section">
              <div class="filter-section-header">
                <div class="filter-section-title">
                  <span class="filter-icon">🏢</span>
                  <span>Space Filters</span>
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
                      <span class="filter-label">${config.name}</span>
                      <span class="filter-badge">${config.name.substring(0, 3)}</span>
                    </label>
                  `
                  )
                  .join("")}
              </div>
            </div>
          </div>

          <div class="filter-modal-footer">
            <div class="filter-info">
              <span><span class="material-icons">search</span> Configure which data to include in your pulse analysis</span>
            </div>
            <div class="filter-modal-actions">
              <button class="filter-cancel-btn" id="cancel-filters-btn">Cancel</button>
              <button class="filter-apply-btn" id="apply-filters-btn">Apply Filters</button>
            </div>
          </div>
        </div>
      </div>
    `;
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
        Object.entries(this.spaceFilters).forEach(([spaceId, config]) => {
          config.checked = spaceId === "90132462540";
        });
      }
    }

    this.updateFilterModalUI(modal);
    this.updateFilterCounts(modal);
  }

  updateFilterModalUI(modal) {
    ["status", "member", "space"].forEach((type) => {
      const checkboxes = modal.querySelectorAll(`[data-filter-type="${type}"]`);
      checkboxes.forEach((checkbox) => {
        const value = checkbox.getAttribute("data-filter-value");
        let isChecked;

        if (type === "space") {
          isChecked = this.spaceFilters[value].checked;
        } else {
          const filters = type === "status" ? this.statusFilters : this.memberFilters;
          isChecked = filters[value];
        }

        checkbox.checked = isChecked;
        checkbox.closest(".filter-item").classList.toggle("checked", isChecked);
      });
    });
  }

  updateFilterCounts(modal) {
    const sections = modal.querySelectorAll(".filter-section");

    sections.forEach((section, index) => {
      const countElement = section.querySelector(".filter-count");
      if (countElement) {
        let activeCount, totalCount;

        if (index === 0) {
          // Status
          activeCount = Object.values(this.statusFilters).filter(Boolean).length;
          totalCount = Object.keys(this.statusFilters).length;
        } else if (index === 1) {
          // Members
          activeCount = Object.values(this.memberFilters).filter(Boolean).length;
          totalCount = Object.keys(this.memberFilters).length;
        } else if (index === 2) {
          // Spaces
          activeCount = Object.values(this.spaceFilters).filter((config) => config.checked).length;
          totalCount = Object.keys(this.spaceFilters).length;
        }

        countElement.textContent = `(${activeCount}/${totalCount} selected)`;
      }
    });
  }

  renderControls() {
    try {
      const isToday = this.selectedDate === new Date().toISOString().split("T")[0];
      const dateObj = new Date(this.selectedDate);
      const isWeekend = dateObj.getDay() === 0 || dateObj.getDay() === 6;
      const isHistorical = this.data.cache_info?.is_historical;

      // try {
      //   const workloads = this.data.member_workloads || {};
              //   console.log("Rendering member workloads:", Object.keys(workloads));

      // if (Object.keys(workloads).length === 0) {
      const activeStatuses = Object.entries(this.statusFilters)
        .filter(([status, isActive]) => isActive)
        .map(([status, isActive]) => status);

      const activeMembers = Object.entries(this.memberFilters)
        .filter(([member, isActive]) => isActive)
        .map(([member, isActive]) => member);

      const activeSpaces = Object.entries(this.spaceFilters)
        .filter(([spaceId, config]) => config.checked)
        .map(([spaceId, config]) => config.name);

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
                            <span></span>
                            <! -- Team Pulse Analytics -->
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
                        <!-- Large Filter Controls -->
                        <div class="filter-controls">
              
              
                          <div class="filter-picker-group">
                            <div class="filter-picker-container">
                              <button id="open-filters-btn" class="filter-picker-btn">
                                <div class="filter-main-info">
                                  <span class="filter-icon">🎛️</span>
                                  <span class="filter-text">Filters</span>
                                </div>
                                <div class="filter-summary">
                                  <div class="filter-summary-line">
                                    <strong>${activeStatusCount}/${totalStatusCount}</strong> statuses: ${activeStatuses
        .slice(0, 3)
        .join(", ")}${activeStatuses.length > 3 ? "..." : ""}
                                  </div>
                                  <div class="filter-summary-line">
                                    <strong>${activeMemberCount}/${totalMemberCount}</strong> members: ${activeMembers
        .slice(0, 4)
        .join(", ")}${activeMembers.length > 4 ? "..." : ""}
                                  </div>
                                  <div class="filter-summary-line">
                                    <strong>${activeSpaceCount}/${totalSpaceCount}</strong> spaces: ${activeSpaces
        .slice(0, 2)
        .join(", ")}${activeSpaces.length > 2 ? "..." : ""}
                                  </div>
                                </div>
                              </button>
                            </div>
                            
                   
                          </div>
                        </div>
                        
                        <div class="debug-controls">
                            <label class="debug-toggle">
                                <input type="checkbox" id="pulse-debug-toggle" ${
                                  this.debugMode ? "checked" : ""
                                }>
                                <span class="toggle-slider"></span>
                                 Debug Mode
                            </label>
                            <div>
                              <button id="pulse-refresh-btn" class="button custom-refresh-btn">
                                <div class="button-outer">
                                  <div class="button-inner">
                                    <span class="material-icons"></span>
                                    <span>New Data</span>
                                  </div>
                                </div>
                              </button>

                              <button id="generate-assessment-btn" class="button custom-refresh-btn">
                                <div class="button-outer">
                                  <div class="button-inner">
                                    <span class="material-icons"></span>
                                    <span>Evaluation</span>
                                  </div>
                                </div>
                              </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
    } catch (error) {
              console.error("Error rendering controls:", error);
      return `<div class="error">Error rendering controls: ${error.message}</div>`;
    }
  }

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
                        <div class="pulse-metric-icon"><span class="material-icons">group</span></div>
                        <div class="pulse-metric-value">${stats.total_members || 0}</div>
                        <div class="pulse-metric-label">Active Members</div>
                    </div>
                    
                    <div class="pulse-metric-card">
                        <div class="pulse-metric-icon"><span class="material-icons">folder</span></div>
                        <div class="pulse-metric-value">${stats.total_projects || 0}</div>
                        <div class="pulse-metric-label">Active Projects</div>
                    </div>
                    
                    <div class="pulse-metric-card">
                        <div class="pulse-metric-icon"><span class="material-icons">check_circle</span></div>
                        <div class="pulse-metric-value">${stats.total_active_tasks || 0}</div>
                        <div class="pulse-metric-label">Active Tasks</div>
                    </div>
                    
                    <div class="pulse-metric-card">
                        <div class="pulse-metric-icon"><span class="material-icons">balance</span></div>
                        <div class="pulse-metric-value">${stats.avg_tasks_per_member || 0}</div>
                        <div class="pulse-metric-label">Avg Tasks/Member</div>
                    </div>
                    
                    <div class="pulse-metric-card team-health-card">
                        <div class="pulse-metric-icon"><span class="material-icons">monitor_heart</span></div>
                        <div class="pulse-metric-value health-score ${healthClass}">${healthScore}</div>
                        <div class="pulse-metric-label">Team Health</div>
                        <div class="health-indicator ${healthClass}" style="width: ${healthScore}%"></div>
                    </div>
                    
                    <div class="pulse-metric-card">
                        <div class="pulse-metric-icon"><span class="material-icons">trending_up</span></div>
                        <div class="pulse-metric-value">${stats.avg_workload_score || 0}</div>
                        <div class="pulse-metric-label">Avg Workload Score</div>
                    </div>
                </div>
            `;
    } catch (error) {
      console.error("Error rendering overview stats:", error);
      return `<div class="error">Error rendering overview stats: ${error.message}</div>`;
    }
  }

  renderMemberWorkloads() {
    try {
      const workloads = this.data.member_workloads || {};
      console.log("Rendering member workloads:", Object.keys(workloads));

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
                                <span class="material-icons">group</span>
                                Member Workloads
                            </h2>
                        </div>
                        <div class="no-workloads">
                            <div style="text-align: center; padding: 40px; color: #64748b;">
                                <div style="font-size: 3rem; margin-bottom: 16px;"><span class="material-icons">analytics</span></div>
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
                                        Try adjusting the filters using the <strong><span class="material-icons">tune</span> Filters</strong> button, or enabling Debug Mode for more info.
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
                            <span class="material-icons">group</span>
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
              console.error("Error rendering member workloads:", error);
      return `<div class="error">Error rendering member workloads: ${error.message}</div>`;
    }
  }

  renderProjectDistribution() {
    try {
      const projects = this.data.project_analytics || {};
              console.log("Rendering project distribution:", Object.keys(projects));

      if (Object.keys(projects).length === 0) {
        return `
          <div class="project-distribution">
            <div class="section-header">
              <h3 class="section-title">
                <span class="material-icons">analytics</span>
                Project Distribution
              </h3>
            </div>
            
            <div class="no-projects">
              <p style="color: #64748b; text-align: center; padding: 20px;">
                <span class="material-icons">assignment</span> No project data available
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
              <span class="material-icons">analytics</span>
              Project Distribution
            </h3>
          </div>
          
          <div class="project-grid">
            ${projectCards}
          </div>
        </div>
      `;
    } catch (error) {
              console.error("Error rendering project distribution:", error);
      return `<div class="error">Error rendering project distribution: ${error.message}</div>`;
    }
  }

  renderLoadBalanceInsights() {
    try {
      const insights = this.data.load_balance_insights || {};
              console.log("Rendering load balance insights:", insights);

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
              <span class="material-icons">balance</span>
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
                <span class="material-icons">analytics</span> No workload comparison available yet
                ${this.debugMode ? "<br><small>Enable debug mode to see why</small>" : ""}
              </p>
            </div>
          `
          }
          
          ${
            insights.overloaded_members && insights.overloaded_members.length > 0
              ? `
               <h4><span class="material-icons">warning</span> Overloaded Members</h4>
            <div class="insight-card highest">
             
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
              <h4><span class="material-icons">lightbulb</span> Transfer Suggestions</h4>
              ${transferSuggestions}
            </div>
          `
              : `
            <div class="no-suggestions">
              <p style="color: #64748b; text-align: center; padding: 16px; font-style: italic;">
                <span class="material-icons">lightbulb</span> No transfer suggestions available
              </p>
            </div>
          `
          }
        </div>
      `;
    } catch (error) {
              console.error("Error rendering load balance insights:", error);
      return `<div class="error">Error rendering load balance insights: ${error.message}</div>`;
    }
  }

  renderRecommendations() {
    try {
      const recommendations = this.data.recommendations || [];
              console.log("Rendering recommendations:", recommendations.length);

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
              <span class="material-icons">lightbulb</span>
              Recommendations
            </h3>
          </div>
          
          ${
            recommendations.length > 0
              ? recommendationItems
              : `
            <div class="no-recommendations">
              <p style="color: #22c55e; text-align: center; padding: 20px;">
                <span class="material-icons">check_circle</span> All good! No immediate actions needed.
                ${this.debugMode ? "<br><small>No workload issues detected</small>" : ""}
              </p>
            </div>
          `
          }
        </div>
      `;
    } catch (error) {
              console.error("Error rendering recommendations:", error);
      return `<div class="error">Error rendering recommendations: ${error.message}</div>`;
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
              console.error("Error rendering debug info:", error);
      return `<div class="error">Error rendering debug info: ${error.message}</div>`;
    }
  }

  setupControlEvents() {
    // STEP 1: Remove existing event listeners by cloning elements
    const elementsToClone = [
      "#pulse-date-picker",
      "#pulse-today-btn",
      "#pulse-yesterday-btn",
      "#pulse-debug-toggle",
      "#pulse-refresh-btn",
      "#open-filters-btn",
      "#reset-filters-btn",
      "#default-filters-btn",
      "#generate-data-btn",
      "#generate-assessment-btn",
    ];

    elementsToClone.forEach((selector) => {
      const element = this.container.querySelector(selector);
      if (element) {
        const newElement = element.cloneNode(true);
        element.parentNode.replaceChild(newElement, element);
      }
    });

    // STEP 2: Add fresh event listeners

    // Date picker
    const datePicker = this.container.querySelector("#pulse-date-picker");
    if (datePicker) {
      datePicker.addEventListener("change", (e) => {
        this.selectedDate = e.target.value;
        this.updateDateButtonStates();
        this.loadData();
      });
    }

    // Today button
    const todayBtn = this.container.querySelector("#pulse-today-btn");
    if (todayBtn) {
      todayBtn.addEventListener("click", () => {
        this.selectedDate = new Date().toISOString().split("T")[0];
        const datePicker = this.container.querySelector("#pulse-date-picker");
        if (datePicker) datePicker.value = this.selectedDate;
        this.updateDateButtonStates();
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
        const datePicker = this.container.querySelector("#pulse-date-picker");
        if (datePicker) datePicker.value = this.selectedDate;
        this.updateDateButtonStates();
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

    // REFRESH BUTTON - This was causing the double API calls!
    const refreshBtn = this.container.querySelector("#pulse-refresh-btn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log("Refresh button clicked - single event");
        this.loadDataWithRefresh();
      });
    }

    // Filter button
    const filterBtn = this.container.querySelector("#open-filters-btn");
    if (filterBtn) {
      filterBtn.addEventListener("click", () => {
        this.showFilterModal();
      });
    }

    // Reset filters button
    const resetBtn = this.container.querySelector("#reset-filters-btn");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        this.resetAllFilters();
        if (this.dataLoaded) {
          this.loadData();
        }
      });
    }

    // Default filters button
    const defaultBtn = this.container.querySelector("#default-filters-btn");
    if (defaultBtn) {
      defaultBtn.addEventListener("click", () => {
        this.setDefaultFilters();
        if (this.dataLoaded) {
          this.loadData();
        }
      });
    }

    // Generate data button
    const generateBtn = this.container.querySelector("#generate-data-btn");
    if (generateBtn) {
      generateBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log("Generate button clicked - single event");
        this.loadData();
      });
    }

    // Generate assessment button
    const assessmentBtn = this.container.querySelector("#generate-assessment-btn");
    if (assessmentBtn) {
      console.log('🔘 Assessment button found in setupControlEvents, adding event listener');
      console.log('🔍 this context:', this);
      console.log('🔍 this.generateAssessment:', typeof this.generateAssessment);
      assessmentBtn.addEventListener("click", function(e) {
        console.log('🔘 Assessment button clicked!');
        console.log('🔍 this context in click handler:', this);
        console.log('🔍 this.generateAssessment in click handler:', typeof this.generateAssessment);
        e.preventDefault();
        e.stopPropagation();
        this.generateAssessment();
      }.bind(this));
    } else {
      console.log('❌ Assessment button not found in setupControlEvents');
    }
  }

  setupClickableWorkloadStats() {
    // First, remove any existing event listeners to prevent duplicates
    this.container
      .querySelectorAll('.workload-stat[data-clickable="true"]')
      .forEach((statElement) => {
        // Clone the element to remove all event listeners
        const newElement = statElement.cloneNode(true);
        statElement.parentNode.replaceChild(newElement, statElement);
      });

    // Then add fresh event listeners
    this.container
      .querySelectorAll('.workload-stat[data-clickable="true"]')
      .forEach((statElement) => {
        statElement.addEventListener("click", (e) => {
          e.preventDefault();
          e.stopPropagation();

          const username = statElement.getAttribute("data-username");
          const taskType = statElement.getAttribute("data-task-type");
          this.showTaskDetailsModal(username, taskType);
        });
      });
  }

  showTaskDetailsModal(username, taskType) {
    // CRITICAL: Close any existing modal first
    this.closeTaskDetailsModal();

    const workload = this.data.member_workloads[username];
    if (!workload) return;

    // ... rest of your existing modal code stays the same ...
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
                          <h4 class="task-item-title">${task.name}</h4>
                          <div class="task-item-badges">
                            ${
                              task.priority
                                ? `<span class="task-priority-badge ${task.priority.priority}">${task.priority.priority}</span>`
                                : ""
                            }
                            <span class="task-status-badge">${task.status}</span>
                          </div>
                        </div>
                        <div class="task-item-details">
                          ${
                            task.due_date
                              ? `<p><span class="material-icons">event</span> Due: ${new Date(
                                  parseInt(task.due_date)
                                ).toLocaleDateString()}</p>`
                              : ""
                          }
                          ${
                            task.url
                              ? `<a href="${task.url}" target="_blank" class="clickup-button">
                                  <span class="material-icons">link</span>
                                  Open in ClickUp
                                </a>`
                              : ""
                          }
                        </div>
                        
                        <!-- Accordion for Task Details -->
                        <div class="task-accordion">
                          <div class="task-accordion-header" onclick="toggleTaskAccordion(this)">
                            <h5>
                              <span class="material-icons">info</span>
                              Task Details
                            </h5>
                            <span class="material-icons">expand_more</span>
                          </div>
                          <div class="task-accordion-content">
                            <div class="task-accordion-body">
                              <div class="task-details-loading">
                                <span class="material-icons">sync</span>
                                Loading task details...
                              </div>
                            </div>
                          </div>
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

    // Setup close events
    const closeBtn = modal.querySelector(".task-details-close");
    closeBtn.addEventListener("click", () => this.closeTaskDetailsModal());

    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        this.closeTaskDetailsModal();
      }
    });

    // Keyboard close
    this.modalKeyHandler = (e) => {
      if (e.key === "Escape") {
        this.closeTaskDetailsModal();
      }
    };
    document.addEventListener("keydown", this.modalKeyHandler);
  }

  closeTaskDetailsModal() {
    if (this.currentModal) {
      document.body.removeChild(this.currentModal);
      this.currentModal = null;
    }

    if (this.modalKeyHandler) {
      document.removeEventListener("keydown", this.modalKeyHandler);
      this.modalKeyHandler = null;
    }
  }

  handleModalKeydown(e) {
    if (e.key === "Escape" && this.currentModal) {
      this.closeTaskDetailsModal();
    }
  }

  refresh() {
    // Don't auto-load data, just refresh the current state
    if (this.dataLoaded) {
      this.loadData();
    } else {
      this.renderInitialState();
    }
  }
}

// Global functions for accordion functionality
function toggleTaskAccordion(header) {
  const content = header.nextElementSibling;
  const icon = header.querySelector('.material-icons:last-child');
  
  // Toggle active state
  header.classList.toggle('active');
  content.classList.toggle('active');
  
  // If opening, load task details
  if (content.classList.contains('active')) {
    loadTaskDetails(content, header.closest('.task-item-modal'));
  }
}

function loadTaskDetails(contentElement, taskItem) {
  const taskName = taskItem.querySelector('.task-item-title').textContent;
  const taskUrl = taskItem.querySelector('.clickup-button')?.href;
  
  // Extract task ID from URL
  const taskId = taskUrl ? taskUrl.split('/').pop() : null;
  
  if (!taskId) {
    contentElement.querySelector('.task-accordion-body').innerHTML = `
      <div class="task-details-loading">
        <span class="material-icons">error</span>
        Could not extract task ID from URL
      </div>
    `;
    return;
  }
  
  // Show loading state
  contentElement.querySelector('.task-accordion-body').innerHTML = `
    <div class="task-details-loading">
      <span class="material-icons">sync</span>
      Loading task details...
    </div>
  `;
  
  // Fetch real task details from API
  fetch(`/api/task-details/${taskId}`)
    .then(response => response.json())
    .then(data => {
      if (data.success && data.task) {
        const taskDetails = generateRealTaskDetails(data.task);
        contentElement.querySelector('.task-accordion-body').innerHTML = taskDetails;
      } else {
        contentElement.querySelector('.task-accordion-body').innerHTML = `
          <div class="task-details-loading">
            <span class="material-icons">error</span>
            ${data.error || 'Failed to load task details'}
          </div>
        `;
      }
    })
    .catch(error => {
      console.error('Error fetching task details:', error);
      contentElement.querySelector('.task-accordion-body').innerHTML = `
        <div class="task-details-loading">
          <span class="material-icons">error</span>
          Failed to load task details. Please try again.
        </div>
      `;
    });
}

function generateRealTaskDetails(task) {
  // Format dates
  const formatDate = (timestamp) => {
    if (!timestamp) return 'Not set';
    return new Date(parseInt(timestamp)).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // Format time estimate
  const formatTimeEstimate = (estimate) => {
    if (!estimate) return 'Not set';
    const hours = Math.floor(estimate / 3600000);
    const minutes = Math.floor((estimate % 3600000) / 60000);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };
  
  // Format assignees
  const formatAssignees = (assignees) => {
    if (!assignees || assignees.length === 0) return 'Unassigned';
    return assignees.map(a => a.username || a.name || 'Unknown').join(', ');
  };
  
  // Format priority
  const formatPriority = (priority) => {
    if (!priority || !priority.priority) return 'Not set';
    return priority.priority.charAt(0).toUpperCase() + priority.priority.slice(1);
  };
  
  // Format tags
  const formatTags = (tags) => {
    if (!tags || tags.length === 0) return 'No tags';
    return tags.map(tag => tag.name || tag).join(', ');
  };
  
  return `
    <div class="task-details-grid">
      <div class="task-detail-item">
        <span class="material-icons">assignment</span>
        <span class="task-detail-label">Task ID:</span>
        <span class="task-detail-value">${task.id || 'Unknown'}</span>
      </div>
      <div class="task-detail-item">
        <span class="material-icons">person</span>
        <span class="task-detail-label">Assignee:</span>
        <span class="task-detail-value">${formatAssignees(task.assignees)}</span>
      </div>
      <div class="task-detail-item">
        <span class="material-icons">folder</span>
        <span class="task-detail-label">Project:</span>
        <span class="task-detail-value">${task.project_name || 'Unknown'}</span>
      </div>
      <div class="task-detail-item">
        <span class="material-icons">schedule</span>
        <span class="task-detail-label">Created:</span>
        <span class="task-detail-value">${formatDate(task.date_created)}</span>
      </div>
      <div class="task-detail-item">
        <span class="material-icons">timer</span>
        <span class="task-detail-label">Time Estimate:</span>
        <span class="task-detail-value">${formatTimeEstimate(task.time_estimate)}</span>
      </div>
      <div class="task-detail-item">
        <span class="material-icons">trending_up</span>
        <span class="task-detail-label">Priority:</span>
        <span class="task-detail-value">${formatPriority(task.priority)}</span>
      </div>
      <div class="task-detail-item">
        <span class="material-icons">label</span>
        <span class="task-detail-label">Tags:</span>
        <span class="task-detail-value">${formatTags(task.tags)}</span>
      </div>
      <div class="task-detail-item">
        <span class="material-icons">update</span>
        <span class="task-detail-label">Updated:</span>
        <span class="task-detail-value">${formatDate(task.date_updated)}</span>
      </div>
    </div>
    
    ${task.description ? `
      <div class="task-description">
        <h6>Description</h6>
        <p>${task.description}</p>
      </div>
    ` : ''}
    
    ${task.text_content ? `
      <div class="task-description">
        <h6>Content</h6>
        <p>${task.text_content}</p>
      </div>
    ` : ''}
    
    ${task.comments && task.comments.length > 0 ? `
      <div class="task-comments">
        <h6>Recent Comments</h6>
        ${task.comments.map(comment => `
          <div class="task-comment">
            <div class="task-comment-header">
              <span class="task-comment-author">${comment.user}</span>
              <span class="task-comment-date">${formatDate(comment.date_created)}</span>
            </div>
            <div class="task-comment-text">${comment.text}</div>
          </div>
        `).join('')}
      </div>
    ` : ''}
  `;
}

function getRandomAssignee() {
  const assignees = ['Jan', 'Arif', 'Wiktor', 'Kendra', 'Calum', 'Tricia', 'Rick'];
  return assignees[Math.floor(Math.random() * assignees.length)];
}

function getRandomProject() {
  const projects = ['Web Design', 'Mobile App', 'SEO Optimization', 'Content Creation', 'UI/UX Design'];
  return projects[Math.floor(Math.random() * projects.length)];
}

function getRandomDate() {
  const dates = ['2025-09-01', '2025-08-30', '2025-08-29', '2025-08-28'];
  return dates[Math.floor(Math.random() * dates.length)];
}

function getRandomTimeEstimate() {
  const estimates = ['2 hours', '4 hours', '1 day', '3 days', '1 week'];
  return estimates[Math.floor(Math.random() * estimates.length)];
}

function getRandomProgress() {
  const progress = ['25%', '50%', '75%', '90%', 'Completed'];
  return progress[Math.floor(Math.random() * progress.length)];
}

function getTaskDescription(taskName) {
  const descriptions = [
    `This task involves ${taskName.toLowerCase()} implementation with focus on user experience and performance optimization.`,
    `Complete ${taskName.toLowerCase()} with attention to detail and following best practices for quality assurance.`,
    `Implement ${taskName.toLowerCase()} functionality while ensuring compatibility across different platforms and devices.`,
    `Develop ${taskName.toLowerCase()} features with emphasis on scalability and maintainability of the codebase.`
  ];
  return descriptions[Math.floor(Math.random() * descriptions.length)];
}

function generateTaskComments() {
  const comments = [
    {
      author: 'Jan',
      date: '2 hours ago',
      text: 'Started working on this task. Will update progress soon.'
    },
    {
      author: 'Arif',
      date: '1 day ago',
      text: 'Reviewed the requirements. Everything looks good to proceed.'
    },
    {
      author: 'Wiktor',
      date: '2 days ago',
      text: 'Added initial setup and configuration files.'
    }
  ];
  
  return comments.map(comment => `
    <div class="task-comment">
      <div class="task-comment-header">
        <span class="task-comment-author">${comment.author}</span>
        <span class="task-comment-date">${comment.date}</span>
      </div>
      <div class="task-comment-text">${comment.text}</div>
    </div>
  `).join('');
}

console.log('📜 PulseAnalytics class defined successfully!');

// Make it globally accessible for testing
window.PulseAnalytics = PulseAnalytics;
