/**
 * ClickUp Analytics Widget Component
 * Manages team productivity tracking and analytics
 */

class ClickUpAnalytics {
  constructor(containerId) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    this.currentTimeFilter = "full-day";
    this.refreshInterval = null;

    // Sample analytics data - replace with actual ClickUp API data
    this.analyticsData = {
      teamMembers: [
        {
          id: 1,
          name: "Jan",
          email: "janisatssm@gmail.com",
          status: "active",
          todayHours: 6.5,
          activeTasks: 3,
          completedTasks: 5,
          productivity: 85,
          activityBlocks: [
            { start: 9, duration: 2, type: "focused" },
            { start: 11, duration: 0.5, type: "break" },
            { start: 11.5, duration: 1.5, type: "meeting" },
            { start: 13, duration: 1, type: "break" },
            { start: 14, duration: 3, type: "active" },
            { start: 17, duration: 0.5, type: "meeting" },
          ],
        },
        {
          id: 2,
          name: "Tricia Kennedy",
          email: "triciais@sourceselect.ca",
          status: "active",
          todayHours: 7.2,
          activeTasks: 2,
          completedTasks: 4,
          productivity: 92,
          activityBlocks: [
            { start: 8.5, duration: 2.5, type: "active" },
            { start: 11, duration: 0.5, type: "break" },
            { start: 11.5, duration: 2, type: "focused" },
            { start: 13.5, duration: 1, type: "break" },
            { start: 14.5, duration: 2.5, type: "active" },
          ],
        },
        {
          id: 3,
          name: "Arif",
          email: "arifis@sourceselect.ca",
          status: "offline",
          todayHours: 0,
          activeTasks: 0,
          completedTasks: 0,
          productivity: 0,
          activityBlocks: [],
        },
      ],
      totalExpectedHours: 7.5,
      insights: {
        averageProductivity: 59,
        totalActiveHours: 13.7,
        totalDowntime: 3.8,
        mostProductiveTime: "2:00 PM - 4:00 PM",
        productivityTrend: "up",
      },
    };

