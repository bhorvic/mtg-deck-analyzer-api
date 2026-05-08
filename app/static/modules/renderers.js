import { appState } from "./state.js";

export function formatCountLabel(count, noun) {
  return `${count} ${noun}${count === 1 ? "" : "s"}`;
}

export function renderColorIdentityMarkup(colors = []) {
  if (!colors.length) {
    return '<span class="colorless-label">Colorless</span>';
  }

  return `
    <span class="color-pip-row" aria-label="${colors.join(", ")}">
      ${colors.map((color) => `<img class="color-pip" src="https://svgs.scryfall.io/card-symbols/${color}.svg" alt="${color}" />`).join("")}
    </span>
  `;
}

export function renderKeyValueList(elementId, values) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";

  const entries = Object.entries(values || {});
  if (!entries.length) {
    el.innerHTML = "<li><span>None</span><strong>-</strong></li>";
    return;
  }

  entries.forEach(([key, value]) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${key}</span><strong>${value}</strong>`;
    el.appendChild(li);
  });
}

export function renderMessageList(elementId, messages, emptyMessage, variant = "neutral") {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  el.dataset.variant = variant;

  if (!messages?.length) {
    const li = document.createElement("li");
    li.className = "message-empty";
    li.textContent = emptyMessage;
    el.appendChild(li);
    return;
  }

  messages.forEach((message) => {
    const li = document.createElement("li");
    li.textContent = typeof message === "string" ? message : message.body;
    el.appendChild(li);
  });
}

export function classifyWarning(message = "") {
  const normalized = message.toLowerCase();

  if (
    normalized.includes("not legal")
    || normalized.includes("illegal duplicates")
    || normalized.includes("too many copies")
    || normalized.includes("restricted cards exceed")
    || normalized.includes("outside commander color identity")
    || normalized.includes("does not appear to be a legal commander")
    || normalized.includes("do not appear to form a legal commander pair")
  ) {
    return { label: "Legality", tone: "danger" };
  }

  if (
    normalized.includes("card not found in scryfall")
    || normalized.includes("commander not found in scryfall")
  ) {
    return { label: "Lookup", tone: "warning" };
  }

  if (
    normalized.includes("should contain")
    || normalized.includes("sideboards are not supported")
    || normalized.includes("sideboards can contain")
    || normalized.includes("no commander provided")
    || normalized.includes("commander appears in the main decklist")
    || normalized.includes("only up to two commanders")
  ) {
    return { label: "Structure", tone: "warning" };
  }

  return { label: "Heads-up", tone: "neutral" };
}

export function renderDetailedMessageList(elementId, messages, emptyMessage, defaultVariant = "neutral") {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  el.dataset.variant = defaultVariant;

  if (!messages?.length) {
    const li = document.createElement("li");
    li.className = "message-empty";
    li.textContent = emptyMessage;
    el.appendChild(li);
    return;
  }

  messages.forEach((message) => {
    const descriptor = typeof message === "string"
      ? { body: message, ...classifyWarning(message) }
      : message;

    const li = document.createElement("li");
    li.className = "message-item";
    li.innerHTML = `
      <div class="message-item-head">
        <span class="message-badge message-badge-${descriptor.tone || defaultVariant}">${descriptor.label || "Note"}</span>
      </div>
      <div class="message-body">${descriptor.body}</div>
    `;
    el.appendChild(li);
  });
}

export function buildAnalysisOverview(data) {
  const warnings = data.warnings || [];
  const recommendations = data.recommendations || [];
  const breakdown = { danger: 0, warning: 0, neutral: 0 };

  warnings.forEach((message) => {
    const descriptor = classifyWarning(message);
    breakdown[descriptor.tone] = (breakdown[descriptor.tone] || 0) + 1;
  });

  const hasDanger = breakdown.danger > 0;
  const hasWarning = breakdown.warning > 0;

  if (!warnings.length) {
    return {
      summary: recommendations.length
        ? "No validation warnings. This looks mechanically clean, with only tuning suggestions left."
        : "No warnings or recommendations — this looks unusually clean at a glance.",
      pill: "Clean",
      pillTone: "success",
      breakdown,
    };
  }

  if (hasDanger) {
    return {
      summary: "This deck has legality or rules-level issues worth fixing before you trust the rest of the analysis.",
      pill: "Needs attention",
      pillTone: "danger",
      breakdown,
    };
  }

  if (hasWarning) {
    return {
      summary: "Nothing catastrophic, but there are structure or lookup issues worth checking before you tune the list.",
      pill: "Mostly clean",
      pillTone: "warning",
      breakdown,
    };
  }

  return {
    summary: "The deck mostly checks out. Remaining notes are soft heads-ups rather than blockers.",
    pill: "Stable",
    pillTone: "neutral",
    breakdown,
  };
}

export function updateFeedbackSummary(data) {
  const overview = buildAnalysisOverview(data);
  document.getElementById("analysis-summary").textContent = overview.summary;
  const healthPill = document.getElementById("analysis-health-pill");
  healthPill.textContent = overview.pill;
  healthPill.className = `pill ${overview.pillTone}`;

  document.getElementById("analysis-danger-count").textContent = overview.breakdown.danger;
  document.getElementById("analysis-warning-count").textContent = overview.breakdown.warning + overview.breakdown.neutral;
  document.getElementById("analysis-recommendation-count").textContent = data.recommendations?.length || 0;

  document.getElementById("analysis-danger-label").textContent = overview.breakdown.danger
    ? `${overview.breakdown.danger} hard issue${overview.breakdown.danger === 1 ? "" : "s"} flagged.`
    : "No hard legality issues detected.";
  document.getElementById("analysis-warning-label").textContent = (overview.breakdown.warning + overview.breakdown.neutral)
    ? `${overview.breakdown.warning + overview.breakdown.neutral} softer warning${overview.breakdown.warning + overview.breakdown.neutral === 1 ? "" : "s"} to review.`
    : "No structure or lookup warnings detected.";
  document.getElementById("analysis-recommendation-label").textContent = data.recommendations?.length
    ? `${data.recommendations.length} tuning suggestion${data.recommendations.length === 1 ? "" : "s"}.`
    : "No tuning suggestions right now.";

  document.getElementById("warnings-count").textContent = data.warnings?.length || 0;
  document.getElementById("recommendations-count").textContent = data.recommendations?.length || 0;
  document.getElementById("commander-validation-count").textContent = data.color_identity_violations?.length || 0;
  document.getElementById("warnings-summary").textContent = data.warnings?.length
    ? `${overview.breakdown.danger} legality, ${overview.breakdown.warning + overview.breakdown.neutral} softer checks.`
    : "No format, legality, or lookup warnings.";
  document.getElementById("recommendations-summary").textContent = data.recommendations?.length
    ? `${data.recommendations.length} suggestion${data.recommendations.length === 1 ? "" : "s"} to consider.`
    : "No tuning suggestions right now.";
  document.getElementById("commander-validation-summary").textContent = data.format === "commander"
    ? (data.color_identity_violations?.length ? "Commander color identity issues were found." : "No commander color identity issues.")
    : "Commander-only validation is hidden for non-Commander formats.";
}

function toggleSectionState(sectionId, { hidden = false, quiet = false, emphasis = false, open = null } = {}) {
  const element = document.getElementById(sectionId);
  if (!element) return;

  element.classList.toggle("section-soft-hidden", hidden);
  element.classList.toggle("section-quiet", quiet && !hidden);
  element.classList.toggle("section-emphasis", emphasis && !hidden);

  if (typeof open === "boolean" && element.tagName === "DETAILS") {
    element.open = open;
  }
}

export function updateSectionEmphasis(data) {
  const warningCount = data.warnings?.length || 0;
  const recommendationCount = data.recommendations?.length || 0;
  const commanderIssueCount = data.color_identity_violations?.length || 0;
  const overview = buildAnalysisOverview(data);
  const hasDanger = overview.breakdown.danger > 0;
  const hasWarnings = warningCount > 0;
  const hasArchetypes = Boolean(data.archetype_guesses?.length);
  const hasSideboard = (data.sideboard_count || 0) > 0;
  const hasManaCurve = Boolean(Object.keys(data.mana_curve || {}).length);
  const hasTypeBreakdown = Boolean(Object.keys(data.type_breakdown || {}).length);
  const hasClassificationCounts = Boolean(Object.keys(data.classification_counts || {}).length);
  const lowIssueState = !hasWarnings || (warningCount <= 1 && !hasDanger);

  toggleSectionState("warnings-section", { emphasis: hasWarnings, quiet: !hasWarnings, open: hasWarnings });
  toggleSectionState("recommendations-section", { quiet: hasWarnings && !recommendationCount, open: recommendationCount > 0 && lowIssueState });
  toggleSectionState("commander-validation-section", {
    hidden: data.format !== "commander",
    emphasis: commanderIssueCount > 0,
    quiet: data.format === "commander" && commanderIssueCount === 0,
    open: commanderIssueCount > 0,
  });
  toggleSectionState("archetype-section", { hidden: !hasArchetypes, quiet: hasWarnings });
  toggleSectionState("sideboard-section", { hidden: !hasSideboard, open: false });
  toggleSectionState("mana-curve-section", { quiet: hasWarnings, open: lowIssueState && !hasDanger && hasManaCurve });
  toggleSectionState("type-breakdown-section", { quiet: hasWarnings, open: false });
  toggleSectionState("classification-section", { quiet: hasWarnings, open: false });
  toggleSectionState("mainboard-section", { quiet: hasWarnings, open: false });
  toggleSectionState("mana-curve-chart-section", { hidden: !hasManaCurve, quiet: hasWarnings });
  toggleSectionState("type-breakdown-chart-section", { hidden: !hasTypeBreakdown, quiet: hasWarnings });

  document.getElementById("summary-grid")?.classList.toggle("section-soft-hidden", !hasManaCurve && !hasTypeBreakdown && !hasClassificationCounts);
  document.getElementById("chart-grid")?.classList.toggle("section-soft-hidden", !hasManaCurve && !hasTypeBreakdown);
}


export function renderBarChart(elementId, values, emptyMessage) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";

  const entries = Object.entries(values || {});
  if (!entries.length) {
    el.innerHTML = `<p class="chart-empty">${emptyMessage}</p>`;
    return;
  }

  const maxValue = Math.max(...entries.map(([, value]) => Number(value) || 0), 1);
  entries.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "chart-row";
    row.innerHTML = `
      <div class="chart-label-row">
        <span>${label}</span>
        <strong>${value}</strong>
      </div>
      <div class="chart-track">
        <div class="chart-bar" style="width: ${(Number(value) / maxValue) * 100}%"></div>
      </div>
    `;
    el.appendChild(row);
  });
}


export function buildSummaryText(data) {
  const parts = [
    `${data.deck_name} (${data.format.toUpperCase()})`,
    `Colors: ${data.color_identity?.join(", ") || "Colorless"}`,
    `Cards: ${data.mainboard_count} main / ${data.sideboard_count} side`,
    `Warnings: ${data.warnings?.length || 0}`,
  ];

  if (data.commanders?.length) {
    parts.push(`Commander(s): ${data.commanders.map((commander) => commander.name).join(" / ")}`);
  } else if (data.commander?.name) {
    parts.push(`Commander: ${data.commander.name}`);
  }

  if (data.primary_archetype) {
    parts.push(`Primary archetype: ${data.primary_archetype}`);
  }

  if (data.archetype_guesses?.length) {
    parts.push(`Archetype guesses:\n- ${data.archetype_guesses.map((guess) => `${guess.name} (${Math.round((guess.confidence || 0) * 100)}%)`).join("\n- ")}`);
  }

  if (data.recommendations?.length) {
    parts.push(`Recommendations:\n- ${data.recommendations.join("\n- ")}`);
  }

  if (data.warnings?.length) {
    parts.push(`Warnings:\n- ${data.warnings.join("\n- ")}`);
  }

  return parts.join("\n\n");
}
