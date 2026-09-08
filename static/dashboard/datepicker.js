(function () {
  const MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
  ];
  const MONTHS_SHORT = [
    "янв", "фев", "мар", "апр", "мая", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек"
  ];
  const WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

  function parseISO(value) {
    if (!value) return null;
    const parts = value.split("-").map(Number);
    if (parts.length !== 3 || parts.some(function (n) { return !n; })) return null;
    return new Date(parts[0], parts[1] - 1, parts[2]);
  }

  function toISO(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + d;
  }

  function formatRu(date) {
    return date.getDate() + " " + MONTHS_SHORT[date.getMonth()] + " " + date.getFullYear();
  }

  function sameDay(a, b) {
    return a && b &&
      a.getFullYear() === b.getFullYear() &&
      a.getMonth() === b.getMonth() &&
      a.getDate() === b.getDate();
  }

  function startOfCalendar(view) {
    const first = new Date(view.getFullYear(), view.getMonth(), 1);
    const weekday = (first.getDay() + 6) % 7;
    first.setDate(first.getDate() - weekday);
    return first;
  }

  let openChip = null;

  function closePicker() {
    if (!openChip) return;
    const pop = openChip.querySelector(".datepicker");
    if (pop) pop.remove();
    openChip.classList.remove("is-open");
    const trigger = openChip.querySelector(".date-chip-trigger");
    if (trigger) trigger.setAttribute("aria-expanded", "false");
    openChip = null;
  }

  function syncValue(chip, input) {
    const valueEl = chip.querySelector(".date-chip-value");
    const date = parseISO(input.value);
    if (!valueEl) return;
    valueEl.textContent = date ? formatRu(date) : "выберите дату";
    valueEl.classList.toggle("is-placeholder", !date);
  }

  function renderCalendar(chip, input, viewDate) {
    const existing = chip.querySelector(".datepicker");
    if (existing) existing.remove();

    const selected = parseISO(input.value);
    const today = new Date();
    const pop = document.createElement("div");
    pop.className = "datepicker";
    pop.setAttribute("role", "dialog");
    pop.setAttribute("aria-label", "Календарь");

    const head = document.createElement("div");
    head.className = "datepicker-head";

    const prev = document.createElement("button");
    prev.type = "button";
    prev.className = "datepicker-nav";
    prev.setAttribute("aria-label", "Предыдущий месяц");
    prev.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    const title = document.createElement("div");
    title.className = "datepicker-title";
    title.textContent = MONTHS[viewDate.getMonth()] + " " + viewDate.getFullYear();

    const next = document.createElement("button");
    next.type = "button";
    next.className = "datepicker-nav";
    next.setAttribute("aria-label", "Следующий месяц");
    next.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    head.append(prev, title, next);

    const week = document.createElement("div");
    week.className = "datepicker-week";
    WEEK.forEach(function (label) {
      const span = document.createElement("span");
      span.textContent = label;
      week.appendChild(span);
    });

    const grid = document.createElement("div");
    grid.className = "datepicker-grid";
    let cursor = startOfCalendar(viewDate);
    for (let i = 0; i < 42; i += 1) {
      const cellDate = new Date(cursor);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "datepicker-day";
      btn.textContent = String(cellDate.getDate());
      if (cellDate.getMonth() !== viewDate.getMonth()) btn.classList.add("is-muted");
      if (sameDay(cellDate, today)) btn.classList.add("is-today");
      if (sameDay(cellDate, selected)) btn.classList.add("is-selected");
      btn.addEventListener("click", function () {
        input.value = toISO(cellDate);
        input.dispatchEvent(new Event("change", { bubbles: true }));
        syncValue(chip, input);
        closePicker();
      });
      grid.appendChild(btn);
      cursor.setDate(cursor.getDate() + 1);
    }

    const foot = document.createElement("div");
    foot.className = "datepicker-foot";
    const clear = document.createElement("button");
    clear.type = "button";
    clear.className = "datepicker-clear";
    clear.textContent = "Сбросить";
    clear.addEventListener("click", function () {
      input.value = "";
      input.dispatchEvent(new Event("change", { bubbles: true }));
      syncValue(chip, input);
      closePicker();
    });
    const todayBtn = document.createElement("button");
    todayBtn.type = "button";
    todayBtn.className = "datepicker-today";
    todayBtn.textContent = "Сегодня";
    todayBtn.addEventListener("click", function () {
      input.value = toISO(today);
      input.dispatchEvent(new Event("change", { bubbles: true }));
      syncValue(chip, input);
      closePicker();
    });
    foot.append(clear, todayBtn);

    pop.append(head, week, grid, foot);
    chip.appendChild(pop);

    prev.addEventListener("click", function (event) {
      event.stopPropagation();
      renderCalendar(chip, input, new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1));
    });
    next.addEventListener("click", function (event) {
      event.stopPropagation();
      renderCalendar(chip, input, new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1));
    });
  }

  function openPicker(chip, input) {
    if (openChip === chip) {
      closePicker();
      return;
    }
    closePicker();
    chip.classList.add("is-open");
    const trigger = chip.querySelector(".date-chip-trigger");
    if (trigger) trigger.setAttribute("aria-expanded", "true");
    const view = parseISO(input.value) || new Date();
    renderCalendar(chip, input, view);
    openChip = chip;
  }

  function enhance(chip) {
    const input = chip.querySelector('input[type="date"]');
    if (!input || chip.dataset.enhanced) return;
    chip.dataset.enhanced = "1";
    chip.classList.add("date-chip--custom");

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "date-chip-trigger";
    trigger.setAttribute("aria-haspopup", "dialog");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-label", input.getAttribute("aria-label") || "Дата");

    const valueEl = document.createElement("span");
    valueEl.className = "date-chip-value";
    const caret = document.createElement("span");
    caret.className = "date-chip-caret";
    caret.setAttribute("aria-hidden", "true");
    caret.innerHTML = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    input.insertAdjacentElement("afterend", trigger);
    trigger.append(valueEl, caret);
    syncValue(chip, input);

    trigger.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      openPicker(chip, input);
    });
    chip.addEventListener("click", function (event) {
      if (event.target.closest(".datepicker, .date-chip-trigger")) return;
      openPicker(chip, input);
    });
  }

  document.addEventListener("mousedown", function (event) {
    if (openChip && !openChip.contains(event.target)) closePicker();
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closePicker();
  });

  document.querySelectorAll(".date-chip").forEach(enhance);
})();
