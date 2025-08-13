/**
 * Dashboard Core Utilities and Shared Functions
 * Provides common functionality for all dashboard components
 */

// ===========================================
// DASHBOARD CORE UTILITIES
// ===========================================

class DashboardCore {
  static formatters = {
    // Date formatting utilities
    formatDate(timestamp, format = "short") {
      const date = new Date(parseInt(timestamp) || timestamp);

      switch (format) {
        case "short":
          return date.toLocaleDateString();
        case "long":
          return date.toLocaleDateString("en-US", {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric",
          });
        case "time":
          return date.toLocaleTimeString("en-US", {
            hour: "numeric",
            minute: "2-digit",
            hour12: true,
          });
        case "datetime":
          return date.toLocaleString();
        default:
          return date.toLocaleDateString();
      }
    },

    // Duration formatting
    formatDuration(hours) {
      if (hours < 1) {
        return `${Math.round(hours * 60)}m`;
      }
      const wholeHours = Math.floor(hours);
      const minutes = Math.round((hours - wholeHours) * 60);

      if (minutes === 0) {
        return `${wholeHours}h`;
      }
      return `${wholeHours}h ${minutes}m`;
    },

    // Number formatting
    formatNumber(num, decimals = 0) {
      return Number(num).toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      });
    },

    // Percentage formatting
    formatPercentage(value, decimals = 0) {
      return `${Number(value).toFixed(decimals)}%`;
    },
  };

  static animations = {
    // Fade in animation
    fadeIn(element, duration = 300) {
      element.style.opacity = "0";
      element.style.display = "block";

      const start = performance.now();

      function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);

        element.style.opacity = progress;

        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      }

      requestAnimationFrame(animate);
    },

    // Fade out animation
    fadeOut(element, duration = 300) {
      const start = performance.now();
      const startOpacity = parseFloat(element.style.opacity) || 1;

      function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);

        element.style.opacity = startOpacity * (1 - progress);

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          element.style.display = "none";
        }
      }

      requestAnimationFrame(animate);
    },

    // Slide animation
    slideIn(element, direction = "left", duration = 300) {
      const transforms = {
        left: "translateX(-100%)",
        right: "translateX(100%)",
        up: "translateY(-100%)",
        down: "translateY(100%)",
      };

      element.style.transform = transforms[direction];
      element.style.opacity = "0";
      element.style.display = "block";

      const start = performance.now();

      function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);

        element.style.transform = `translateX(${
          (1 - easeOut) * (direction === "left" ? -100 : direction === "right" ? 100 : 0)
        }%) translateY(${
          (1 - easeOut) * (direction === "up" ? -100 : direction === "down" ? 100 : 0)
        }%)`;
        element.style.opacity = easeOut;

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          element.style.transform = "";
        }
      }

      requestAnimationFrame(animate);
    },
    // In your DashboardController class
    loadComponents() {
      // Initialize components
      if (typeof ClickUpAnalytics !== "undefined") {
        this.components.clickup = new ClickUpAnalytics("clickup-analytics-widget");
      }

      if (typeof ProjectsTracker !== "undefined") {
        this.components.projects = new ProjectsTracker("projects-tracker-widget");
      }

      if (typeof WebflowImporter !== "undefined") {
        this.components.tools = new WebflowImporter("webflow-importer-widget");
      }
    },
    // Pulse animation for notifications
    pulse(element, intensity = 0.3, duration = 1000) {
      const originalTransform = element.style.transform;
      const start = performance.now();

      function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = (elapsed % duration) / duration;
        const scale = 1 + Math.sin(progress * Math.PI * 2) * intensity;

        element.style.transform = `${originalTransform} scale(${scale})`;

        if (elapsed < duration * 3) {
          // Pulse 3 times
          requestAnimationFrame(animate);
        } else {
          element.style.transform = originalTransform;
        }
      }

      requestAnimationFrame(animate);
    },
  };

  static storage = {
    // Local storage utilities
    set(key, value, expiration = null) {
      const item = {
        value: value,
        timestamp: Date.now(),
        expiration: expiration,
      };

      try {
        localStorage.setItem(`dashboard_${key}`, JSON.stringify(item));
        return true;
      } catch (e) {
        console.warn("Failed to save to localStorage:", e);
        return false;
      }
    },

    get(key, defaultValue = null) {
      try {
        const item = JSON.parse(localStorage.getItem(`dashboard_${key}`));

        if (!item) {
          return defaultValue;
        }

        // Check expiration
        if (item.expiration && Date.now() > item.expiration) {
          this.remove(key);
          return defaultValue;
        }

        return item.value;
      } catch (e) {
        console.warn("Failed to read from localStorage:", e);
        return defaultValue;
      }
    },

    remove(key) {
      try {
        localStorage.removeItem(`dashboard_${key}`);
        return true;
      } catch (e) {
        console.warn("Failed to remove from localStorage:", e);
        return false;
      }
    },

    // Session storage utilities
    setSession(key, value) {
      try {
        sessionStorage.setItem(`dashboard_${key}`, JSON.stringify(value));
        return true;
      } catch (e) {
        console.warn("Failed to save to sessionStorage:", e);
        return false;
      }
    },

    getSession(key, defaultValue = null) {
      try {
        const value = sessionStorage.getItem(`dashboard_${key}`);
        return value ? JSON.parse(value) : defaultValue;
      } catch (e) {
        console.warn("Failed to read from sessionStorage:", e);
        return defaultValue;
      }
    },
  };

  static notifications = {
    // Show notification
    show(message, type = "info", duration = 5000) {
      const notification = this.create(message, type);
      document.body.appendChild(notification);

      // Animate in
      DashboardCore.animations.slideIn(notification, "right");

      // Auto remove
      setTimeout(() => {
        this.remove(notification);
      }, duration);

      return notification;
    },

    create(message, type) {
      const notification = document.createElement("div");
      notification.className = `dashboard-notification notification-${type}`;

      const icons = {
        success: "✅",
        error: "❌",
        warning: "⚠️",
        info: "ℹ️",
      };

      notification.innerHTML = `
                  <div class="notification-content">
                      <span class="notification-icon">${icons[type] || icons.info}</span>
                      <span class="notification-message">${message}</span>
                      <button class="notification-close" onclick="DashboardCore.notifications.remove(this.parentElement.parentElement)">×</button>
                  </div>
              `;

      // Add styles
      Object.assign(notification.style, {
        position: "fixed",
        top: "20px",
        right: "20px",
        background:
          type === "error"
            ? "#fee2e2"
            : type === "warning"
            ? "#fef3c7"
            : type === "success"
            ? "#d1fae5"
            : "#dbeafe",
        color:
          type === "error"
            ? "#dc2626"
            : type === "warning"
            ? "#d97706"
            : type === "success"
            ? "#059669"
            : "#2563eb",
        padding: "12px 16px",
        borderRadius: "8px",
        border: `1px solid ${
          type === "error"
            ? "#fecaca"
            : type === "warning"
            ? "#fed7aa"
            : type === "success"
            ? "#a7f3d0"
            : "#bfdbfe"
        }`,
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
        zIndex: "10000",
        maxWidth: "400px",
        fontSize: "0.9rem",
      });

      return notification;
    },

    remove(notification) {
      DashboardCore.animations.fadeOut(notification, 200);
      setTimeout(() => {
        if (notification.parentElement) {
          notification.parentElement.removeChild(notification);
        }
      }, 200);
    },
  };

  static api = {
    // Simple API wrapper with error handling
    async request(url, options = {}) {
      const defaultOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      };

      const mergedOptions = { ...defaultOptions, ...options };

      try {
        const response = await fetch(url, mergedOptions);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          return await response.json();
        }

        return await response.text();
      } catch (error) {
        console.error("API Request failed:", error);
        throw error;
      }
    },

    // GET request
    async get(url, params = {}) {
      const urlParams = new URLSearchParams(params);
      const fullUrl = urlParams.toString() ? `${url}?${urlParams}` : url;

      return this.request(fullUrl);
    },

    // POST request
    async post(url, data = {}) {
      return this.request(url, {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    // PUT request
    async put(url, data = {}) {
      return this.request(url, {
        method: "PUT",
        body: JSON.stringify(data),
      });
    },

    // DELETE request
    async delete(url) {
      return this.request(url, {
        method: "DELETE",
      });
    },
  };

  static events = {
    // Event emitter for component communication
    listeners: new Map(),

    on(event, callback) {
      if (!this.listeners.has(event)) {
        this.listeners.set(event, []);
      }
      this.listeners.get(event).push(callback);
    },

    off(event, callback) {
      if (this.listeners.has(event)) {
        const callbacks = this.listeners.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    },

    emit(event, data = null) {
      if (this.listeners.has(event)) {
        this.listeners.get(event).forEach((callback) => {
          try {
            callback(data);
          } catch (error) {
            console.error(`Error in event callback for ${event}:`, error);
          }
        });
      }
    },
  };

  static utils = {
    // Generate unique ID
    generateId() {
      return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    // Debounce function
    debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },

    // Throttle function
    throttle(func, limit) {
      let lastFunc;
      let lastRan;
      return function (...args) {
        if (!lastRan) {
          func(...args);
          lastRan = Date.now();
        } else {
          clearTimeout(lastFunc);
          lastFunc = setTimeout(() => {
            if (Date.now() - lastRan >= limit) {
              func(...args);
              lastRan = Date.now();
            }
          }, limit - (Date.now() - lastRan));
        }
      };
    },

    // Deep clone object
    deepClone(obj) {
      if (obj === null || typeof obj !== "object") {
        return obj;
      }

      if (obj instanceof Date) {
        return new Date(obj.getTime());
      }

      if (obj instanceof Array) {
        return obj.map((item) => this.deepClone(item));
      }

      if (typeof obj === "object") {
        const clonedObj = {};
        for (let key in obj) {
          if (obj.hasOwnProperty(key)) {
            clonedObj[key] = this.deepClone(obj[key]);
          }
        }
        return clonedObj;
      }
    },

    // Check if element is in viewport
    isInViewport(element) {
      const rect = element.getBoundingClientRect();
      return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
      );
    },

    // Smooth scroll to element
    scrollToElement(element, offset = 0, duration = 500) {
      const targetPosition = element.offsetTop - offset;
      const startPosition = window.pageYOffset;
      const distance = targetPosition - startPosition;
      let startTime = null;

      function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = this.easeInOutQuad(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
      }

      requestAnimationFrame(animation);
    },

    // Easing function
    easeInOutQuad(t, b, c, d) {
      t /= d / 2;
      if (t < 1) return (c / 2) * t * t + b;
      t--;
      return (-c / 2) * (t * (t - 2) - 1) + b;
    },
  };

  // Color utilities for dynamic theming
  static colors = {
    // Generate color variations
    lighten(color, amount) {
      const num = parseInt(color.replace("#", ""), 16);
      const amt = Math.round(2.55 * amount);
      const R = (num >> 16) + amt;
      const G = ((num >> 8) & 0x00ff) + amt;
      const B = (num & 0x0000ff) + amt;

      return (
        "#" +
        (
          0x1000000 +
          (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
          (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
          (B < 255 ? (B < 1 ? 0 : B) : 255)
        )
          .toString(16)
          .slice(1)
      );
    },

    darken(color, amount) {
      return this.lighten(color, -amount);
    },

    // Convert hex to rgba
    hexToRgba(hex, alpha = 1) {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);

      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    },

    // Get contrast color (black or white)
    getContrastColor(hexcolor) {
      const r = parseInt(hexcolor.substr(1, 2), 16);
      const g = parseInt(hexcolor.substr(3, 2), 16);
      const b = parseInt(hexcolor.substr(5, 2), 16);
      const brightness = (r * 299 + g * 587 + b * 114) / 1000;

      return brightness > 155 ? "#000000" : "#ffffff";
    },
  };
}

// ===========================================
// COMPONENT BASE CLASS
// ===========================================

class DashboardComponent {
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    this.options = { ...this.defaultOptions, ...options };
    this.isDestroyed = false;
    this.eventListeners = [];

    if (!this.container) {
      throw new Error(`Container element with ID "${containerId}" not found`);
    }
  }

  get defaultOptions() {
    return {
      autoRefresh: false,
      refreshInterval: 30000,
      debug: false,
    };
  }

  // Add event listener with cleanup tracking
  addEventListener(element, event, handler, options = {}) {
    element.addEventListener(event, handler, options);
    this.eventListeners.push({ element, event, handler, options });
  }

  // Emit component events
  emit(eventName, data = null) {
    DashboardCore.events.emit(`${this.constructor.name}.${eventName}`, {
      component: this,
      data: data,
    });
  }

  // Listen to component events
  on(eventName, callback) {
    DashboardCore.events.on(`${this.constructor.name}.${eventName}`, callback);
  }

  // Show loading state
  showLoading(message = "Loading...") {
    const loader = document.createElement("div");
    loader.className = "component-loader";
    loader.innerHTML = `
              <div class="loader-content">
                  <div class="loader-spinner"></div>
                  <div class="loader-message">${message}</div>
              </div>
          `;

    // Add styles
    Object.assign(loader.style, {
      position: "absolute",
      top: "0",
      left: "0",
      right: "0",
      bottom: "0",
      background: "rgba(15, 23, 42, 0.8)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: "100",
      borderRadius: "12px",
    });

    this.container.style.position = "relative";
    this.container.appendChild(loader);

    return loader;
  }

  // Hide loading state
  hideLoading() {
    const loader = this.container.querySelector(".component-loader");
    if (loader) {
      DashboardCore.animations.fadeOut(loader, 200);
      setTimeout(() => {
        if (loader.parentElement) {
          loader.parentElement.removeChild(loader);
        }
      }, 200);
    }
  }

  // Show error state
  showError(message, retry = null) {
    const error = document.createElement("div");
    error.className = "component-error";
    error.innerHTML = `
              <div class="error-content">
                  <div class="error-icon">⚠️</div>
                  <div class="error-message">${message}</div>
                  ${retry ? '<button class="error-retry">Retry</button>' : ""}
              </div>
          `;

    if (retry) {
      error.querySelector(".error-retry").addEventListener("click", retry);
    }

    this.container.innerHTML = "";
    this.container.appendChild(error);
  }

  // Cleanup component
  destroy() {
    this.isDestroyed = true;

    // Remove all event listeners
    this.eventListeners.forEach(({ element, event, handler, options }) => {
      element.removeEventListener(event, handler, options);
    });
    this.eventListeners = [];

    // Stop auto refresh
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }

    // Clear container
    if (this.container) {
      this.container.innerHTML = "";
    }

    this.emit("destroyed");
  }

  // Debug logging
  debug(...args) {
    if (this.options.debug) {
      console.log(`[${this.constructor.name}]`, ...args);
    }
  }
}

