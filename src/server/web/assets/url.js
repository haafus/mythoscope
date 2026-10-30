// Record a page's state in the address bar. push=true adds a history entry (a deliberate
// selection, so Back returns to the previous one); push=false rewrites the current entry
// (canonicalising a restored state). No-op when the URL is already current.
export function setHashUrl(url, push = true) {
    if (url === window.location.hash) return;
    if (push) history.pushState(null, "", url);
    else history.replaceState(null, "", url);
}
