// 1) Auto-refresh: any element with a data-refresh-url attribute
//    is reloaded from that URL every few seconds.
// 2) Forms marked data-ajax are sent without leaving the page: the server answers with the
//    new cart box, which replaces the old one (no page reload, no jump to the top).
(function () {
  const REFRESH_MS = 4000;

  async function refreshBox(box) {
    try {
      const response = await fetch(box.dataset.refreshUrl);
      if (response.redirected) {                // session ended: go to the login page
        window.location.reload();
        return;
      }
      if (!response.ok) return;
      const html = await response.text();
      if (html !== box.dataset.lastHtml) {      // only touch the page if something changed
        box.innerHTML = html;
        box.dataset.lastHtml = html;
      }
    } catch (error) {
      // server unreachable: keep the old content and try again next time
    }
  }

  document.querySelectorAll("[data-refresh-url]").forEach(function (box) {
    box.dataset.lastHtml = box.innerHTML;
    setInterval(function () {
      if (!document.hidden) refreshBox(box);    // don't poll while the tab is hidden
    }, REFRESH_MS);
  });

  document.addEventListener("submit", async function (event) {
    const form = event.target;
    if (!form.hasAttribute("data-ajax")) return;
    event.preventDefault();
    const cartBox = document.querySelector("[data-cart-box]");
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "fetch" },
      });
      if (response.redirected) {                // not signed in any more
        window.location.href = response.url;
        return;
      }
      if (response.ok && cartBox) cartBox.innerHTML = await response.text();
    } catch (error) {
      form.submit();                            // fall back to a normal page load
      return;
    }
    document.querySelectorAll("[data-refresh-url]").forEach(refreshBox);   // new order shows up now
  });
})();
