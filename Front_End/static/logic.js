// Customer cart and order panels use AJAX, with a normal form fallback.
(function () {
  const REFRESH_MS = 4000;

  async function refreshBox(box) {
    try {
      const response = await fetch(box.dataset.refreshUrl, { headers: { "X-Requested-With": "fetch" } });
      if (response.redirected) { window.location.href = response.url; return; }
      if (!response.ok) return;
      const html = await response.text();
      if (html !== box.dataset.lastHtml) {
        box.innerHTML = html;
        box.dataset.lastHtml = html;
      }
    } catch (_) { /* leave existing content visible if offline */ }
  }

  document.querySelectorAll("[data-refresh-url]").forEach(function (box) {
    box.dataset.lastHtml = box.innerHTML;
    setInterval(function () {
      if (!document.hidden) refreshBox(box);
    }, REFRESH_MS);
  });

  document.addEventListener("submit", async function (event) {
    const form = event.target.closest("form[data-ajax]");
    if (!form) return;
    event.preventDefault();

    // If the cart panel isn't on this page, let the browser submit normally.
    const cartBox = document.querySelector("[data-cart-box]");
    if (!cartBox) { form.removeAttribute("data-ajax"); form.submit(); return; }

    const submitButton = form.querySelector('button[type="submit"], button:not([type])');
    if (submitButton) { submitButton.disabled = true; submitButton.dataset.originalText = submitButton.textContent; }

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "fetch" },
      });
      if (response.redirected) { window.location.href = response.url; return; }
      if (!response.ok) {
        const body = await response.text();
        // Show server error instead of silently doing nothing.
        cartBox.innerHTML = '<div class="flash">Cart update failed (' + response.status + '). Please refresh and try again.</div>' + cartBox.innerHTML;
        console.error("Redplate cart request failed:", response.status, body);
        return;
      }
      const html = await response.text();
      cartBox.innerHTML = html;
      cartBox.dataset.lastHtml = html;
      document.querySelectorAll("[data-refresh-url]:not([data-cart-box])").forEach(refreshBox);
    } catch (error) {
      console.error("Redplate cart request error:", error);
      form.removeAttribute("data-ajax");
      form.submit(); // fallback to normal navigation so errors/results are visible
    } finally {
      if (submitButton && submitButton.isConnected) submitButton.disabled = false;
    }
  });
})();