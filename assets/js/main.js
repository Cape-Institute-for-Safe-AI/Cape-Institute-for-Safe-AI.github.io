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

    var available = inner.clientWidth;
    var needed = logo.getBoundingClientRect().width + nav.scrollWidth;

    if (needed > available) {
      header.classList.add("nav-collapsed");
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

  // Play-once GIFs: start the animation only once scrolled into view,
  // then freeze on the final frame after it completes a single loop.
  var playOnceGifs = document.querySelectorAll("[data-gif-src]");
  if (playOnceGifs.length && "IntersectionObserver" in window) {
    var gifObserver = new IntersectionObserver(
      function (entries, observer) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;

          var img = entry.target;
          var gifSrc = img.getAttribute("data-gif-src");
          var freezeSrc = img.getAttribute("data-freeze-src");
          var duration = parseInt(img.getAttribute("data-gif-duration"), 10) || 10000;

          // Preload the freeze frame ahead of time so the swap is instant
          // (no blank gap while the browser fetches/decodes it).
          var preloadedFreeze = null;
          if (freezeSrc) {
            preloadedFreeze = new Image();
            preloadedFreeze.src = freezeSrc;
          }

          // Time the countdown from when the GIF has actually loaded and
          // started rendering, not from when we merely set `src` — network
          // + decode latency otherwise makes the freeze-frame swap land
          // mid-animation instead of after it truly completes.
          var startTimer = function () {
            window.setTimeout(function () {
              if (freezeSrc) {
                img.src = freezeSrc;
              }
            }, duration);
          };

          img.addEventListener(
            "load",
            function () {
              startTimer();
            },
            { once: true }
          );

          img.src = gifSrc;

          observer.unobserve(img);
        });
      },
      { threshold: 0.25 }
    );

    playOnceGifs.forEach(function (img) {
      gifObserver.observe(img);
    });
  }
});
