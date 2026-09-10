// Cape Institute for Safe AI — minimal interactions
document.addEventListener("DOMContentLoaded", function () {
  var header = document.querySelector(".site-header");
  var inner = document.querySelector(".site-header__inner");
  var logo = document.querySelector(".logo-link");
  var toggle = document.getElementById("nav-toggle");
  var nav = document.getElementById("site-nav");

  // Collapse the nav into the hamburger menu based on measured overflow
  // (i.e. as soon as the tabs would actually start being pushed off
  // screen), rather than a guessed, fixed viewport breakpoint.
  function updateNavCollapse() {
    if (!header || !inner || !logo || !nav) return;

    // Measure against the uncollapsed (full desktop) layout first.
    header.classList.remove("nav-collapsed");
    document.body.classList.remove("nav-collapsed");

    var available = inner.clientWidth;
    var needed = logo.getBoundingClientRect().width + nav.scrollWidth;

    if (needed > available) {
      header.classList.add("nav-collapsed");
      document.body.classList.add("nav-collapsed");
    }
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  updateNavCollapse();

  // Only re-evaluate on width changes. On mobile, scrolling causes the
  // browser address bar to show/hide, which fires resize with a changed
  // height but the same width. Running updateNavCollapse then briefly
  // removes nav-collapsed to remeasure, causing the menu to flash open.
  var lastWidth = window.innerWidth;
  window.addEventListener("resize", function () {
    var currentWidth = window.innerWidth;
    if (currentWidth !== lastWidth) {
      lastWidth = currentWidth;
      updateNavCollapse();
    }
  });

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(updateNavCollapse);
  }

  var yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  // Defined-term popups (d/acc, Schelling point)
  function initTermPopup(termSelector, popupId, backdropId) {
    var popup    = document.getElementById(popupId);
    var backdrop = document.getElementById(backdropId);
    if (!popup || !backdrop) return;

    function open() {
      popup.hidden    = false;
      backdrop.hidden = false;
      popup.focus();
    }

    function close() {
      popup.hidden    = true;
      backdrop.hidden = true;
    }

    document.querySelectorAll(termSelector).forEach(function (el) {
      el.addEventListener("click", function (e) {
        e.preventDefault();
        open();
      });
    });

    backdrop.addEventListener("click", close);

    var closeBtn = popup.querySelector(".term-popup__close");
    if (closeBtn) closeBtn.addEventListener("click", close);

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
  }

  initTermPopup("abbr.dacc-term", "dacc-popup", "dacc-backdrop");
  initTermPopup("abbr.schelling-term", "schelling-popup", "schelling-backdrop");

  // Mark the current page's tab. Sub-pages under the Capacity Building
  // dropdown (programs, events) light up the parent tab.
  (function markActiveNav() {
    if (!nav) return;
    var file = (location.pathname.split("/").pop() || "index.html").toLowerCase();
    var parentOf = { "programs.html": "capacity-building.html", "events.html": "capacity-building.html" };
    var target = parentOf[file] || file;
    nav.querySelectorAll(":scope > a, .nav-item > a").forEach(function (link) {
      var raw = link.getAttribute("href") || "";
      // "#about" on the homepage is a same-page anchor, i.e. index.html
      var href = (raw.charAt(0) === "#" ? "index.html" : raw.split("#")[0]).toLowerCase();
      if (href === target) link.classList.add("is-active");
    });
  })();

  // Program cards: clamped descriptions get a "Read more" toggle, but only
  // when the text actually overflows its four-line clamp.
  function initCardToggles() {
    document.querySelectorAll("[data-card-more]").forEach(function (button) {
      var text = button.previousElementSibling;
      if (!text || !text.classList.contains("card__text--clamp")) return;
      var overflows = text.scrollHeight > text.clientHeight + 1;
      if (!overflows && !text.classList.contains("is-expanded")) {
        button.hidden = true;
        return;
      }
      button.hidden = false;
      if (button.dataset.bound) return;
      button.dataset.bound = "1";
      button.addEventListener("click", function () {
        var expanded = text.classList.toggle("is-expanded");
        button.setAttribute("aria-expanded", expanded ? "true" : "false");
        button.innerHTML = (expanded ? "Show less" : "Read more") + ' <span class="arrow">&darr;</span>';
      });
    });
  }

  initCardToggles();
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(initCardToggles);
  }

  // Event archive: reveal the next batch of hidden rows per click.
  document.querySelectorAll("[data-archive-more]").forEach(function (button) {
    var step = parseInt(button.getAttribute("data-archive-step"), 10) || 10;
    var shell = button.closest(".archive-more").previousElementSibling;
    var count = button.parentElement.querySelector("[data-archive-count]");
    var all = shell ? shell.querySelectorAll(".archive-row") : [];

    function update() {
      var hidden = shell.querySelectorAll(".archive-row.is-hidden");
      if (count) count.textContent = (all.length - hidden.length) + " of " + all.length;
      if (!hidden.length) button.hidden = true;
    }

    button.addEventListener("click", function () {
      shell.querySelectorAll(".archive-row.is-hidden").forEach(function (row, i) {
        if (i < step) row.classList.remove("is-hidden");
      });
      update();
    });

    update();
  });

});
