/**
 * Projects Tracker Widget Component
 * Manages project and task tracking with team/user views
 */

class ProjectsTracker {
  constructor(containerId) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    this.currentView = "team";
    this.currentFilter = "all";
    this.searchQuery = "";

    // Sample project data - replace with actual data source
    this.projectData = {
      90132462540: {
        name: "Web Design and App Development",
        folders: [
          {
            id: "901310157028",
            name: "TheSantris",
            lists: [
              {
                id: "901310471238",
                name: "Lotto (P1)",
                status: {
                  status: "red",
                  color: "#d33d44",
                  hide_label: true,
                },
                tasks: [
                  {
                    id: "86aanbgch",
                    name: "Email updates bug - not receiving win notifications",
                    status: "complete",
                    assignees: [
                      {
                        id: 99989505,
                        username: "Tricia Kennedy",
                        email: "triciais@sourceselect.ca",
                      },
                      {
                        id: 126127973,
                        username: "Jan",
                        email: "janisatssm@gmail.com",
                      },
                    ],
                    due_date: "1754042400000",
                    start_date: null,
                    priority: {
                      color: "#f50000",
                      id: "1",
                      orderindex: "1",
                      priority: "urgent",
                    },
                  },
                  {
                    id: "86aanbe1d",
                    name: "Photo acceptance issues for tickets",
                    status: "in progress",
                    assignees: [
                      {
                        id: 99989505,
                        username: "Tricia Kennedy",
                        email: "triciais@sourceselect.ca",
                      },
                      {
                        id: 126127973,
                        username: "Jan",
                        email: "janisatssm@gmail.com",
                      },
                    ],
                    due_date: "1754042400000",
                    start_date: "1751364000000",
                    priority: {
                      color: "#f50000",
                      id: "1",
                      orderindex: "1",
                      priority: "urgent",
                    },
                  },
                  {
                    id: "86aanbd0q",
                    name: "App incorrectly showing no winners",
                    status: "bugs",
                    assignees: [
                      {
                        id: 126127973,
                        username: "Jan",
                        email: "janisatssm@gmail.com",
                      },
                    ],
                    due_date: "1754042400000",
                    start_date: null,
                    priority: {
                      color: "#f50000",
                      id: "1",
                      orderindex: "1",
                      priority: "urgent",
                    },
                  },
                  {
                    id: "86aa4x0kp",
                    name: "Email notification design",
                    status: "to do",
                    assignees: [
                      {
                        id: 126127973,
                        username: "Jan",
                        email: "janisatssm@gmail.com",
                      },
                    ],
                    due_date: null,
                    start_date: null,
                    priority: null,
                  },
                ],
              },
            ],
          },
        ],
      },
      90134767504: {
        name: "Design & Creative Services",
        folders: [
          {
            id: "901310136443",
            name: "Design & Media",
            lists: [
              {
                id: "901309584374",
                name: "The Cardboard Casket",
                tasks: [
                  {
                    id: "86aa5fjp3",
                    name: "Vinyl for Cardboard Casket and Retro Classics",
                    status: "on hold",
                    assignees: [
                      {
                        id: 93916583,
                        username: "Calum",
                        email: "calumis@sourceselect.ca",
                      },
                    ],
                    due_date: null,
                    start_date: "1753264800000",
                    priority: {
                      color: "#f8ae00",
                      id: "2",
                      orderindex: "2",
                      priority: "high",
                    },
                  },
                  {
                    id: "86a7pyf7m",
                    name: "Create arrows colour proposal",
                    status: "complete",
                    assignees: [],
                    due_date: null,
                    start_date: null,
                    priority: null,
                  },
                ],
              },
            ],
          },
        ],
      },
      90138214659: {
        name: "Digital Marketing",
        folders: [
          {
            id: "901311011097",
            name: "Social Media & Content Marketing",
            lists: [
              {
                id: "901316071894",
                name: "Ryan Targerson",
                tasks: [
                  {
                    id: "86aa4ry1f",
                    name: "Overtime tracking implementation",
                    status: "complete",
                    assignees: [],
                    due_date: null,
                    start_date: null,
                    priority: {
                      color: "#6fddff",
                      id: "3",
                      orderindex: "3",
                      priority: "normal",
                    },
                  },
                  {
                    id: "86aa4p4v2",
                    name: "Time log option development",
                    status: "to do",
                    assignees: [],
                    due_date: "1754560800000",
                    start_date: null,
                    priority: {
                      color: "#6fddff",
                      id: "3",
                      orderindex: "3",
                      priority: "normal",
                    },
                  },
                  {
                    id: "86aa4nxjr",
                    name: "Check for time tracking functionality",
                    status: "in progress",
                    assignees: [
                      {
                        id: 99989505,
                        username: "Tricia Kennedy",
                        email: "triciais@sourceselect.ca",
                      },
                    ],
                    due_date: "1723334400000",
                    start_date: "1722124800000",
                    priority: {
                      color: "#f8ae00",
                      id: "2",
                      orderindex: "2",
                      priority: "high",
                    },
                  },
                ],
              },
            ],
          },
        ],
      },
    };

