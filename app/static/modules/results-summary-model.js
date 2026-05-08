import { buildAnalysisOverview, classifyWarning, formatCountLabel } from "./renderers.js";

export function buildResultsSummaryModel(data = null) {
  if (!data) {
    return {
      stats: [
        { label: "Total cards", value: "-", accent: true },
        { label: "Unique cards", value: "-" },
        { label: "Colors", value: "Colorless", isColors: true, colors: [] },
        { label: "Commander", value: "-" },
        { label: "Main / Side", value: "-" },
        { label: "Warnings", value: "0" },
      ],
      overview: {
        summary: "Run an analysis to get a fast deck health summary.",
        pill: "Waiting",
        pillTone: "neutral",
        dangerCount: 0,
        warningCount: 0,
        recommendationCount: 0,
        dangerLabel: "Legality and hard format issues.",
        warningLabel: "Structure and validation warnings.",
        recommendationLabel: "Tuning ideas and softer guidance.",
      },
      feedback: {
        commanderValidation: {
          hidden: true,
          summary: "Color identity and pairing checks.",
          count: 0,
          pillTone: "neutral",
          open: true,
          items: [],
          emptyMessage: "No commander color identity issues.",
          variant: "neutral",
          detailed: false,
          quiet: false,
          emphasis: false,
        },
        recommendations: {
          summary: "Soft tuning ideas.",
          count: 0,
          pillTone: "success",
          open: false,
          items: [],
          emptyMessage: "No recommendations.",
          variant: "success",
          detailed: false,
          quiet: false,
          emphasis: false,
        },
        warnings: {
          summary: "Format, legality, and lookup checks.",
          count: 0,
          pillTone: "danger",
          open: false,
          items: [],
          emptyMessage: "No warnings.",
          variant: "success",
          detailed: true,
          quiet: true,
          emphasis: false,
        },
      },
      header: {
        title: "Results",
        format: "-",
        colors: [],
        warningCount: 0,
        mainboardCountLabel: "0 cards",
        sideboardCountLabel: "0 cards",
      },
    };
  }

  const overview = buildAnalysisOverview(data);
  const warningCount = data.warnings?.length || 0;
  const recommendationCount = data.recommendations?.length || 0;
  const commanderIssueCount = data.color_identity_violations?.length || 0;
  const hasDanger = overview.breakdown.danger > 0;
  const hasWarnings = warningCount > 0;
  const lowIssueState = !hasWarnings || (warningCount <= 1 && !hasDanger);
  const commanderNames = data.commanders?.length
    ? data.commanders.map((commander) => commander.name).join(" / ")
    : (data.commander?.name || "-");

  return {
    stats: [
      { label: "Total cards", value: String(data.total_cards ?? "-"), accent: true },
      { label: "Unique cards", value: String(data.unique_cards ?? "-") },
      { label: "Colors", value: data.color_identity?.join(", ") || "Colorless", isColors: true, colors: data.color_identity || [] },
      { label: "Commander", value: data.format === "commander" ? commanderNames : "-" },
      { label: "Main / Side", value: `${data.mainboard_count} / ${data.sideboard_count}` },
      { label: "Warnings", value: String(warningCount) },
    ],
    overview: {
      summary: overview.summary,
      pill: overview.pill,
      pillTone: overview.pillTone,
      dangerCount: overview.breakdown.danger,
      warningCount: overview.breakdown.warning + overview.breakdown.neutral,
      recommendationCount,
      dangerLabel: overview.breakdown.danger
        ? `${overview.breakdown.danger} hard issue${overview.breakdown.danger === 1 ? "" : "s"} flagged.`
        : "No hard legality issues detected.",
      warningLabel: (overview.breakdown.warning + overview.breakdown.neutral)
        ? `${overview.breakdown.warning + overview.breakdown.neutral} softer warning${overview.breakdown.warning + overview.breakdown.neutral === 1 ? "" : "s"} to review.`
        : "No structure or lookup warnings detected.",
      recommendationLabel: recommendationCount
        ? `${recommendationCount} tuning suggestion${recommendationCount === 1 ? "" : "s"}.`
        : "No tuning suggestions right now.",
    },
    feedback: {
      commanderValidation: {
        hidden: data.format !== "commander",
        summary: data.format === "commander"
          ? (commanderIssueCount ? "Commander color identity issues were found." : "No commander color identity issues.")
          : "Commander-only validation is hidden for non-Commander formats.",
        count: commanderIssueCount,
        pillTone: "neutral",
        open: commanderIssueCount > 0,
        items: commanderIssueCount
          ? data.color_identity_violations.map((name) => ({ body: `${name} is outside the commander's color identity.` }))
          : [],
        emptyMessage: "No commander color identity issues.",
        variant: commanderIssueCount ? "neutral" : "success",
        detailed: false,
        quiet: data.format === "commander" && commanderIssueCount === 0,
        emphasis: commanderIssueCount > 0,
      },
      recommendations: {
        summary: recommendationCount
          ? `${recommendationCount} suggestion${recommendationCount === 1 ? "" : "s"} to consider.`
          : "No tuning suggestions right now.",
        count: recommendationCount,
        pillTone: "success",
        open: recommendationCount > 0 && lowIssueState,
        items: (data.recommendations || []).map((body) => ({ body })),
        emptyMessage: "No recommendations.",
        variant: "success",
        detailed: false,
        quiet: hasWarnings && !recommendationCount,
        emphasis: false,
      },
      warnings: {
        summary: warningCount
          ? `${overview.breakdown.danger} legality, ${overview.breakdown.warning + overview.breakdown.neutral} softer checks.`
          : "No format, legality, or lookup warnings.",
        count: warningCount,
        pillTone: "danger",
        open: hasWarnings,
        items: (data.warnings || []).map((body) => ({ body, ...classifyWarning(body) })),
        emptyMessage: "No warnings.",
        variant: hasWarnings ? "danger" : "success",
        detailed: true,
        quiet: !hasWarnings,
        emphasis: hasWarnings,
      },
    },
    header: {
      title: data.deck_name || "Results",
      format: (data.format || "unknown").toUpperCase(),
      colors: data.color_identity || [],
      warningCount,
      mainboardCountLabel: formatCountLabel(data.mainboard_count || 0, "card"),
      sideboardCountLabel: formatCountLabel(data.sideboard_count || 0, "card"),
    },
  };
}
