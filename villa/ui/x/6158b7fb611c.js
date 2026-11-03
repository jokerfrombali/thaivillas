
(function() {
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  let baseDate = new Date();
  let startDate = null;
  let endDate = null;

  function renderCalendars() {
    document.querySelectorAll('.calendar-month').forEach((container, idx) => {
      const offset = parseInt(container.dataset.monthOffset) || idx;
      const date = new Date(baseDate.getFullYear(), baseDate.getMonth() + offset, 1);
      const titleEl = container.querySelector('.month-title');
      if (titleEl) titleEl.textContent = months[date.getMonth()] + ' ' + date.getFullYear();

      const grid = container.querySelector('.calendar-grid');
      if (!grid) return;
      grid.innerHTML = '';

      const firstDay = date.getDay();
      const daysInMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
      const today = new Date();
      today.setHours(0,0,0,0);

      for (let i = 0; i < firstDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'calendar-day empty';
        grid.appendChild(empty);
      }

      for (let day = 1; day <= daysInMonth; day++) {
        const dayDate = new Date(date.getFullYear(), date.getMonth(), day);
        const cell = document.createElement('div');
        cell.className = 'calendar-day';
        cell.textContent = day;

        if (dayDate < today) {
          cell.classList.add('disabled');
        } else {
          cell.onclick = () => selectDate(dayDate);
        }

        if (dayDate.toDateString() === today.toDateString()) {
          cell.classList.add('today');
        }

        if (startDate && dayDate.toDateString() === startDate.toDateString()) {
          cell.classList.add('selected', 'range-start');
        }
        if (endDate && dayDate.toDateString() === endDate.toDateString()) {
          cell.classList.add('selected', 'range-end');
        }
        if (startDate && endDate && dayDate > startDate && dayDate < endDate) {
          cell.classList.add('in-range');
        }

        grid.appendChild(cell);
      }
    });
  }

  function selectDate(date) {
    if (!startDate || (startDate && endDate)) {
      startDate = date;
      endDate = null;
    } else if (date > startDate) {
      endDate = date;
    } else {
      startDate = date;
      endDate = null;
    }
    renderCalendars();
    updateDateDisplay();
    updateBookingForm();
  }

  function updateDateDisplay() {
    const el = document.getElementById('selectedDateRange');
    if (!el) return;
    if (startDate && endDate) {
      const opts = { month: 'short', day: 'numeric', year: 'numeric' };
      el.textContent = startDate.toLocaleDateString('en-US', opts) + ' ~ ' + endDate.toLocaleDateString('en-US', opts);
    } else if (startDate) {
      el.textContent = 'Select check-out date';
    } else {
      el.textContent = 'Select your dates';
    }
  }

  function updateBookingForm() {
    const checkInEl = document.getElementById('bookingCheckIn');
    const checkOutEl = document.getElementById('bookingCheckOut');
    const opts = { month: 'short', day: 'numeric' };

    // Update sidebar form
    document.querySelectorAll('div').forEach(div => {
      if (div.textContent.trim() === 'Add date' && startDate) {
        const parent = div.closest('[class*="border"]');
        if (parent) {
          const siblings = parent.parentElement.querySelectorAll('div');
          let count = 0;
          siblings.forEach(s => {
            if (s.textContent.trim() === 'Add date' || s.textContent.match(/^[A-Z][a-z]{2} \d+$/)) {
              count++;
              if (count === 1 && startDate) {
                s.textContent = startDate.toLocaleDateString('en-US', opts);
              } else if (count === 2 && endDate) {
                s.textContent = endDate.toLocaleDateString('en-US', opts);
              }
            }
          });
        }
      }
    });
  }

  window.prevMonth = function(idx) {
    const now = new Date();
    const prev = new Date(baseDate.getFullYear(), baseDate.getMonth() - 1, 1);
    if (prev < new Date(now.getFullYear(), now.getMonth(), 1)) return;
    baseDate = prev;
    renderCalendars();
  };

  window.nextMonth = function(idx) {
    baseDate = new Date(baseDate.getFullYear(), baseDate.getMonth() + 1, 1);
    renderCalendars();
  };

  window.renderCalendars = renderCalendars;
  window.thbGetDates = function () { return { start: startDate, end: endDate }; };

  /* Даты, выбранные в каталоге, приходят в адресе (?checkin=&checkout=).
     Гость отфильтровал выдачу по датам и открыл виллу — на странице виллы они
     должны быть уже выбраны, иначе он выбирает их второй раз. Ставит их
     thb-avail.js, когда календарь отрисован. */
  window.thbSetDates = function (a, b) {
    var p = String(a || '').split('-'), q = String(b || '').split('-');
    if (p.length !== 3 || q.length !== 3) return false;
    var s = new Date(+p[0], +p[1] - 1, +p[2]), e = new Date(+q[0], +q[1] - 1, +q[2]);
    if (isNaN(s) || isNaN(e) || e <= s) return false;
    startDate = s; endDate = e;
    baseDate = new Date(s.getFullYear(), s.getMonth(), 1);
    renderCalendars();
    updateDateDisplay();
    updateBookingForm();
    return true;
  };

  window.clearDates = function() {
    startDate = null;
    endDate = null;
    renderCalendars();
    updateDateDisplay();
  };

  // Initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderCalendars);
  } else {
    renderCalendars();
  }
})();