    this.init();
  }

  init() {
    this.render();
    this.setupEventListeners();
  }

  render() {
    this.container.innerHTML = this.getTemplate();
    this.renderMetrics();
    this.renderContent();
  }

  getTemplate() {
    return `
            <div class="projects-tracker-widget">
                <!-- Metrics Grid -->
                <div class="metrics-grid" id="projectMetrics">
                    <!-- Metrics will be populated by renderMetrics() -->
                </div>

                <!-- Main Content Section -->
                <div class="projects-section">
                    <div class="section-header">
                        <h3 class="section-title"> Project Overview</h3>
                    </div>

                    <!-- Search Input -->
                    <input type="text" class="search-input" placeholder="🔍 Search projects and tasks..." id="searchInput">
                    
                    <!-- View Toggle -->
                    <div class="view-toggle-container">
                        <div class="view-toggle">
                            <input type="radio" id="teamView" name="viewType" value="team" checked>
                            <label for="teamView" class="toggle-option">
                                <span class="toggle-icon"></span>
                                <span class="toggle-text">Team View</span>
                            </label>
                            
                            <input type="radio" id="userView" name="viewType" value="user">
                            <label for="userView" class="toggle-option">
                                <span class="toggle-icon"></span>
                                <span class="toggle-text">User View</span>
                            </label>
                            
                            <div class="toggle-slider"></div>
                        </div>
                    </div>

                    <!-- Project Filters -->
                    <div class="project-filters" id="projectFilters">
                        <div class="project-filter active" data-filter="all">All Teams</div>
                        <div class="project-filter" data-filter="urgent">🔥 Urgent</div>
                        <div class="project-filter" data-filter="overdue">⚠️ Overdue</div>
                        <div class="project-filter" data-filter="stuck">⏰ Stuck in Progress</div>
                    </div>

                    <!-- Content Container -->
                    <div class="teams-grid view-container" id="teamsContainer">
                        <!-- Teams will be populated by renderTeams() -->
                    </div>

                    <div class="users-grid view-container" id="usersContainer" style="display: none;">
                        <!-- Users will be populated by renderUsers() -->
                    </div>
                </div>
            </div>
        `;
  }

  setupEventListeners() {
    // View toggle
    const viewToggle = this.container.querySelectorAll('input[name="viewType"]');
    viewToggle.forEach((toggle) => {
      toggle.addEventListener("change", (e) => {
        this.switchView(e.target.value);
      });
    });

    // Project filters
    const filters = this.container.querySelectorAll(".project-filter");
    filters.forEach((filter) => {
      filter.addEventListener("click", () => {
        filters.forEach((f) => f.classList.remove("active"));
        filter.classList.add("active");

        this.currentFilter = filter.dataset.filter;
        this.applyFilters();
      });
    });

    // Search
    const searchInput = this.container.querySelector("#searchInput");
    searchInput.addEventListener("input", (e) => {
      this.searchQuery = e.target.value;
      this.applySearch();
    });
  }

  renderMetrics() {
    const metricsContainer = this.container.querySelector("#projectMetrics");
    const allTasks = this.getAllTasks();

    const totalTasks = allTasks.length;
    const completedTasks = allTasks.filter((task) => task.status === "complete").length;
    const inProgressTasks = allTasks.filter((task) => task.status === "in progress").length;
    const overdueTasks = allTasks.filter((task) => this.isOverdue(task)).length;
    const urgentTasks = allTasks.filter((task) => task.priority?.priority === "urgent").length;

    metricsContainer.innerHTML = `
            <div class="metric-card">
                <div class="metric-icon">📋</div>
                <div class="metric-label">Total Tasks</div>
                <div class="metric-value">${totalTasks}</div>
                <div class="metric-subtitle">Across all projects</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">✅</div>
                <div class="metric-label">Completed</div>
                <div class="metric-value">${completedTasks}</div>
                <div class="metric-subtitle">${
                  totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0
                }% completion rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">🔄</div>
                <div class="metric-label">In Progress</div>
                <div class="metric-value">${inProgressTasks}</div>
                <div class="metric-subtitle">Currently active</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">⚠️</div>
                <div class="metric-label">Overdue</div>
                <div class="metric-value">${overdueTasks}</div>
                <div class="metric-subtitle">Need attention</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">🔥</div>
                <div class="metric-label">Urgent</div>
                <div class="metric-value">${urgentTasks}</div>
                <div class="metric-subtitle">High priority items</div>
            </div>
        `;
  }

  renderContent() {
    if (this.currentView === "team") {
      this.renderTeams();
    } else {
      this.renderUsers();
    }
  }

  renderTeams() {
    const teamsContainer = this.container.querySelector("#teamsContainer");
    teamsContainer.innerHTML = "";

    Object.entries(this.projectData).forEach(([teamId, team]) => {
      const teamCard = this.createTeamCard(team);
      teamsContainer.appendChild(teamCard);
    });
  }

  renderUsers() {
    const usersContainer = this.container.querySelector("#usersContainer");
    usersContainer.innerHTML = "";

    const usersMap = new Map();

    // Collect all tasks by user
    Object.values(this.projectData).forEach((team) => {
      const teamTasks = this.getTeamTasks(team);

      teamTasks.forEach((task) => {
        if (task.assignees && task.assignees.length > 0) {
          task.assignees.forEach((assignee) => {
            if (!usersMap.has(assignee.id)) {
              usersMap.set(assignee.id, {
                ...assignee,
                tasks: [],
                teams: new Set(),
              });
            }

            const userTaskData = { ...task, teamName: team.name };
            usersMap.get(assignee.id).tasks.push(userTaskData);
            usersMap.get(assignee.id).teams.add(team.name);
          });
        }
      });
    });

    // Create user cards
    Array.from(usersMap.values()).forEach((user) => {
      const userCard = this.createUserCard(user);
      usersContainer.appendChild(userCard);
    });
  }

  createTeamCard(team) {
    const card = document.createElement("div");
    card.className = "team-card";

    const allTasks = this.getTeamTasks(team);
    const completedTasks = allTasks.filter((task) => task.status === "complete").length;
    const totalTasks = allTasks.length;
    const progressPercentage = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

    const overdueCount = allTasks.filter((task) => this.isOverdue(task)).length;
    const urgentCount = allTasks.filter((task) => task.priority?.priority === "urgent").length;

    card.innerHTML = `
            <div class="team-header">
                <div>
                    <div class="team-name">${team.name}</div>
                    <div class="team-stats">
                        <span>📊 ${totalTasks} tasks</span>
                        ${
                          urgentCount > 0
                            ? `<span style="color: #ff4500; text-shadow: 0 0 8px rgba(255, 69, 0, 0.5);">🔥 ${urgentCount} urgent</span>`
                            : ""
                        }
                        ${
                          overdueCount > 0
                            ? `<span style="color: #ff4500; text-shadow: 0 0 8px rgba(255, 69, 0, 0.5);">⚠️ ${overdueCount} overdue</span>`
                            : ""
                        }
                    </div>
                </div>
                ${overdueCount > 0 ? `<div class="notification-badge">${overdueCount}</div>` : ""}
            </div>
            
            <div class="progress-section">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progressPercentage}%"></div>
                </div>
                <div class="progress-text">
                    <span>${completedTasks}/${totalTasks} completed</span>
                    <span>${Math.round(progressPercentage)}%</span>
                </div>
            </div>
            
            <div class="task-list">
                ${allTasks
                  .slice(0, 8)
                  .map((task) => this.createTaskItem(task))
                  .join("")}
                ${
                  allTasks.length > 8
                    ? `<div style="text-align: center; color: #64748b; margin-top: 12px; font-size: 0.8rem;">+${
                        allTasks.length - 8
                      } more tasks</div>`
                    : ""
                }
            </div>
        `;

    return card;
  }

  createUserCard(user) {
    const card = document.createElement("div");
    card.className = "user-card";

    const completedTasks = user.tasks.filter((task) => task.status === "complete").length;
    const inProgressTasks = user.tasks.filter((task) => task.status === "in progress").length;
    const totalTasks = user.tasks.length;
    const overdueCount = user.tasks.filter((task) => this.isOverdue(task)).length;
    const urgentCount = user.tasks.filter((task) => task.priority?.priority === "urgent").length;

    // Calculate workload
    const workloadLevel = this.getWorkloadLevel(totalTasks);
    const progressPercentage = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

    const userInitials = user.username
      .split(" ")
      .map((name) => name.charAt(0))
      .join("")
      .slice(0, 2);
    const teamsArray = Array.from(user.teams);

    card.innerHTML = `
            <div class="user-header">
                <div class="user-avatar">
                    ${userInitials}
                </div>
                <div class="user-info">
                    <div class="user-name">${user.username}</div>
                    <div class="user-email">${user.email}</div>
                    <div class="user-stats">
                        <span>🏢 ${teamsArray.length} team${
      teamsArray.length !== 1 ? "s" : ""
    }</span>
                        ${
                          urgentCount > 0
                            ? `<span style="color: #ff4500; text-shadow: 0 0 8px rgba(255, 69, 0, 0.5);">🔥 ${urgentCount} urgent</span>`
                            : ""
                        }
                        ${
                          overdueCount > 0
                            ? `<span style="color: #ff4500; text-shadow: 0 0 8px rgba(255, 69, 0, 0.5);">⚠️ ${overdueCount} overdue</span>`
                            : ""
                        }
                    </div>
                </div>
                <div class="workload-indicator">
                    <div class="workload-circle workload-${workloadLevel.level}">
                        ${totalTasks}
                    </div>
                    <div class="workload-label">${workloadLevel.label}</div>
                </div>
                ${overdueCount > 0 ? `<div class="notification-badge">${overdueCount}</div>` : ""}
            </div>
            
            <div class="user-task-summary">
                <div class="task-summary-item summary-completed">
                    <div class="summary-number">${completedTasks}</div>
                    <div class="summary-label">Completed</div>
                </div>
                <div class="task-summary-item summary-progress">
                    <div class="summary-number">${inProgressTasks}</div>
                    <div class="summary-label">In Progress</div>
                </div>
                <div class="task-summary-item summary-total">
                    <div class="summary-number">${totalTasks}</div>
                    <div class="summary-label">Total</div>
                </div>
            </div>
            
            <div class="progress-section">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progressPercentage}%"></div>
                </div>
                <div class="progress-text">
                    <span>Progress: ${completedTasks}/${totalTasks}</span>
                    <span>${Math.round(progressPercentage)}%</span>
                </div>
            </div>
            
            <div class="task-list">
                ${user.tasks
                  .slice(0, 6)
                  .map((task) => this.createUserTaskItem(task))
                  .join("")}
                ${
                  user.tasks.length > 6
                    ? `<div style="text-align: center; color: #64748b; margin-top: 12px; font-size: 0.8rem;">+${
                        user.tasks.length - 6
                      } more tasks</div>`
                    : ""
                }
            </div>
        `;

    return card;
  }

  createTaskItem(task) {
    const now = Date.now();
    const dueDate = task.due_date ? parseInt(task.due_date) : null;
    const startDate = task.start_date ? parseInt(task.start_date) : null;

    let taskClasses = "task-item";
    let warnings = [];

    // Check warnings
    if (this.isOverdue(task)) {
      taskClasses += " warning-overdue";
      warnings.push("OVERDUE");
    } else if (dueDate && dueDate - now < 3 * 24 * 60 * 60 * 1000 && dueDate > now) {
      taskClasses += " warning-due-soon";
      warnings.push("Due soon");
    }

    if (task.status === "in progress" && startDate && now - startDate > 14 * 24 * 60 * 60 * 1000) {
      taskClasses += " warning-stuck";
      warnings.push("Long running");
    }

    const assigneeAvatars = task.assignees
      ? task.assignees
          .map(
            (assignee) =>
              `<div class="avatar" title="${assignee.username}">${assignee.username
                .charAt(0)
                .toUpperCase()}</div>`
          )
          .join("")
      : "";

    const priorityClass = task.priority ? `priority-${task.priority.priority}` : "";
    const statusClass = `status-${task.status.replace(" ", "-")}`;

    return `
            <div class="${taskClasses}">
                <div class="task-status ${statusClass}"></div>
                <div class="task-content">
                    <div class="task-name">${task.name}</div>
                    <div class="task-meta">
                        ${
                          task.priority
                            ? `<span class="priority-indicator ${priorityClass}">${task.priority.priority.toUpperCase()}</span>`
                            : ""
                        }
                        ${
                          dueDate
                            ? `<span>Due: ${new Date(dueDate).toLocaleDateString()}</span>`
                            : ""
                        }
                        ${
                          warnings.length > 0
                            ? `<span style="color: #ff4500; font-weight: bold; text-shadow: 0 0 6px rgba(255, 69, 0, 0.5);">${warnings.join(
                                " • "
                              )}</span>`
                            : ""
                        }
                    </div>
                </div>
                ${assigneeAvatars ? `<div class="assignee-avatars">${assigneeAvatars}</div>` : ""}
            </div>
        `;
  }

  createUserTaskItem(task) {
    const now = Date.now();
    const dueDate = task.due_date ? parseInt(task.due_date) : null;
    const startDate = task.start_date ? parseInt(task.start_date) : null;

    let taskClasses = "task-item";
    let warnings = [];

    // Check warnings
    if (this.isOverdue(task)) {
      taskClasses += " warning-overdue";
      warnings.push("OVERDUE");
    } else if (dueDate && dueDate - now < 3 * 24 * 60 * 60 * 1000 && dueDate > now) {
      taskClasses += " warning-due-soon";
      warnings.push("Due soon");
    }

    if (task.status === "in progress" && startDate && now - startDate > 14 * 24 * 60 * 60 * 1000) {
      taskClasses += " warning-stuck";
      warnings.push("Long running");
    }

    const priorityClass = task.priority ? `priority-${task.priority.priority}` : "";
    const statusClass = `status-${task.status.replace(" ", "-")}`;

    return `
            <div class="${taskClasses}">
                <div class="task-status ${statusClass}"></div>
                <div class="task-content">
                    <div class="task-name">${task.name}</div>
                    <div class="task-meta">
                        <span style="color: #8b5cf6; font-weight: 500;">📁 ${task.teamName}</span>
                        ${
                          task.priority
                            ? `<span class="priority-indicator ${priorityClass}">${task.priority.priority.toUpperCase()}</span>`
                            : ""
                        }
                        ${
                          dueDate
                            ? `<span>Due: ${new Date(dueDate).toLocaleDateString()}</span>`
                            : ""
                        }
                        ${
                          warnings.length > 0
                            ? `<span style="color: #ff4500; font-weight: bold; text-shadow: 0 0 6px rgba(255, 69, 0, 0.5);">${warnings.join(
                                " • "
                              )}</span>`
                            : ""
                        }
                    </div>
                </div>
            </div>
        `;
  }

  switchView(viewType) {
    const teamsContainer = this.container.querySelector("#teamsContainer");
    const usersContainer = this.container.querySelector("#usersContainer");
    const projectFilters = this.container.querySelector("#projectFilters");

    // Add switching animation
    teamsContainer.classList.add("switching");
    usersContainer.classList.add("switching");

    setTimeout(() => {
      if (viewType === "team") {
        teamsContainer.style.display = "grid";
        usersContainer.style.display = "none";
        this.updateFilterLabels("team");
        this.renderTeams();
      } else {
        teamsContainer.style.display = "none";
        usersContainer.style.display = "grid";
        this.renderUsers();
        this.updateFilterLabels("user");
      }

      // Remove switching animation
      setTimeout(() => {
        teamsContainer.classList.remove("switching");
        usersContainer.classList.remove("switching");
      }, 50);
    }, 250);

    this.currentView = viewType;
  }

  updateFilterLabels(viewType) {
    const filters = this.container.querySelectorAll(".project-filter");

    if (viewType === "user") {
      filters[0].textContent = "All Users";
    } else {
      filters[0].textContent = "All Teams";
    }
  }

  applyFilters() {
    const containers =
      this.currentView === "team"
        ? this.container.querySelectorAll(".team-card")
        : this.container.querySelectorAll(".user-card");

    containers.forEach((card) => {
      const tasks = card.querySelectorAll(".task-item");
      let hasVisibleTasks = false;

      tasks.forEach((task) => {
        let show = true;

        switch (this.currentFilter) {
          case "urgent":
            show = task.querySelector(".priority-urgent") !== null;
            break;
          case "overdue":
            show = task.classList.contains("warning-overdue");
            break;
          case "stuck":
            show = task.classList.contains("warning-stuck");
            break;
          default:
            show = true;
        }

        task.style.display = show ? "flex" : "none";
        if (show) hasVisibleTasks = true;
      });

      card.style.display = hasVisibleTasks ? "block" : "none";
    });
  }

  applySearch() {
    const containers =
      this.currentView === "team"
        ? this.container.querySelectorAll(".team-card")
        : this.container.querySelectorAll(".user-card");

    containers.forEach((card) => {
      const entityName =
        this.currentView === "team"
          ? card.querySelector(".team-name").textContent.toLowerCase()
          : card.querySelector(".user-name").textContent.toLowerCase() +
            " " +
            card.querySelector(".user-email").textContent.toLowerCase();

      const tasks = card.querySelectorAll(".task-item");
      let hasVisibleTasks = entityName.includes(this.searchQuery.toLowerCase());

      tasks.forEach((task) => {
        const taskName = task.querySelector(".task-name").textContent.toLowerCase();
        const show = taskName.includes(this.searchQuery.toLowerCase()) || this.searchQuery === "";

        task.style.display = show ? "flex" : "none";
        if (show) hasVisibleTasks = true;
      });

      card.style.display = hasVisibleTasks ? "block" : "none";
    });
  }

  // Utility methods
  getAllTasks() {
    const tasks = [];
    Object.values(this.projectData).forEach((team) => {
      tasks.push(...this.getTeamTasks(team));
    });
    return tasks;
  }

  getTeamTasks(team) {
    const tasks = [];

    if (team.folders) {
      team.folders.forEach((folder) => {
        if (folder.lists) {
          folder.lists.forEach((list) => {
            if (list.tasks) {
              tasks.push(...list.tasks);
            }
          });
        }
      });
    }

    if (team.lists) {
      team.lists.forEach((list) => {
        if (list.tasks) {
          tasks.push(...list.tasks);
        }
      });
    }

    return tasks;
  }

  isOverdue(task) {
    if (!task.due_date) return false;
    return parseInt(task.due_date) < Date.now();
  }

  getWorkloadLevel(taskCount) {
    if (taskCount <= 3) {
      return { level: "low", label: "Light" };
    } else if (taskCount <= 7) {
      return { level: "medium", label: "Moderate" };
    } else {
      return { level: "high", label: "Heavy" };
    }
  }

  // Public methods for external control
  refresh() {
    this.renderMetrics();
    this.renderContent();
  }

  updateData(newData) {
    this.projectData = newData;
    this.refresh();
  }

  setFilter(filter) {
    this.currentFilter = filter;

    // Update UI
    const filters = this.container.querySelectorAll(".project-filter");
    filters.forEach((f) => f.classList.remove("active"));
    this.container.querySelector(`[data-filter="${filter}"]`).classList.add("active");

    this.applyFilters();
  }

  setSearchQuery(query) {
    this.searchQuery = query;
    this.container.querySelector("#searchInput").value = query;
    this.applySearch();
  }
}
