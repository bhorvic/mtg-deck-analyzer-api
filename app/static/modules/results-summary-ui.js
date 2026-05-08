import { resultsSummaryRootEl } from "./dom.js";
import { initResultsSummary } from "../react/results-summary.js";

const resultsSummaryRenderer = resultsSummaryRootEl
  ? initResultsSummary("results-summary-root")
  : null;

export function updateResultsSummary(data = null) {
  resultsSummaryRenderer?.render(data);
}
