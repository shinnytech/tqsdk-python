/* Progressive enhancements. Navigation and document content work without JS. */
document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  const searchInput = document.querySelector("#tq-search-input");
  const searchPageInput = document.querySelector("#tq-search-page-input");
  const toggle = document.querySelector(".tq-menu-toggle");
  const sidebar = document.querySelector(".wy-nav-side");
  const mobile = window.matchMedia("(max-width: 768px)");
  const query = new URLSearchParams(window.location.search).get("q");
  if (query) [searchInput, searchPageInput].forEach(input => { if (input) input.value = query; });
  document.addEventListener("keydown", event => {
    const target = event.target;
    const editing = target instanceof HTMLElement && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName));
    // Sphinx also handles '/', but cannot focus an input inside a closed drawer.
    if (event.key === "/" && !editing && !event.isComposing && !event.ctrlKey && !event.metaKey && !event.altKey) {
      const input = searchPageInput || searchInput;
      if (!input) return;
      event.preventDefault();
      // Open the mobile drawer before focusing its otherwise inert search field.
      if (input === searchInput && mobile.matches && sidebar && !sidebar.classList.contains("shift")) {
        if (!toggle) return;
        toggle.click();
      }
      // Let the drawer's MutationObserver clear inert before moving focus.
      window.queueMicrotask(() => {
        input.focus({ preventScroll: true });
        input.select();
      });
    }
  });

  document.querySelectorAll(".rst-content div.highlight").forEach(block => {
    const code = block.querySelector("pre");
    if (!code || !code.textContent.trim()) return;
    const button = document.createElement("button");
    const isPrompt = Boolean(block.closest(".tq-ai-onboarding"));
    const copyLabel = isPrompt ? "复制给 AI" : "复制";
    button.type = "button";
    button.className = "tq-copy-button";
    button.textContent = copyLabel;
    button.setAttribute("aria-label", isPrompt ? "复制 AI 提示词" : "复制代码");
    const status = document.createElement("span");
    status.className = "tq-sr-only";
    status.setAttribute("role", "status");
    block.append(button, status);
    button.addEventListener("click", async () => {
      try {
        // Copy only code, never line numbers or the copy control itself.
        const clean = code.cloneNode(true);
        clean.querySelectorAll(".linenos, .gp").forEach(node => node.remove());
        await navigator.clipboard.writeText(clean.textContent);
        button.textContent = "已复制";
        status.textContent = isPrompt ? "提示词已复制到剪贴板" : "代码已复制到剪贴板";
      } catch (_) {
        button.textContent = "请手动复制";
        status.textContent = "无法访问剪贴板，请选中代码后复制";
      }
      window.setTimeout(() => { button.textContent = copyLabel; status.textContent = ""; }, 2200);
    });
  });

  // Sphinx headerlinks are ordinary anchors until enhanced here. Keep their
  // hrefs for right-click, modified clicks and browsing without JavaScript.
  const permalinkStatus = document.createElement("div");
  permalinkStatus.className = "tq-permalink-status";
  permalinkStatus.setAttribute("role", "status");
  permalinkStatus.setAttribute("aria-live", "polite");
  permalinkStatus.setAttribute("aria-atomic", "true");
  document.body.append(permalinkStatus);
  let permalinkStatusTimer;

  document.querySelectorAll('.rst-content a.headerlink[href^="#"]').forEach(link => {
    link.title = "复制此处链接";
    link.setAttribute("aria-label", "复制此处链接");
    link.addEventListener("click", async event => {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      const url = new URL(link.href);
      // Search-result highlighting is not part of the permanent document link.
      url.searchParams.delete("highlight");
      window.clearTimeout(permalinkStatusTimer);
      permalinkStatus.textContent = "正在复制链接…";
      let copied = false;
      try {
        await navigator.clipboard.writeText(url.href);
        copied = true;
        permalinkStatus.textContent = "链接已复制";
      } catch (_) {
        permalinkStatus.textContent = "复制失败，请右键点击链接图标，选择“复制链接地址”";
      }
      window.clearTimeout(permalinkStatusTimer);
      permalinkStatusTimer = window.setTimeout(() => { permalinkStatus.textContent = ""; }, copied ? 2200 : 6000);
    });
  });

  const enableScrollKeyboard = () => {
    document.querySelectorAll(".rst-content pre, .wy-table-responsive").forEach(region => {
      if (region.scrollWidth > region.clientWidth) {
        region.tabIndex = 0;
        region.setAttribute("aria-label", region.tagName === "PRE" ? "代码，可横向滚动" : "表格，可横向滚动");
      }
    });
  };
  enableScrollKeyboard();
  // RTD wraps tables after DOMContentLoaded; include those wrappers as well.
  window.addEventListener("load", enableScrollKeyboard, { once: true });
  window.addEventListener("resize", enableScrollKeyboard);

  const toc = document.querySelector(".tq-page-toc");
  if (toc && "IntersectionObserver" in window) {
    const links = [...toc.querySelectorAll('a[href^="#"]')];
    const targets = links.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1)))).filter(Boolean);
    const observer = new IntersectionObserver(entries => {
      const current = entries.filter(entry => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!current) return;
      links.forEach(link => {
        if (decodeURIComponent(link.hash.slice(1)) === current.target.id) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    }, { rootMargin: "-90px 0px -65% 0px" });
    targets.forEach(target => observer.observe(target));
  }

  if (toggle && sidebar) {
    const syncMenu = () => {
      const expanded = sidebar.classList.contains("shift");
      toggle.setAttribute("aria-expanded", String(expanded));
      toggle.setAttribute("aria-label", expanded ? "关闭文档导航" : "打开文档导航");
      sidebar.inert = mobile.matches && !expanded;
      if (mobile.matches && !expanded) sidebar.setAttribute("aria-hidden", "true");
      else sidebar.removeAttribute("aria-hidden");
    };
    new MutationObserver(syncMenu).observe(sidebar, { attributes: true, attributeFilter: ["class"] });
    mobile.addEventListener("change", syncMenu);
    syncMenu();
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && sidebar.classList.contains("shift")) { toggle.click(); toggle.focus(); }
    });
  }
});
