export function getCommanderValue(state) {
  return state.format === "commander" ? state.commander : "";
}

export function getFormState(state = {}) {
  return {
    name: state.name || "",
    format: state.format || "commander",
    commander: getCommanderValue({
      format: state.format || "commander",
      commander: state.commander || "",
    }),
    decklist: state.decklist || "",
    sideboard: state.sideboard || "",
  };
}

export function applyFormState(state, formatEl, formFields, syncCommanderVisibility) {
  const next = getFormState(state);
  formFields.name.value = next.name;
  formatEl.value = next.format;
  formFields.commander.value = next.commander;
  formFields.decklist.value = next.decklist;
  formFields.sideboard.value = next.sideboard;
  syncCommanderVisibility();
}

export function updateUrlFromState(state) {
  const normalized = getFormState(state);
  const params = new URLSearchParams();

  if (normalized.name) params.set("name", normalized.name);
  if (normalized.format) params.set("format", normalized.format);
  if (normalized.commander) params.set("commander", normalized.commander);
  if (normalized.decklist) params.set("decklist", normalized.decklist);
  if (normalized.sideboard) params.set("sideboard", normalized.sideboard);

  const nextUrl = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ""}`;
  window.history.replaceState({}, "", nextUrl);
}

export function updateUrlFromForm(formatEl, formFields) {
  updateUrlFromState({
    name: formFields.name.value,
    format: formatEl.value,
    commander: formFields.commander.value,
    decklist: formFields.decklist.value,
    sideboard: formFields.sideboard.value,
  });
}

export function persistDraftState(storageKey, state, setDraftStatus) {
  const normalized = getFormState(state);
  window.localStorage.setItem(storageKey, JSON.stringify({ ...normalized, savedAt: new Date().toISOString() }));
  setDraftStatus("Draft autosaved locally.", "success");
}

export function persistDraft(storageKey, formatEl, formFields, setDraftStatus) {
  persistDraftState(storageKey, {
    name: formFields.name.value,
    format: formatEl.value,
    commander: formFields.commander.value,
    decklist: formFields.decklist.value,
    sideboard: formFields.sideboard.value,
  }, setDraftStatus);
}

export function readDraftState(storageKey) {
  const raw = window.localStorage.getItem(storageKey);
  if (!raw) return null;
  return JSON.parse(raw);
}

export function restoreDraft(storageKey, formatEl, formFields, syncCommanderVisibility, updateUrl, setDraftStatus, showToast) {
  const parsed = readDraftState(storageKey);
  if (!parsed) {
    setDraftStatus("No local draft saved yet.", "warning");
    showToast("No saved draft to restore yet.", "warning");
    return;
  }

  applyFormState(parsed, formatEl, formFields, syncCommanderVisibility);
  updateUrl();
  setDraftStatus(`Restored local draft from ${new Date(parsed.savedAt).toLocaleString()}.`, "success");
  showToast("Draft restored.", "success");
}

export function clearDraft(storageKey, setDraftStatus, showToast) {
  window.localStorage.removeItem(storageKey);
  setDraftStatus("Local draft cleared.", "muted");
  showToast("Local draft cleared.", "success");
}

export function hydrateStateFromUrl(defaultState = {}) {
  const params = new URLSearchParams(window.location.search);
  if (!params.toString()) {
    return null;
  }

  const baseline = getFormState(defaultState);
  return getFormState({
    name: params.get("name") || baseline.name,
    format: params.get("format") || baseline.format,
    commander: params.get("commander") || "",
    decklist: params.get("decklist") || baseline.decklist,
    sideboard: params.get("sideboard") || "",
  });
}

export function hydrateFormFromUrl(formatEl, formFields, syncCommanderVisibility, setStatus) {
  const hydrated = hydrateStateFromUrl({
    name: formFields.name.value,
    format: formatEl.value,
    commander: formFields.commander.value,
    decklist: formFields.decklist.value,
    sideboard: formFields.sideboard.value,
  });

  if (!hydrated) {
    return false;
  }

  applyFormState(hydrated, formatEl, formFields, syncCommanderVisibility);
  setStatus("Loaded deck state from the URL.", "success");
  return true;
}
