// GlobalCalendarPicker.js - Using CSS Classes
const GlobalCalendarPicker = ({
  selectedDate = new Date(),
  onDateSelect = () => {},
  onClose = () => {},
  isOpen = true,
}) => {
  const [currentDate, setCurrentDate] = React.useState(new Date(selectedDate));

  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const today = new Date();

  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      const prevMonthDay = new Date(year, month, -startingDayOfWeek + i + 1);
      days.push({
        date: prevMonthDay,
        isCurrentMonth: false,
        isPrevMonth: true,
      });
    }

    // Add days of the current month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push({
        date: new Date(year, month, day),
        isCurrentMonth: true,
        isPrevMonth: false,
      });
    }

    // Add days from next month to fill the grid
    const remainingCells = 42 - days.length; // 6 rows × 7 days
    for (let day = 1; day <= remainingCells; day++) {
      days.push({
        date: new Date(year, month + 1, day),
        isCurrentMonth: false,
        isPrevMonth: false,
      });
    }

    return days;
  };

  const navigateMonth = (direction) => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev);
      newDate.setMonth(prev.getMonth() + direction);
      return newDate;
    });
  };

  const handleDateClick = (date) => {
    onDateSelect(date);
  };

  const isSelectedDate = (date) => {
    return (
      selectedDate &&
      date.getDate() === selectedDate.getDate() &&
      date.getMonth() === selectedDate.getMonth() &&
      date.getFullYear() === selectedDate.getFullYear()
    );
  };

  const isToday = (date) => {
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const handleTodayClick = () => {
    const todayDate = new Date();
    setCurrentDate(todayDate);
    onDateSelect(todayDate);
  };

  const handleClearClick = () => {
    onDateSelect(null);
  };

  const days = getDaysInMonth(currentDate);

  if (!isOpen) return null;

  return React.createElement(
    "div",
    {
      className: "calendar-picker-overlay",
    },
    React.createElement(
      "div",
      {
        className: "calendar-picker-container",
      },
      // Header
      React.createElement(
        "div",
        {
          className: "calendar-picker-header",
        },
        React.createElement(
          "div",
          {
            className: "calendar-picker-title",
          },
          React.createElement(
            "div",
            {
              className: "calendar-picker-icon",
            },
            "📅"
          ),
          React.createElement(
            "h2",
            {
              className: "calendar-picker-heading",
            },
            "Select Date"
          )
        ),
        React.createElement(
          "button",
          {
            onClick: onClose,
            className: "calendar-picker-close",
          },
          "×"
        )
      ),

      // Month Navigation
      React.createElement(
        "div",
        {
          className: "calendar-picker-nav",
        },
        React.createElement(
          "button",
          {
            onClick: () => navigateMonth(-1),
            className: "calendar-picker-nav-btn",
          },
          "‹"
        ),

        React.createElement(
          "div",
          {
            className: "calendar-picker-month-year",
          },
          `${months[currentDate.getMonth()]} ${currentDate.getFullYear()}`
        ),

        React.createElement(
          "button",
          {
            onClick: () => navigateMonth(1),
            className: "calendar-picker-nav-btn",
          },
          "›"
        )
      ),

      // Days of Week
      React.createElement(
        "div",
        {
          className: "calendar-picker-weekdays",
        },
        ...daysOfWeek.map((day) =>
          React.createElement(
            "div",
            {
              key: day,
              className: "calendar-picker-weekday",
            },
            day
          )
        )
      ),

      // Calendar Grid
      React.createElement(
        "div",
        {
          className: "calendar-picker-grid",
        },
        ...days.map((dayObj, index) => {
          const { date, isCurrentMonth } = dayObj;
          const selected = isSelectedDate(date);
          const todayDate = isToday(date);

          let dayClasses = "calendar-picker-day";

          if (!isCurrentMonth) {
            dayClasses += " other-month";
          }

          if (selected) {
            dayClasses += " selected";
          } else if (todayDate) {
            dayClasses += " today";
          }

          return React.createElement(
            "button",
            {
              key: index,
              onClick: () => handleDateClick(date),
              className: dayClasses,
            },
            date.getDate()
          );
        })
      ),

      // Action Buttons
      React.createElement(
        "div",
        {
          className: "calendar-picker-actions",
        },
        React.createElement(
          "button",
          {
            onClick: handleClearClick,
            className: "calendar-picker-btn clear",
          },
          "Clear"
        ),

        React.createElement(
          "button",
          {
            onClick: handleTodayClick,
            className: "calendar-picker-btn today",
          },
          "Today"
        )
      )
    )
  );
};

// Make it globally accessible
window.GlobalCalendarPicker = GlobalCalendarPicker;
