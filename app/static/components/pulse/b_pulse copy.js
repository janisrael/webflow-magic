/**
 * Enhanced Pulse Analytics Component with Status Filters
 * Adds task status filtering functionality
 */

class PulseAnalytics {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.data = null;
    this.selectedDate = new Date().toISOString().split("T")[0];
    this.debugMode = false;
    this.currentModal = null;

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

    this.init();
  }

  init() {
    this.render();
    // this.loadData();
  }

  async loadData() {
    try {
      this.showLoading();

      // Build URL with parameters including status filters
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

      const url = `/api/pulse-data${params.toString() ? "?" + params.toString() : ""}`;
      console.log("📡 Fetching pulse data from:", url);
      console.log("🔍 Active status filters:", activeStatuses);

      const response = await fetch(url);
      const data = await response.json();

      if (data.error && !data.demo_data) {
        throw new Error(data.error);
      }

      this.data = data;
      this.render();

      if (this.debugMode && data.debug_info) {
        console.log("🐛 DEBUG INFO:", data.debug_info);
      }
    } catch (error) {
      console.error("Error loading pulse data:", error);
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
      return;
    }

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

    this.setupControlEvents();
    this.setupClickableWorkloadStats();
  }

  renderControls() {
    const isToday = this.selectedDate === new Date().toISOString().split("T")[0];
    const dateObj = new Date(this.selectedDate);
    const isWeekend = dateObj.getDay() === 0 || dateObj.getDay() === 6;
    const isHistorical = this.data.cache_info?.is_historical;
    const isBackdate = this.selectedDate < new Date().toISOString().split("T")[0];

    // Count active filters
    const activeFiltersCount = Object.values(this.statusFilters).filter(Boolean).length;
    const totalFiltersCount = Object.keys(this.statusFilters).length;

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
                                ? `Historical workload data from ${this.data.cache_info.source_file} • Generated: ${this.data.cache_info.generated_date}`
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
                            <label for="pulse-date-picker">
                                📅 Analysis Date
                            </label>
                            
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
                                    }">
                                        Today
                                    </button>
                                    <button id="pulse-yesterday-btn" class="control-btn">
                                        Yesterday
                                    </button>
                                </div>
                            </div>
                            
                            <div class="date-status-notices">
                                ${
                                  isWeekend
                                    ? `
                                    <div class="weekend-notice">
                                        Weekend selected - limited data expected
                                    </div>
                                `
                                    : ""
                                }
                            </div>
                        </div>
                        
                        <div class="debug-controls">
                            <label class="debug-toggle">
                                <input type="checkbox" 
                                       id="pulse-debug-toggle" 
                                       ${this.debugMode ? "checked" : ""}>
                                <span class="toggle-slider"></span>
                                 Debug Mode
                            </label>
                            <button id="pulse-refresh-btn" class="control-btn">
                                 Load Data
                            </button>
                        </div>
                    </div>
                    
                    <!-- NEW: Status Filters Section -->
                    <div class="status-filters-section">
                        <div class="status-filters-header">
                            <div class="status-filters-title">
                                <span>🎯</span>
                                Task Status Filters
                                <span class="filter-count">(${activeFiltersCount}/${totalFiltersCount} selected)</span>
                            </div>
                            <div class="status-filters-actions">
                                <button id="select-all-statuses" class="filter-action-btn">Select All</button>
                                <button id="select-default-statuses" class="filter-action-btn">Default</button>
                                <button id="clear-all-statuses" class="filter-action-btn">Clear All</button>
                            </div>
                        </div>
                        
                        <div class="status-filters-grid">
                            ${Object.entries(this.statusFilters)
                              .map(
                                ([status, isChecked]) => `
                                <label class="status-filter-item ${isChecked ? "checked" : ""}">
                                    <input type="checkbox" 
                                           class="status-filter-checkbox"
                                           data-status="${status}"
                                           ${isChecked ? "checked" : ""}>
                                    <span class="status-filter-checkmark"></span>
                                    <span class="status-filter-label">${this.formatStatusName(
                                      status
                                    )}</span>
                                    <span class="status-filter-badge">${status}</span>
                                </label>
                            `
                              )
                              .join("")}
                        </div>
                        
                        <div class="status-filters-info">
                            <div class="filter-info-item">
                                <span class="filter-info-icon">ℹ️</span>
                                <span>Only tasks with selected statuses will be included in workload calculations</span>
                            </div>
                            <div class="filter-info-item">
                                <span class="filter-info-icon">🔄</span>
                                <span>Click "Refresh" after changing filters to update data</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
  }

  formatStatusName(status) {
    // Convert status to display-friendly format
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

    // NEW: Status filter checkboxes
    const statusCheckboxes = this.container.querySelectorAll(".status-filter-checkbox");
    statusCheckboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", (e) => {
        const status = e.target.getAttribute("data-status");
        this.statusFilters[status] = e.target.checked;

        // Update the visual state of the filter item
        const filterItem = e.target.closest(".status-filter-item");
        if (e.target.checked) {
          filterItem.classList.add("checked");
        } else {
          filterItem.classList.remove("checked");
        }

        // Update filter count
        this.updateFilterCount();

        console.log(`Status filter "${status}" ${e.target.checked ? "enabled" : "disabled"}`);
      });
    });

    // NEW: Filter action buttons
    const selectAllBtn = this.container.querySelector("#select-all-statuses");
    if (selectAllBtn) {
      selectAllBtn.addEventListener("click", () => {
        this.setAllStatusFilters(true);
      });
    }

    const selectDefaultBtn = this.container.querySelector("#select-default-statuses");
    if (selectDefaultBtn) {
      selectDefaultBtn.addEventListener("click", () => {
        this.setDefaultStatusFilters();
      });
    }

    const clearAllBtn = this.container.querySelector("#clear-all-statuses");
    if (clearAllBtn) {
      clearAllBtn.addEventListener("click", () => {
        this.setAllStatusFilters(false);
      });
    }
  }

  setAllStatusFilters(checked) {
    Object.keys(this.statusFilters).forEach((status) => {
      this.statusFilters[status] = checked;
    });
    this.updateFilterUI();
    this.updateFilterCount();
  }

  setDefaultStatusFilters() {
    // Reset to default: to do, planning, in progress, bugs
    this.statusFilters = {
      "to do": true,
      planning: true,
      "in progress": true,
      bugs: true,
      "for qa": false,
      "for viewing": false,
      grammar: false,
    };
    this.updateFilterUI();
    this.updateFilterCount();
  }

  updateFilterUI() {
    const statusCheckboxes = this.container.querySelectorAll(".status-filter-checkbox");
    statusCheckboxes.forEach((checkbox) => {
      const status = checkbox.getAttribute("data-status");
      checkbox.checked = this.statusFilters[status];

      const filterItem = checkbox.closest(".status-filter-item");
      if (this.statusFilters[status]) {
        filterItem.classList.add("checked");
      } else {
        filterItem.classList.remove("checked");
      }
    });
  }

  updateFilterCount() {
    const activeFiltersCount = Object.values(this.statusFilters).filter(Boolean).length;
    const totalFiltersCount = Object.keys(this.statusFilters).length;

    const filterCountElement = this.container.querySelector(".filter-count");
    if (filterCountElement) {
      filterCountElement.textContent = `(${activeFiltersCount}/${totalFiltersCount} selected)`;
    }
  }

  // Setup click events for workload stats
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

  // Show task details modal
  showTaskDetailsModal(username, taskType) {
    const workload = this.data.member_workloads[username];
    if (!workload) return;

    // Filter tasks based on type
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

    // Create modal
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
                            ? `
                          <span class="task-priority-badge task-priority-${task.priority.priority}">
                            ${task.priority.priority.toUpperCase()}
                          </span>
                        `
                            : ""
                        }
                        <span class="task-status-badge">${task.status}</span>
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
                        task.list_id
                          ? `
                        <p>🆔 List ID: ${task.list_id}</p>
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

    // Add modal to body
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

  // Keep all other render methods the same...
  renderOverviewStats() {
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
                    
                    <div class="pulse-metric-card" >
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
  }

  renderMemberWorkloads() {
    const workloads = this.data.member_workloads || {};

    if (Object.keys(workloads).length === 0) {
      const activeStatuses = Object.entries(this.statusFilters)
        .filter(([status, isActive]) => isActive)
        .map(([status, isActive]) => status);

      return `
                    <div class="workload-section">
                        <div class="section-header">
                            <h2 class="section-title">
                                <span></span>
                                Member Workloads
                            </h2>
                        </div>
                        <div class="no-workloads">
                            <div style="text-align: center; padding: 40px; color: #64748b;">
                                <div style="font-size: 3rem; margin-bottom: 16px;">📊</div>
                                <h3>No Workload Data Available</h3>
                                <p>This could be because:</p>
                                <ul style="text-align: left; max-width: 400px; margin: 16px auto;">
                                    <li>• It's a weekend day (${new Date(
                                      this.selectedDate
                                    ).toLocaleDateString("en-US", { weekday: "long" })})</li>
                                    <li>• No team members have tasks with selected statuses</li>
                                    <li>• Selected status filters: ${activeStatuses.join(", ")}</li>
                                    <li>• API configuration issue</li>
                                </ul>
                                <p style="margin-top: 16px;">
                                    Try adjusting the status filters or enabling Debug Mode for more info.
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
        const projects = workload.projects || [];
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
                            <span></span>
                            Member Workloads
                            <span class="section-subtitle">Click on numbers to view task details</span>
                        </h2>
                    </div>
                    <div class="workload-grid">
                        ${memberCards}
                    </div>
                </div>
            `;
  }

  // Keep other render methods the same (renderLoadBalanceInsights, renderRecommendations, renderProjectDistribution, renderDebugInfo)
  // Replace the placeholder render methods with these complete implementations:

  renderLoadBalanceInsights() {
    const insights = this.data.load_balance_insights || {};

    const highestWorkload = insights.highest_workload;
    const lowestWorkload = insights.lowest_workload;

    const transferSuggestions = (insights.transfer_suggestions || [])
      .map(
        (suggestion) => `
          <div class="transfer-suggestion">
            <div class="transfer-header">
              <span class="transfer-members">
                ${suggestion.from_member} 
                <span class="transfer-arrow">→</span> 
                ${suggestion.to_member}
              </span>
            </div>
            <div class="transfer-task">
              <strong>Task:</strong> ${suggestion.task?.name || "Unknown Task"}
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
            <span></span>
            Load Balance Insights
          </h3>
        </div>
        
        ${
          highestWorkload && lowestWorkload
            ? `
            <div class="insight-comparison">
              <div class="insight-card highest">
                <div class="insight-label">Highest Workload</div>
                <div class="insight-member">${highestWorkload.username}</div>
                <div class="insight-score ${highestWorkload.status}">
                  Score: ${highestWorkload.score}
                </div>
              </div>
              
              <div class="insight-card lowest">
                <div class="insight-label">Lowest Workload</div>
                <div class="insight-member">${lowestWorkload.username}</div>
                <div class="insight-score ${lowestWorkload.status}">
                  Score: ${lowestWorkload.score}
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
              <h3 class="section-header"><span>Overloaded Members</span></h3>
              <div class="overloaded-alert-cotainer">
              <ul>
                ${insights.overloaded_members
                  .map(
                    (member) =>
                      `<li>${member.username} - ${
                        member.workload?.active_tasks || 0
                      } tasks, score: ${member.workload?.workload_score || 0}</li>`
                  )
                  .join("")}
              </ul>
              </div>
            </div>
          `
            : ""
        }
        
        ${
          transferSuggestions
            ? `
            <div class="transfer-suggestions">
              <h3 class="section-header"><span>Transfer Suggestions</span></h3>
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
  }

  renderRecommendations() {
    const recommendations = this.data.recommendations || [];

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
            <span></span>
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
  }

  renderProjectDistribution() {
    const projects = this.data.project_analytics || {};

    if (Object.keys(projects).length === 0) {
      return `
        <div class="project-distribution">
          <div class="section-header">
            <h3 class="section-title">
              <span></span>
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
          if (project.due_date) {
            dueDate = new Date(project.due_date);
            daysUntilDue = (dueDate - new Date()) / (1000 * 60 * 60 * 24);
            isDueSoon = daysUntilDue !== null && daysUntilDue <= 7;
          }
        } catch {
          // Handle invalid date format
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
            <span></span>
            Project Distribution
          </h3>
        </div>
        
        <div class="project-grid">
          ${projectCards}
        </div>
      </div>
    `;
  }

  renderDebugInfo() {
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
            <strong>Total Team Members:</strong> ${this.data.debug_info.total_team_members || "N/A"}
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
                <strong>Cache Source:</strong> ${this.data.cache_info.source_file}
              </div>
              <div class="debug-row">
                <strong>Generated Date:</strong> ${this.data.cache_info.generated_date}
              </div>
            `
              : ""
          }
          <div class="debug-row">
            <strong>Last Updated:</strong> ${new Date(this.data.last_updated).toLocaleString()}
          </div>
          ${
            this.data.status_filters
              ? `
              <div class="debug-row">
                <strong>Status Filters Applied:</strong> ${this.data.status_filters.join(", ")}
              </div>
            `
              : ""
          }
        </div>
      </div>
    `;
  }

  refresh() {
    this.loadData();
  }
}