// ===========================================
// GLOBAL INITIALIZATION
// ===========================================

// Add global styles for notifications and loaders
const globalStyles = document.createElement("style");
globalStyles.textContent = `
      .notification-content {
          display: flex;
          align-items: center;
          gap: 8px;
      }
      
      .notification-close {
          background: none;
          border: none;
          font-size: 1.2rem;
          cursor: pointer;
          opacity: 0.7;
          margin-left: auto;
      }
      
      .notification-close:hover {
          opacity: 1;
      }
      
      .loader-content {
          text-align: center;
          color: #e2e8f0;
      }
      
      .loader-spinner {
          width: 32px;
          height: 32px;
          border: 3px solid #334155;
          border-top: 3px solid #6366f1;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 12px;
      }
      
      .loader-message {
          font-size: 0.9rem;
          color: #94a3b8;
      }
      
      @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
      }
      
      .error-content {
          text-align: center;
          padding: 40px 20px;
          color: #64748b;
      }
      
      .error-icon {
          font-size: 3rem;
          margin-bottom: 16px;
      }
      
      .error-message {
          font-size: 1rem;
          margin-bottom: 16px;
          color: #94a3b8;
      }
      
      .error-retry {
          background: #6366f1;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          cursor: pointer;
          transition: background-color 0.2s;
      }
      
      .error-retry:hover {
          background: #5856eb;
      }
  `;

document.head.appendChild(globalStyles);

// Export for use in other components
window.DashboardCore = DashboardCore;
window.DashboardComponent = DashboardComponent;
