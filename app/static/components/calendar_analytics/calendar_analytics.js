/**
 * Calendar Analytics Widget Component
 * Integrates ClickUp tasks with calendar view for unified scheduling
 */

class CalendarAnalytics {
  constructor(containerId) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    this.currentDate = new Date();
    this.selectedDate = new Date();
    this.viewMode = "month";
    this.showClickUpTasks = true;
    this.showGoogleEvents = true;
    this.isCalendarPickerOpen = false;
    // Sample Google Calendar events - replace with real API data
    this.googleEvents = [
      {
        id: "gc1",
        title: "Team Standup",
        start: new Date(2025, 7, 14, 9, 0), // Aug 14, 2025, 9:00 AM
        end: new Date(2025, 7, 14, 9, 30),
        type: "meeting",
        source: "google",
      },
      {
        id: "gc2",
        title: "Client Review Call",
        start: new Date(2025, 7, 15, 14, 0),
        end: new Date(2025, 7, 15, 15, 0),
        type: "meeting",
        source: "google",
      },
      {
        id: "gc3",
        title: "Sprint Planning",
        start: new Date(2025, 7, 16, 10, 0),
        end: new Date(2025, 7, 16, 12, 0),
        type: "meeting",
        source: "google",
      },
    ];

    this.init();
  }

  init() {
    // Wait for DOM to be fully ready before rendering
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        this.render();
        this.setupEventListeners();
        this.loadClickUpTasks();
        this.loadGoogleCalendarEvents();
        this.loadLiveClickUpTasks();
      });
    } else {
      // DOM is already ready
      this.render();
      this.setupEventListeners();
      this.loadClickUpTasks();
      this.loadGoogleCalendarEvents();
      this.loadLiveClickUpTasks();
    }
  }

  render() {
    try {
      console.log('🔄 Calendar component rendering...');
      console.log('📅 Container:', this.container);
      console.log('📅 Container ID:', this.containerId);
      
      if (!this.container) {
        console.error('❌ Calendar container not found!');
        return;
      }
      
      const template = this.getTemplate();
      console.log('📝 Template generated, length:', template.length);
      
      this.container.innerHTML = template;
      console.log('✅ Template rendered to container');
      
      // Wait a bit for DOM to update
      setTimeout(() => {
        this.renderCalendar();
        console.log('✅ Calendar grid rendered');
        
        this.renderSidebar();
        console.log('✅ Sidebar rendered');
        
        console.log('✅ Calendar component render complete');
      }, 50);
      
    } catch (error) {
      console.error('❌ Error in calendar render:', error);
    }
  }

  renderCalendarPicker() {
    if (this.isCalendarPickerOpen && window.GlobalCalendarPicker) {
      // Create React element and render it
      const calendarElement = React.createElement(window.GlobalCalendarPicker, {
        selectedDate: this.selectedDate,
        onDateSelect: (date) => {
          this.selectedDate = date;
          this.isCalendarPickerOpen = false;
          this.selectDate(date); // Your existing method
          this.removeCalendarPicker();
        },
        onClose: () => {
          this.isCalendarPickerOpen = false;
          this.removeCalendarPicker();
        },
        isOpen: this.isCalendarPickerOpen,
      });

      // Render to a container
      const calendarContainer = document.createElement("div");
      calendarContainer.id = "calendar-picker-container";
      document.body.appendChild(calendarContainer);
      ReactDOM.render(calendarElement, calendarContainer);
    }
  }

  removeCalendarPicker() {
    const container = document.getElementById("calendar-picker-container");
    if (container) {
      ReactDOM.unmountComponentAtNode(container);
      container.remove();
    }
  }

  getTemplate() {
    return `
        <div class="calendar-analytics-widget">
          <!-- Calendar Header -->
          <div class="calendar-header">
            <div class="calendar-title">
              <h3 class="section-title">📅 Unified Calendar Dashboard</h3>
              <div class="calendar-subtitle">ClickUp Tasks + Google Calendar</div>
            </div>
            
            <div class="calendar-controls">
              <button class="calendar-nav-btn" id="prevMonth">‹</button>
              <div class="calendar-month-year" id="monthYear"></div>
              <button class="calendar-nav-btn" id="nextMonth">›</button>
              <button class="today-btn" id="todayBtn">Today</button>
            </div>
          </div>
  
          <!-- Calendar Filters -->
          <div class="calendar-filters">
            <label class="filter-toggle">
              <input type="checkbox" id="showClickUp" checked>
              <span class="toggle-text">ClickUp Tasks</span>
              <span class="toggle-count" id="clickupCount">0</span>
            </label>
            
            <label class="filter-toggle">
              <input type="checkbox" id="showGoogle" checked>
              <span class="toggle-text">Google Calendar</span>
              <span class="toggle-count" id="googleCount">0</span>
            </label>
  
            <div class="calendar-legend">
              <div class="legend-item">
                <div class="legend-color urgent"></div>
                <span>Urgent Tasks</span>
              </div>
              <div class="legend-item">
                <div class="legend-color high"></div>
                <span>High Priority</span>
              </div>
              <div class="legend-item">
                <div class="legend-color normal"></div>
                <span>Normal Tasks</span>
              </div>
              <div class="legend-item">
                <div class="legend-color google-event"></div>
                <span>Google Events</span>
              </div>
            </div>
          </div>
  
          <!-- Main Calendar Content -->
          <div class="calendar-content">
            <!-- Calendar Grid -->
            <div class="calendar-grid-container">
              <div class="calendar-grid" id="calendarGrid">
                <!-- Calendar will be rendered here -->
              </div>
            </div>
  
            <!-- Sidebar -->
            <div class="calendar-sidebar">
              <div class="sidebar-header">
                <h4 id="selectedDateTitle">Today</h4>
                <div class="selected-date-info" id="selectedDateInfo"></div>
              </div>
  
              <div class="sidebar-content">
                <!-- Daily Summary -->
                <div class="daily-summary" id="dailySummary">
                  <!-- Daily events and tasks will be shown here -->
                </div>
  
                <!-- Quick Stats -->
                <div class="quick-stats">
                  <div class="stat-card">
                    <div class="stat-number" id="dueTodayCount">0</div>
                    <div class="stat-label">Due Today</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-number" id="dueWeekCount">0</div>
                    <div class="stat-label">Due This Week</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-number" id="overdueCount">0</div>
                    <div class="stat-label">Overdue</div>
                  </div>
                </div>
  
                <!-- Integration Status -->
                <div class="integration-status">
                  <h5>Integration Status</h5>
                  <div class="status-item">
                    <span class="status-indicator active"></span>
                    <span>ClickUp Connected</span>
                  </div>
                  <div class="status-item">
                    <span class="status-indicator demo"></span>
                    <span>Google Calendar (Demo)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
  }

  setupEventListeners() {
    // Navigation controls
    document.getElementById("prevMonth").addEventListener("click", () => {
      this.currentDate.setMonth(this.currentDate.getMonth() - 1);
      this.renderCalendar();
    });

    document.getElementById("nextMonth").addEventListener("click", () => {
      this.currentDate.setMonth(this.currentDate.getMonth() + 1);
      this.renderCalendar();
    });

    document.getElementById("todayBtn").addEventListener("click", () => {
      this.currentDate = new Date();
      this.selectedDate = new Date();
      this.renderCalendar();
      this.renderSidebar();
    });

    if (document.getElementById("dateFilter")) {
      document.getElementById("dateFilter").addEventListener("click", () => {
        this.openCalendarPicker();
      });
    }

    // Filter toggles
    document.getElementById("showClickUp").addEventListener("change", (e) => {
      this.showClickUpTasks = e.target.checked;
      this.renderCalendar();
    });

    document.getElementById("showGoogle").addEventListener("change", (e) => {
      this.showGoogleEvents = e.target.checked;
      this.renderCalendar();
    });
  }

  renderCalendar() {
    const monthYear = document.getElementById("monthYear");
    const calendarGrid = document.getElementById("calendarGrid");

    // Update month/year display
    monthYear.textContent = this.currentDate.toLocaleDateString("en-US", {
      month: "long",
      year: "numeric",
    });

    // Generate calendar grid
    const firstDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
    const lastDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());

    let calendarHTML = `
        <div class="calendar-weekdays">
          ${["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            .map((day) => `<div class="weekday">${day}</div>`)
            .join("")}
        </div>
        <div class="calendar-days">
      `;

    for (let i = 0; i < 42; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);

      const isCurrentMonth = date.getMonth() === this.currentDate.getMonth();
      const isToday = this.isToday(date);
      const isSelected = this.isSameDay(date, this.selectedDate);

      const dayEvents = this.getEventsForDate(date);
      const dayTasks = this.getTasksForDate(date);

      calendarHTML += `
          <div class="calendar-day ${isCurrentMonth ? "current-month" : "other-month"} ${
        isToday ? "today" : ""
      } ${isSelected ? "selected" : ""}"
               data-date="${date.toISOString().split("T")[0]}"
               onclick="window.calendarAnalytics.selectDate(new Date('${date.toISOString()}'))">
            <div class="day-number">${date.getDate()}</div>
            <div class="day-events">
              ${this.renderDayEvents(dayEvents, dayTasks)}
            </div>
          </div>
        `;
    }

    calendarHTML += "</div>";
    calendarGrid.innerHTML = calendarHTML;

    // Update filter counts
    this.updateFilterCounts();
  }

  renderDayEvents(events, tasks) {
    let html = "";

    // Render Google Calendar events
    if (this.showGoogleEvents) {
      events.forEach((event) => {
        html += `<div class="day-event google-event" title="${event.title}">${event.title}</div>`;
      });
    }

    // Render ClickUp tasks with enhanced display
    if (this.showClickUpTasks) {
      tasks.forEach((task) => {
        const priorityClass = task.priority
          ? `priority-${task.priority.priority}`
          : "priority-normal";
        
        const statusClass = task.status ? `status-${task.status.toLowerCase().replace(' ', '-')}` : '';
        const taskLink = task.url ? `onclick="window.open('${task.url}', '_blank')"` : '';
        const clickableClass = task.url ? 'clickable' : '';
        
        // Truncate task name for display
        const displayName = task.name.length > 20 ? task.name.substring(0, 20) + '...' : task.name;
        
        html += `
          <div class="day-event clickup-task ${priorityClass} ${statusClass} ${clickableClass}" 
               title="${task.name} (${task.status || 'No Status'})" 
               ${taskLink}>
            <div class="task-priority-indicator"></div>
            <div class="task-content">
              <div class="task-name">${displayName}</div>
              ${task.project_name ? `<div class="task-project">${task.project_name}</div>` : ''}
            </div>
          </div>
        `;
      });
    }

    return html;
  }

  renderSidebar() {
    const selectedDateTitle = document.getElementById("selectedDateTitle");
    const selectedDateInfo = document.getElementById("selectedDateInfo");
    const dailySummary = document.getElementById("dailySummary");

    // Update selected date display
    selectedDateTitle.textContent = this.selectedDate.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
    });

    selectedDateInfo.textContent = this.isToday(this.selectedDate)
      ? "Today"
      : this.selectedDate.toLocaleDateString("en-US", { year: "numeric" });

    // Get events and tasks for selected date
    const events = this.getEventsForDate(this.selectedDate);
    const tasks = this.getTasksForDate(this.selectedDate);

    // Render daily summary
    let summaryHTML = "";

    if (events.length === 0 && tasks.length === 0) {
      summaryHTML = '<div class="no-events">No events or tasks scheduled</div>';
    } else {
      // Sort all items by time
      const allItems = [
        ...events.map((e) => ({ ...e, type: "event" })),
        ...tasks.map((t) => ({ ...t, type: "task" })),
      ].sort((a, b) => {
        const aTime = a.start || a.due_date || 0;
        const bTime = b.start || b.due_date || 0;
        return new Date(aTime) - new Date(bTime);
      });

      allItems.forEach((item) => {
        if (item.type === "event") {
          const timeStr = item.start
            ? new Date(item.start).toLocaleTimeString("en-US", {
                hour: "numeric",
                minute: "2-digit",
              })
            : "";

          const eventLink = item.html_link ? `onclick="window.open('${item.html_link}', '_blank')"` : '';
          const clickableClass = item.html_link ? 'clickable' : '';

          summaryHTML += `
              <div class="summary-item event-item ${clickableClass}" ${eventLink}>
                <div class="item-time">${timeStr}</div>
                <div class="item-content">
                  <div class="item-title">${item.title}</div>
                  <div class="item-meta">Google Calendar</div>
                  ${item.location ? `<div class="item-location">📍 ${item.location}</div>` : ''}
                </div>
              </div>
            `;
        } else {
          const priorityClass = item.priority
            ? `priority-${item.priority.priority}`
            : "priority-normal";
          const assignees = item.assignees ? item.assignees.map((a) => a.username).join(", ") : "";

          summaryHTML += `
              <div class="summary-item task-item ${priorityClass}">
                <div class="item-priority"></div>
                <div class="item-content">
                  <div class="item-title">${item.name}</div>
                  <div class="item-meta">
                    ${item.priority ? item.priority.priority.toUpperCase() : "NORMAL"}
                    ${assignees ? ` • ${assignees}` : ""}
                  </div>
                </div>
              </div>
            `;
        }
      });
    }

    dailySummary.innerHTML = summaryHTML;

    // Update quick stats
    this.updateQuickStats();
  }

  openCalendarPicker() {
    this.isCalendarPickerOpen = true;
    this.renderCalendarPicker();
  }

  loadClickUpTasks() {
    // Wait for dashboard to be properly initialized
    const waitForDashboard = () => {
      if (window.dashboard && window.dashboard.components && window.dashboard.components.projects) {
        // Get tasks from the existing ProjectsTracker component
        this.clickUpTasks = window.dashboard.components.projects.getAllTasks();
        console.log('✅ Loaded ClickUp tasks from ProjectsTracker:', this.clickUpTasks.length);
      } else {
        // Fallback to sample data structure matching your existing format
        this.clickUpTasks = [
          {
            id: "86aanbgch",
            name: "Email updates bug - not receiving win notifications",
            status: "complete",
            due_date: "1723334400000", // Today
            priority: { priority: "urgent", color: "#f50000" },
            assignees: [{ username: "Tricia Kennedy" }, { username: "Jan" }],
          },
          {
            id: "86aanbe1d",
            name: "Photo acceptance issues for tickets",
            status: "in progress",
            due_date: "1723420800000", // Tomorrow
            priority: { priority: "urgent", color: "#f50000" },
            assignees: [{ username: "Tricia Kennedy" }],
          },
          {
            id: "86aanbd0q",
            name: "App incorrectly showing no winners",
            status: "bugs",
            due_date: "1723507200000", // Day after tomorrow
            priority: { priority: "urgent", color: "#f50000" },
            assignees: [{ username: "Jan" }],
          },
        ];
        console.log('⚠️ Using fallback sample data - ProjectsTracker not ready yet');
      }

      this.renderCalendar();
      this.renderSidebar();
    };

    // Try immediately, if not ready, wait a bit and try again
    if (window.dashboard && window.dashboard.components && window.dashboard.components.projects) {
      waitForDashboard();
    } else {
      // Wait for dashboard to be ready
      setTimeout(waitForDashboard, 100);
    }
  }

  getEventsForDate(date) {
    if (!this.showGoogleEvents) return [];

    return this.googleEvents.filter((event) => {
      const eventDate = new Date(event.start);
      return this.isSameDay(eventDate, date);
    });
  }

  getTasksForDate(date) {
    if (!this.showClickUpTasks || !this.clickUpTasks) return [];

    return this.clickUpTasks.filter((task) => {
      if (!task.due_date) return false;
      const taskDate = new Date(parseInt(task.due_date));
      return this.isSameDay(taskDate, date);
    });
  }

  selectDate(date) {
    this.selectedDate = new Date(date);
    this.renderCalendar();
    this.renderSidebar();
  }

  updateFilterCounts() {
    const clickupCount = document.getElementById("clickupCount");
    const googleCount = document.getElementById("googleCount");

    if (clickupCount) {
      clickupCount.textContent = this.clickUpTasks ? this.clickUpTasks.length : 0;
    }

    if (googleCount) {
      googleCount.textContent = this.googleEvents.length;
    }
  }

  updateQuickStats() {
    const today = new Date();
    const weekFromNow = new Date();
    weekFromNow.setDate(today.getDate() + 7);

    let dueToday = 0;
    let dueThisWeek = 0;
    let overdue = 0;

    if (this.clickUpTasks) {
      this.clickUpTasks.forEach((task) => {
        if (!task.due_date) return;

        const dueDate = new Date(parseInt(task.due_date));

        if (this.isSameDay(dueDate, today)) {
          dueToday++;
        } else if (dueDate <= weekFromNow && dueDate > today) {
          dueThisWeek++;
        } else if (dueDate < today) {
          overdue++;
        }
      });
    }

    document.getElementById("dueTodayCount").textContent = dueToday;
    document.getElementById("dueWeekCount").textContent = dueThisWeek;
    document.getElementById("overdueCount").textContent = overdue;
  }

  // Utility methods
  isSameDay(date1, date2) {
    return date1.toDateString() === date2.toDateString();
  }

  isToday(date) {
    return this.isSameDay(date, new Date());
  }

  // Public methods for external control
  refresh() {
    this.loadClickUpTasks();
    this.loadGoogleCalendarEvents();
    this.loadLiveClickUpTasks();
    this.renderCalendar();
    this.renderSidebar();
  }

  async loadLiveClickUpTasks() {
    try {
      console.log('🔄 Loading live ClickUp tasks...');
      
      // Fetch tasks from the calendar tasks API
      const response = await fetch('/api/calendar-tasks?force_refresh=true');
      const data = await response.json();
      
      if (data.success && data.tasks) {
        console.log(`✅ Loaded ${data.tasks.length} live ClickUp tasks for calendar`);
        
        // Convert to calendar format
        this.clickUpTasks = data.tasks.map(task => ({
          id: task.id,
          name: task.name,
          status: task.status?.status || task.status,
          due_date: task.due_date,
          priority: task.priority,
          assignees: task.assignees || [],
          list_name: task.list_name,
          project_name: task.project_name,
          url: task.url
        }));
        
        console.log(`📅 Processed ${this.clickUpTasks.length} tasks for calendar display`);
        
        // Update the calendar display
        this.updateFilterCounts();
        this.renderCalendar();
        
      } else {
        console.warn('⚠️ No live ClickUp tasks found or API error');
        // Keep existing tasks if available
        if (!this.clickUpTasks || this.clickUpTasks.length === 0) {
          this.loadClickUpTasks(); // Fallback to existing method
        }
      }
      
    } catch (error) {
      console.error('❌ Error loading live ClickUp tasks:', error);
      // Fallback to existing method
      this.loadClickUpTasks();
    }
  }

  async loadGoogleCalendarEvents() {
    try {
      console.log('🔄 Loading Google Calendar events...');
      
      const response = await fetch('/api/calendar-events?days=30');
      const data = await response.json();
      
      if (data.success && data.events) {
        console.log(`✅ Loaded ${data.events.length} Google Calendar events`);
        
        // Convert Google Calendar events to the format expected by the calendar
        this.googleEvents = data.events.map(event => {
          const startTime = event.start_time ? new Date(event.start_time) : new Date();
          const endTime = event.end_time ? new Date(event.end_time) : new Date(startTime.getTime() + 60 * 60 * 1000); // 1 hour default
          
          return {
            id: event.id,
            title: event.title,
            start: startTime,
            end: endTime,
            type: 'meeting',
            source: 'google',
            description: event.description || '',
            location: event.location || '',
            attendees: event.attendees || [],
            html_link: event.html_link || ''
          };
        });
        
        // Update the integration status
        this.updateIntegrationStatus('google', 'connected');
        
        // Update the calendar display
        this.updateFilterCounts();
        this.renderCalendar();
        
      } else {
        console.warn('⚠️ No Google Calendar events found or API error');
        this.updateIntegrationStatus('google', 'demo');
      }
      
    } catch (error) {
      console.error('❌ Error loading Google Calendar events:', error);
      this.updateIntegrationStatus('google', 'error');
    }
  }

  updateIntegrationStatus(service, status) {
    // Find the status item for the service
    const statusItems = document.querySelectorAll('.status-item');
    let targetItem = null;
    
    for (const item of statusItems) {
      const text = item.textContent.toLowerCase();
      if (service === 'google' && text.includes('google')) {
        targetItem = item;
        break;
      } else if (service === 'clickup' && text.includes('clickup')) {
        targetItem = item;
        break;
      }
    }
    
    if (targetItem) {
      const indicator = targetItem.querySelector('.status-indicator');
      if (indicator) {
        indicator.className = `status-indicator ${status}`;
      }
      
      // Update the text
      const textElement = targetItem.querySelector('span:last-child');
      if (textElement) {
        if (status === 'connected') {
          textElement.textContent = service === 'google' ? 'Google Calendar Connected' : 'ClickUp Connected';
        } else if (status === 'demo') {
          textElement.textContent = service === 'google' ? 'Google Calendar (Demo)' : 'ClickUp (Demo)';
        } else if (status === 'error') {
          textElement.textContent = service === 'google' ? 'Google Calendar Error' : 'ClickUp Error';
        }
      }
    }
  }

  updateData(newData) {
    if (newData.clickUpTasks) {
      this.clickUpTasks = newData.clickUpTasks;
    }
    if (newData.googleEvents) {
      this.googleEvents = newData.googleEvents;
    }
    this.refresh();
  }

  goToDate(date) {
    this.currentDate = new Date(date);
    this.selectedDate = new Date(date);
    this.renderCalendar();
    this.renderSidebar();
  }

  setViewMode(mode) {
    this.viewMode = mode;
    // Could extend to support week/day views
    this.renderCalendar();
  }
}

// Make it globally accessible for the selectDate functionality
window.calendarAnalytics = null;
