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
  window.addEventListener("resize", updateNavCollapse);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(updateNavCollapse);
  }

  var yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  // d/acc definition popup
  var popup   = document.getElementById("dacc-popup");
  var backdrop = document.getElementById("dacc-backdrop");

  function openDacc() {
    if (!popup) return;
    popup.hidden   = false;
    backdrop.hidden = false;
    popup.focus();
  }

  function closeDacc() {
    if (!popup) return;
    popup.hidden   = true;
    backdrop.hidden = true;
  }

  document.querySelectorAll("abbr.dacc-term").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      openDacc();
    });
  });

  if (backdrop) backdrop.addEventListener("click", closeDacc);

  var closeBtn = document.querySelector(".dacc-popup__close");
  if (closeBtn) closeBtn.addEventListener("click", closeDacc);

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeDacc();
  });

});
