// Legacy shim: dashboard rendering now happens in React at dashboard.html
if (window.location.pathname.endsWith('/dashboard.html')) {
  const target = chrome?.runtime?.getURL ? chrome.runtime.getURL('dashboard.html') : null;
  if (target && target !== window.location.href) {
    window.location.replace(target);
  }
}
