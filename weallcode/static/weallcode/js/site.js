// Site-wide behaviour for the public base (weallcode/_base.html).
// One ES module with no imports: ManifestFilesMixin doesn't rewrite import paths.
// The mobile nav needs no script: it is a native popover (popovertarget).

// "See more" reveal: <button data-reveal-target="id" aria-controls="id" aria-expanded="false">
// controls a wrapper with hidden="until-found". Clicking, or Find-in-page matching inside it
// (beforematch), shows the content, marks the button expanded and hides the button's wrapper.
function revealed(target) {
  for (const button of document.querySelectorAll("[data-reveal-target]")) {
    if (button.dataset.revealTarget !== target.id) continue;
    button.setAttribute("aria-expanded", "true");
    if (button.parentElement) button.parentElement.hidden = true;
  }
}

document.addEventListener("click", (event) => {
  const button = event.target.closest?.("[data-reveal-target]");
  if (!button) return;
  const target = document.getElementById(button.dataset.revealTarget);
  if (!target) return;
  target.hidden = false;
  revealed(target);
  // The button just hid itself, so keep focus near where it was.
  target.tabIndex = -1;
  target.focus({ preventScroll: true });
});

// beforematch bubbles, so one listener covers every until-found region.
document.addEventListener("beforematch", (event) => {
  if (event.target instanceof HTMLElement && event.target.id) revealed(event.target);
});
