export function legacyCopyToClipboard(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "fixed";
  textArea.style.top = "-9999px";
  textArea.style.left = "-9999px";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch (error) {
    console.error(error);
  }

  document.body.removeChild(textArea);
  return copied;
}

export async function copyToClipboard(text, successMessage, failureMessage, setStatus, showToast) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      setStatus(successMessage, "success");
      showToast(successMessage, "success");
      return;
    }

    if (legacyCopyToClipboard(text)) {
      setStatus(`${successMessage} (fallback copy)`, "success");
      showToast("Copied with browser fallback.", "success");
      return;
    }

    setStatus(`${failureMessage} Copy it manually from the dialog.`, "warning");
    showToast("Automatic copy failed — manual copy dialog opened.", "warning");
    window.prompt("Copy this text:", text);
  } catch (error) {
    console.error(error);
    if (legacyCopyToClipboard(text)) {
      setStatus(`${successMessage} (fallback copy)`, "success");
      showToast("Copied with browser fallback.", "success");
      return;
    }
    setStatus(`${failureMessage} Copy it manually from the dialog.`, "warning");
    showToast("Automatic copy failed — manual copy dialog opened.", "warning");
    window.prompt("Copy this text:", text);
  }
}
