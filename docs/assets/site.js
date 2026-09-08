'use strict';
// Copy is a progressive enhancement. The full selectable text remains visible.
for (const button of document.querySelectorAll('[data-copy-target]')) {
  const target = document.getElementById(button.dataset.copyTarget);
  const status = document.getElementById(button.dataset.copyStatus);
  if (!target || !status) continue;
  button.hidden = false;
  button.addEventListener('click', async () => {
    if (!navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') {
      status.textContent = 'Clipboard access is unavailable. Select the text above and copy it with your browser or keyboard.';
      return;
    }
    button.disabled = true;
    status.textContent = '';
    try {
      await navigator.clipboard.writeText(target.textContent.trim());
      status.textContent = 'Copied. Paste it when you are ready.';
    } catch {
      status.textContent = 'Your browser did not allow copying. Select the text above and copy it manually.';
    } finally {
      button.disabled = false;
    }
  });
}