    this.init();
  }

  init() {
    this.render();
    this.setupEventListeners();
    this.startRealTimeUpdates();
  }

  render() {
    this.container.innerHTML = this.getTemplate();
    this.renderMetrics();
    this.renderTeamMembers();
    this.renderTimeline();
    this.renderInsights();
  }

  getTemplate() {
    return `
              <div class="clickup-analytics-widget">
                  <!-- Metrics Grid -->
                  <div class="metrics-grid" id="analyticsMetrics">
                      <!-- Metrics will be populated by renderMetrics() -->
                  </div>
  
                  <!-- Team Timeline Section -->
                  <div class="timeline-section">
                      <div class="timeline-header">
                          <h3 class="timeline-title"> Task-Level Team Timeline</h3>
                          <div class="timeline-date" id="timelineDate">Friday, Aug 8, 2025</div>
                          <div class="timeline-controls">
                              <button class="time-filter" data-filter="morning">🌅 Morning</button>
                              <button class="time-filter" data-filter="afternoon">🌞 Afternoon</button>
                              <button class="time-filter active" data-filter="full-day">📅 Full Day</button>
                          </div>
                      </div>
  
                      <!-- Team Members Grid -->
                      <div class="team-members-grid" id="teamMembersGrid">
                          <!-- Team members will be populated by renderTeamMembers() -->
                      </div>
  
                      <!-- Activity Legend -->
                      <div class="activity-legend">
                          <div class="legend-item">
                              <div class="legend-color legend-active"></div>
                              <span>Active Work</span>
                          </div>
                          <div class="legend-item">
                              <div class="legend-color legend-focused"></div>
                              <span>Deep Focus</span>
                          </div>
                          <div class="legend-item">
                              <div class="legend-color legend-meeting"></div>
                              <span>Meetings</span>
                          </div>
                          <div class="legend-item">
                              <div class="legend-color legend-break"></div>
                              <span>Breaks</span>
                          </div>
                          <div class="legend-item">
                              <div class="legend-color legend-inactive"></div>
                              <span>Inactive</span>
                          </div>
                      </div>
                  </div>
  
                  <!-- Productivity Insights -->
                  <div class="productivity-insights" id="productivityInsights">
                      <!-- Insights will be populated by renderInsights() -->
                  </div>
              </div>
          `;
  }

  setupEventListeners() {
    // Time filter buttons
    const timeFilters = this.container.querySelectorAll(".time-filter");
    timeFilters.forEach((filter) => {
      filter.addEventListener("click", () => {
        timeFilters.forEach((f) => f.classList.remove("active"));
        filter.classList.add("active");

        this.currentTimeFilter = filter.dataset.filter;
        this.updateTimelineView();
      });
    });
  }

  renderMetrics() {
    const metricsContainer = this.container.querySelector("#analyticsMetrics");
    const data = this.analyticsData;

    const activeMembers = data.teamMembers.filter((member) => member.status === "active").length;
    const totalActiveHours = data.insights.totalActiveHours;
    const totalDowntime = data.insights.totalDowntime;
    const activeTasks = data.teamMembers.reduce((sum, member) => sum + member.activeTasks, 0);
    const avgProductivity = data.insights.averageProductivity;

    metricsContainer.innerHTML = `
              <div class="metric-card">
                  <div class="metric-icon">👥</div>
                  <div class="metric-label">Team Members</div>
                  <div class="metric-value">${activeMembers}</div>
                  <div class="metric-subtitle">Currently being tracked</div>
              </div>
              <div class="metric-card">
                  <div class="metric-icon">⏰</div>
                  <div class="metric-label">Active Hours</div>
                  <div class="metric-value">${totalActiveHours}h</div>
                  <div class="metric-subtitle">of ${data.totalExpectedHours}h per member expected</div>
              </div>
              <div class="metric-card">
                  <div class="metric-icon">⚠️</div>
                  <div class="metric-label">Downtime</div>
                  <div class="metric-value">${totalDowntime}h</div>
                  <div class="metric-subtitle">Total inactive periods</div>
              </div>
              <div class="metric-card">
                  <div class="metric-icon">📋</div>
                  <div class="metric-label">Active Tasks</div>
                  <div class="metric-value">${activeTasks}</div>
                  <div class="metric-subtitle">Currently in progress</div>
              </div>
              <div class="metric-card">
                  <div class="metric-icon">⚡</div>
                  <div class="metric-label">Efficiency</div>
                  <div class="metric-value">${avgProductivity}%</div>
                  <div class="metric-subtitle">Active vs total working time</div>
              </div>
          `;
  }

  renderTeamMembers() {
    const membersContainer = this.container.querySelector("#teamMembersGrid");
    const members = this.analyticsData.teamMembers;

    if (members.length === 0) {
      membersContainer.innerHTML = this.getEmptyState();
      return;
    }

    membersContainer.innerHTML = members.map((member) => this.createMemberCard(member)).join("");
  }

  createMemberCard(member) {
    const initials = member.name
      .split(" ")
      .map((n) => n.charAt(0))
      .join("")
      .slice(0, 2);
    const statusClass = member.status === "active" ? "" : "status-offline";
    const statusText = member.status === "active" ? "Active" : "Offline";

    return `
              <div class="member-card">
                  <div class="member-header">
                      <div class="member-avatar">${initials}</div>
                      <div class="member-info">
                          <div class="member-name">${member.name}</div>
                          <div class="member-status ${statusClass}">
                              <div class="status-indicator"></div>
                              ${statusText}
                          </div>
                      </div>
                  </div>
                  
                  <div class="member-stats">
                      <div class="member-stat">
                          <div class="stat-value">${member.todayHours}h</div>
                          <div class="stat-label">Today</div>
                      </div>
                      <div class="member-stat">
                          <div class="stat-value">${member.activeTasks}</div>
                          <div class="stat-label">Active</div>
                      </div>
                      <div class="member-stat">
                          <div class="stat-value">${member.completedTasks}</div>
                          <div class="stat-label">Done</div>
                      </div>
                  </div>
  
                  ${this.renderMemberTimeline(member)}
              </div>
          `;
  }

  renderMemberTimeline(member) {
    if (member.activityBlocks.length === 0) {
      return `
                  <div class="member-timeline">
                      <div class="timeline-bar timeline-inactive" style="width: 100%; left: 0;"></div>
                  </div>
              `;
    }

    const workdayStart = 8; // 8 AM
    const workdayEnd = 18; // 6 PM
    const workdayDuration = workdayEnd - workdayStart; // 10 hours

    const timelineHtml = member.activityBlocks
      .map((block) => {
        const startPercent = ((block.start - workdayStart) / workdayDuration) * 100;
        const widthPercent = (block.duration / workdayDuration) * 100;

        return `
                  <div class="time-block block-${block.type}" 
                       style="left: ${startPercent}%; width: ${widthPercent}%;"
                       title="${this.getBlockTitle(block)}">
                  </div>
              `;
      })
      .join("");

    return `
              <div class="activity-timeline">
                  <div class="timeline-hours">
                      <span>8 AM</span>
                      <span>12 PM</span>
                      <span>6 PM</span>
                  </div>
                  <div class="timeline-container">
                      ${timelineHtml}
                  </div>
              </div>
          `;
  }

  getBlockTitle(block) {
    const startTime = this.formatTime(block.start);
    const endTime = this.formatTime(block.start + block.duration);
    const typeLabel =
      {
        active: "Active Work",
        focused: "Deep Focus",
        meeting: "Meeting",
        break: "Break",
      }[block.type] || "Activity";

    return `${typeLabel}: ${startTime} - ${endTime}`;
  }

  formatTime(hour) {
    const h = Math.floor(hour);
    const m = Math.round((hour - h) * 60);
    const period = h >= 12 ? "PM" : "AM";
    const displayHour = h > 12 ? h - 12 : h === 0 ? 12 : h;

    return `${displayHour}:${m.toString().padStart(2, "0")} ${period}`;
  }

  renderTimeline() {
    // Update the timeline date
    const timelineDate = this.container.querySelector("#timelineDate");
    const today = new Date();
    timelineDate.textContent = today.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  renderInsights() {
    const insightsContainer = this.container.querySelector("#productivityInsights");
    const insights = this.analyticsData.insights;

    const trendClass = `trend-${insights.productivityTrend}`;
    const trendIcon = {
      up: "📈 +12%",
      down: "📉 -5%",
      stable: "➡️ Stable",
    }[insights.productivityTrend];

    insightsContainer.innerHTML = `
              <div class="insight-card">
                  <div class="insight-icon">🎯</div>
                  <div class="insight-value">${insights.averageProductivity}%</div>
                  <div class="insight-label">Avg Productivity</div>
                  <div class="insight-trend ${trendClass}">${trendIcon}</div>
              </div>
              <div class="insight-card">
                  <div class="insight-icon">⏱️</div>
                  <div class="insight-value">${insights.totalActiveHours}h</div>
                  <div class="insight-label">Total Active</div>
                  <div class="insight-trend trend-up">📈 +2.3h</div>
              </div>
              <div class="insight-card">
                  <div class="insight-icon">🌟</div>
                  <div class="insight-value">${insights.mostProductiveTime}</div>
                  <div class="insight-label">Peak Hours</div>
                  <div class="insight-trend trend-stable">🔄 Consistent</div>
              </div>
              <div class="insight-card">
                  <div class="insight-icon">⏸️</div>
                  <div class="insight-value">${insights.totalDowntime}h</div>
                  <div class="insight-label">Downtime</div>
                  <div class="insight-trend trend-down">📉 -0.8h</div>
              </div>
          `;
  }

  updateTimelineView() {
    // Filter activity blocks based on selected time period
    const filteredData = { ...this.analyticsData };

    if (this.currentTimeFilter === "morning") {
      filteredData.teamMembers = filteredData.teamMembers.map((member) => ({
        ...member,
        activityBlocks: member.activityBlocks.filter(
          (block) => block.start >= 8 && block.start < 12
        ),
      }));
    } else if (this.currentTimeFilter === "afternoon") {
      filteredData.teamMembers = filteredData.teamMembers.map((member) => ({
        ...member,
        activityBlocks: member.activityBlocks.filter(
          (block) => block.start >= 12 && block.start < 18
        ),
      }));
    }

    // Re-render team members with filtered data
    const membersContainer = this.container.querySelector("#teamMembersGrid");
    membersContainer.innerHTML = filteredData.teamMembers
      .map((member) => this.createMemberCard(member))
      .join("");
  }

  getEmptyState() {
    return `
              <div class="empty-state">
                  <div class="empty-state-icon">👤</div>
                  <div class="empty-state-title">No Active Team Members</div>
                  <div class="empty-state-description">
                      No team members are currently being tracked. <br>
                      Check your ClickUp integration or team member activity.
                  </div>
              </div>
          `;
  }

  startRealTimeUpdates() {
    // Update every 30 seconds
    this.refreshInterval = setInterval(() => {
      this.simulateDataUpdate();
      this.renderMetrics();
      this.renderTeamMembers();
    }, 30000);
  }

  simulateDataUpdate() {
    // Simulate real-time data updates
    this.analyticsData.teamMembers.forEach((member) => {
      if (member.status === "active") {
        // Randomly update hours (simulate time tracking)
        member.todayHours += Math.random() * 0.1;
        member.todayHours = Math.round(member.todayHours * 10) / 10;

        // Occasionally update productivity
        if (Math.random() < 0.3) {
          member.productivity += (Math.random() - 0.5) * 5;
          member.productivity = Math.max(0, Math.min(100, member.productivity));
        }
      }
    });

    // Update insights
    const activeMembers = this.analyticsData.teamMembers.filter((m) => m.status === "active");
    if (activeMembers.length > 0) {
      this.analyticsData.insights.totalActiveHours = activeMembers.reduce(
        (sum, member) => sum + member.todayHours,
        0
      );
      this.analyticsData.insights.averageProductivity = Math.round(
        activeMembers.reduce((sum, member) => sum + member.productivity, 0) / activeMembers.length
      );
    }
  }

  // Public methods for external control
  refresh() {
    this.render();
  }

  updateData(newData) {
    this.analyticsData = { ...this.analyticsData, ...newData };
    this.render();
  }

  setTimeFilter(filter) {
    this.currentTimeFilter = filter;

    // Update UI
    const filters = this.container.querySelectorAll(".time-filter");
    filters.forEach((f) => f.classList.remove("active"));
    this.container.querySelector(`[data-filter="${filter}"]`).classList.add("active");

    this.updateTimelineView();
  }

  destroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }
}
