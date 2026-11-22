// Auto-refresh: any element with a data-refresh-url attribute
// is reloaded from that URL every few seconds.
(function () {
  const REFRESH_MS = 4000;

  document.querySelectorAll("[data-refresh-url]").forEach(function (box) {
    const url = box.dataset.refreshUrl;
    let lastHtml = box.innerHTML;

    setInterval(async function () {
      if (document.hidden) return;              // don't poll while the tab is hidden
      try {
        const response = await fetch(url);
        if (response.redirected) {              // session ended: go to the login page
          window.location.reload();
          return;
        }
        if (!response.ok) return;
        const html = await response.text();
        if (html !== lastHtml) {                // only touch the page if something changed
          box.innerHTML = html;
          lastHtml = html;
        }
      } catch (error) {
        // server unreachable: keep the old content and try again next time
      }
    }, REFRESH_MS);
  });
})();
