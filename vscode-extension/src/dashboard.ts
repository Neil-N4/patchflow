import type {
  AnalyzeResult,
  CleanErrorResult,
  CleanPreviewResult,
  CleanSuccessResult,
  DoctorResult,
  StatusResult,
} from "./types";

export type DashboardPayload = {
  analyze?: AnalyzeResult;
  preview?: CleanPreviewResult;
  status?: StatusResult;
  doctor?: DoctorResult;
  cleanResult?: CleanSuccessResult | CleanErrorResult;
  analyzeError?: string;
  previewError?: string;
  statusError?: string;
  doctorError?: string;
  prRef?: string;
  cleanBranchName?: string;
  switchToClean?: boolean;
};

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderList(items: string[], empty = "none"): string {
  if (!items.length) {
    return `<li>${escapeHtml(empty)}</li>`;
  }
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function statusTone(status: string | undefined): string {
  const normalized = (status ?? "").toUpperCase();
  if (normalized.includes("FAIL") || normalized.includes("BLOCK")) {
    return "bad";
  }
  if (normalized.includes("WARN") || normalized.includes("LOW") || normalized.includes("DIRTY")) {
    return "warn";
  }
  return "good";
}

function renderPills(analyzeResult: AnalyzeResult | undefined): string {
  if (!analyzeResult) {
    return "";
  }

  return [
    ["Branch", analyzeResult.branch.current],
    ["Base", analyzeResult.branch.base],
    ["Status", analyzeResult.status],
    ["Confidence", analyzeResult.confidence],
    ["Clusters", String(analyzeResult.clusters.length)],
    ["Changed files", String(analyzeResult.changed_files.length)],
  ]
    .map(
      ([label, value]) =>
        `<div class="pill"><span class="pill-label">${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`,
    )
    .join("");
}

function renderMetrics(analyzeResult: AnalyzeResult | undefined): string {
  if (!analyzeResult) {
    return `<div class="metric-grid"><div class="metric"><span class="metric-label">Analysis</span><strong>Unavailable</strong></div></div>`;
  }

  const selectedCluster = analyzeResult.clusters.find(
    (cluster) => cluster.index === analyzeResult.selected_cluster_index,
  );
  const metrics = [
    ["Ahead of base", String(analyzeResult.branch.ahead_by)],
    ["Behind base", String(analyzeResult.branch.behind_by)],
    ["Worktree files", String(analyzeResult.worktree_files.length)],
    ["Selected files", String(selectedCluster?.files.length ?? 0)],
  ];

  return `<div class="metric-grid">${metrics
    .map(
      ([label, value]) =>
        `<div class="metric"><span class="metric-label">${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`,
    )
    .join("")}</div>`;
}

function renderClusterCards(analyzeResult: AnalyzeResult | undefined): string {
  if (!analyzeResult || !analyzeResult.clusters.length) {
    return `<div class="empty">No clusters detected yet.</div>`;
  }

  return `<div class="cluster-grid">${analyzeResult.clusters
    .map((cluster) => {
      const isSelected = analyzeResult.selected_cluster_index === cluster.index;
      const commitMessages = cluster.commits.map((commit) => commit.message);
      return `
        <article class="cluster-card ${isSelected ? "selected" : ""}">
          <div class="cluster-card-header">
            <div>
              <div class="cluster-index">Cluster ${cluster.index}</div>
              <h3>${escapeHtml(cluster.label)}</h3>
            </div>
            <span class="badge ${statusTone(cluster.confidence)}">${escapeHtml(cluster.confidence)}</span>
          </div>
          <div class="cluster-meta">
            <span>Score ${cluster.score.toFixed(2)}</span>
            <span>${cluster.commits.length} commits</span>
            <span>${cluster.files.length} files</span>
          </div>
          <div class="cluster-section">
            <div class="section-label">Commits</div>
            <ul>${renderList(commitMessages, "none")}</ul>
          </div>
          <div class="cluster-section">
            <div class="section-label">Files</div>
            <ul>${renderList(cluster.files, "none")}</ul>
          </div>
        </article>`;
    })
    .join("")}</div>`;
}

function renderStatusSummary(statusResult: StatusResult | undefined, statusError?: string): string {
  if (!statusResult) {
    return `<div class="empty">${escapeHtml(statusError ?? "No PR status available.")}</div>`;
  }

  return `
    <div class="summary-row">
      <div class="summary-item">
        <span class="summary-label">Status</span>
        <strong class="badge ${statusTone(statusResult.status)}">${escapeHtml(statusResult.status)}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">Recommendation</span>
        <strong>${escapeHtml(statusResult.recommendation)}</strong>
      </div>
    </div>
    <div class="column-grid">
      <div>
        <div class="section-label">Checks</div>
        <ul>${renderList(statusResult.checks)}</ul>
      </div>
      <div>
        <div class="section-label">Reviews</div>
        <ul>${renderList(statusResult.reviews)}</ul>
      </div>
      <div>
        <div class="section-label">Branch</div>
        <ul>${renderList(statusResult.branch)}</ul>
      </div>
      <div>
        <div class="section-label">Conflicts</div>
        <ul>${renderList(statusResult.conflicts)}</ul>
      </div>
    </div>`;
}

function renderDoctorSummary(doctorResult: DoctorResult | undefined, doctorError?: string): string {
  if (!doctorResult) {
    return `<div class="empty">${escapeHtml(doctorError ?? "No environment diagnostics available.")}</div>`;
  }

  return `
    <div class="summary-row">
      <div class="summary-item">
        <span class="summary-label">Overall</span>
        <strong class="badge ${statusTone(doctorResult.overall_status)}">${escapeHtml(doctorResult.overall_status)}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">Patchflow</span>
        <strong>${escapeHtml(doctorResult.patchflow_version)}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">Python</span>
        <strong>${escapeHtml(doctorResult.python_version)}</strong>
      </div>
    </div>
    <ul>${renderList(
      doctorResult.checks.map((check) => `[${check.status}] ${check.name}: ${check.summary}`),
    )}</ul>`;
}

function renderPreview(preview: CleanPreviewResult | undefined, previewError?: string): string {
  if (!preview) {
    return `<div class="empty">${escapeHtml(previewError ?? "Run a clean preview to see selected and excluded changes.")}</div>`;
  }

  return `
    <div class="summary-row">
      <div class="summary-item">
        <span class="summary-label">Planned branch</span>
        <strong><code>${escapeHtml(preview.branch_name)}</code></strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">Selected cluster</span>
        <strong>${preview.selected_cluster_index ?? "none"}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">Safe</span>
        <strong>${preview.safe ? "yes" : "no"}</strong>
      </div>
    </div>
    <div class="column-grid">
      <div>
        <div class="section-label">Selected commits</div>
        <ul>${renderList(preview.selected_commits.map((commit) => commit.message))}</ul>
      </div>
      <div>
        <div class="section-label">Excluded commits</div>
        <ul>${renderList(preview.excluded_commits.map((commit) => commit.message))}</ul>
      </div>
      <div>
        <div class="section-label">Selected files</div>
        <ul>${renderList(preview.selected_files)}</ul>
      </div>
      <div>
        <div class="section-label">Excluded files</div>
        <ul>${renderList(preview.excluded_files)}</ul>
      </div>
    </div>`;
}

function renderSelectedCluster(analyzeResult: AnalyzeResult | undefined): string {
  if (!analyzeResult) {
    return `<div class="empty">No analysis loaded.</div>`;
  }

  const cluster = analyzeResult.clusters.find(
    (entry) => entry.index === analyzeResult.selected_cluster_index,
  );
  if (!cluster) {
    return `<div class="empty">No cluster selected.</div>`;
  }

  return `
    <div class="summary-row">
      <div class="summary-item">
        <span class="summary-label">Cluster</span>
        <strong>${cluster.index}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">Score</span>
        <strong>${cluster.score.toFixed(2)}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">Confidence</span>
        <strong class="badge ${statusTone(cluster.confidence)}">${escapeHtml(cluster.confidence)}</strong>
      </div>
    </div>
    <div class="column-grid two">
      <div>
        <div class="section-label">Recommendations</div>
        <ul>${renderList(analyzeResult.recommendations)}</ul>
      </div>
      <div>
        <div class="section-label">Other changes</div>
        <ul>${renderList(analyzeResult.other_files)}</ul>
      </div>
    </div>`;
}

export function renderDashboardHtml(payload: DashboardPayload): string {
  const analyzeResult = payload.analyze;
  const cleanResult = payload.cleanResult;
  const clusterOptions =
    analyzeResult?.clusters
      .map((cluster) => {
        const selected =
          analyzeResult.selected_cluster_index === cluster.index ? "selected" : "";
        return `<option value="${cluster.index}" ${selected}>[${cluster.index}] ${escapeHtml(
          cluster.label,
        )} · ${cluster.commits.length} commits · ${cluster.files.length} files</option>`;
      })
      .join("") ?? "";

  const cleanMessage = cleanResult
    ? "success" in cleanResult && cleanResult.success
      ? `<div class="notice success">Created ${escapeHtml(cleanResult.branch_name)} from ${cleanResult.included_commits} commits. Current branch: ${escapeHtml(cleanResult.current_branch)}.</div>`
      : `<div class="notice error">${escapeHtml(cleanResult.error.message)}</div>`
    : "";

  const analyzeError = payload.analyzeError
    ? `<div class="notice error">${escapeHtml(payload.analyzeError)}</div>`
    : "";

  return `<!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <style>
        :root {
          color-scheme: light dark;
        }
        body {
          font-family: var(--vscode-font-family);
          color: var(--vscode-foreground);
          background:
            radial-gradient(circle at top left, color-mix(in srgb, var(--vscode-textLink-foreground) 16%, transparent), transparent 26%),
            linear-gradient(180deg, color-mix(in srgb, var(--vscode-editor-background) 90%, black), var(--vscode-editor-background));
          margin: 0;
          padding: 20px;
        }
        code {
          font-family: var(--vscode-editor-font-family);
        }
        h1, h2, h3, p {
          margin: 0;
        }
        ul {
          margin: 0;
          padding-left: 18px;
        }
        .page {
          max-width: 1320px;
          margin: 0 auto;
          display: grid;
          gap: 16px;
        }
        .hero {
          display: grid;
          gap: 16px;
          padding: 20px;
          border: 1px solid color-mix(in srgb, var(--vscode-panel-border) 70%, transparent);
          border-radius: 16px;
          background: color-mix(in srgb, var(--vscode-sideBar-background) 65%, transparent);
          box-shadow: 0 18px 50px color-mix(in srgb, black 18%, transparent);
        }
        .hero-top {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          align-items: start;
          flex-wrap: wrap;
        }
        .hero-copy {
          display: grid;
          gap: 8px;
          max-width: 720px;
        }
        .eyebrow {
          text-transform: uppercase;
          letter-spacing: 0.08em;
          font-size: 11px;
          opacity: 0.7;
        }
        .hero h1 {
          font-size: 28px;
          line-height: 1.05;
        }
        .hero p {
          opacity: 0.86;
          line-height: 1.5;
        }
        .hero-pills {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }
        .pill {
          display: inline-flex;
          gap: 8px;
          align-items: baseline;
          padding: 8px 12px;
          border-radius: 999px;
          border: 1px solid color-mix(in srgb, var(--vscode-panel-border) 70%, transparent);
          background: color-mix(in srgb, var(--vscode-badge-background) 25%, transparent);
        }
        .pill-label, .summary-label, .metric-label, .section-label, .cluster-index {
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          opacity: 0.72;
        }
        .metric-grid, .summary-row {
          display: grid;
          gap: 12px;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        }
        .metric, .summary-item {
          padding: 14px;
          border-radius: 12px;
          border: 1px solid color-mix(in srgb, var(--vscode-panel-border) 70%, transparent);
          background: color-mix(in srgb, var(--vscode-editor-background) 82%, transparent);
          display: grid;
          gap: 6px;
        }
        .controls {
          display: grid;
          gap: 12px;
          padding: 16px;
          border: 1px solid color-mix(in srgb, var(--vscode-panel-border) 70%, transparent);
          border-radius: 14px;
          background: color-mix(in srgb, var(--vscode-editor-background) 90%, transparent);
        }
        .toolbar {
          display: flex;
          gap: 10px;
          align-items: center;
          flex-wrap: wrap;
        }
        button, select {
          background: var(--vscode-button-background);
          color: var(--vscode-button-foreground);
          border: none;
          border-radius: 10px;
          padding: 10px 14px;
        }
        button.secondary {
          background: var(--vscode-button-secondaryBackground);
          color: var(--vscode-button-secondaryForeground);
        }
        select, input {
          min-height: 40px;
        }
        select {
          background: var(--vscode-dropdown-background);
          border: 1px solid var(--vscode-dropdown-border);
          min-width: 320px;
        }
        input {
          background: var(--vscode-input-background);
          color: var(--vscode-input-foreground);
          border: 1px solid var(--vscode-input-border);
          border-radius: 10px;
          padding: 10px 12px;
          min-width: 280px;
        }
        label.toggle {
          display: inline-flex;
          gap: 8px;
          align-items: center;
          padding: 10px 12px;
          border-radius: 10px;
          border: 1px solid color-mix(in srgb, var(--vscode-panel-border) 70%, transparent);
          background: color-mix(in srgb, var(--vscode-editor-background) 82%, transparent);
        }
        .notice {
          padding: 12px 14px;
          border-radius: 12px;
          border: 1px solid transparent;
        }
        .notice.success {
          background: color-mix(in srgb, var(--vscode-testing-iconPassed) 15%, transparent);
          border-color: color-mix(in srgb, var(--vscode-testing-iconPassed) 35%, transparent);
        }
        .notice.error {
          background: color-mix(in srgb, var(--vscode-testing-iconFailed) 15%, transparent);
          border-color: color-mix(in srgb, var(--vscode-testing-iconFailed) 35%, transparent);
        }
        .content-grid {
          display: grid;
          gap: 16px;
          grid-template-columns: 1.5fr 1fr;
        }
        .stack {
          display: grid;
          gap: 16px;
        }
        .panel {
          display: grid;
          gap: 14px;
          padding: 18px;
          border-radius: 14px;
          border: 1px solid color-mix(in srgb, var(--vscode-panel-border) 70%, transparent);
          background: color-mix(in srgb, var(--vscode-sideBar-background) 45%, transparent);
        }
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }
        .badge {
          display: inline-flex;
          align-items: center;
          padding: 6px 10px;
          border-radius: 999px;
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.04em;
        }
        .badge.good {
          background: color-mix(in srgb, var(--vscode-testing-iconPassed) 18%, transparent);
          color: var(--vscode-testing-iconPassed);
        }
        .badge.warn {
          background: color-mix(in srgb, var(--vscode-testing-iconQueued) 18%, transparent);
          color: var(--vscode-testing-iconQueued);
        }
        .badge.bad {
          background: color-mix(in srgb, var(--vscode-testing-iconFailed) 18%, transparent);
          color: var(--vscode-testing-iconFailed);
        }
        .column-grid {
          display: grid;
          gap: 14px;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        }
        .column-grid.two {
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        }
        .cluster-grid {
          display: grid;
          gap: 14px;
          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        }
        .cluster-card {
          display: grid;
          gap: 12px;
          padding: 16px;
          border-radius: 14px;
          border: 1px solid color-mix(in srgb, var(--vscode-panel-border) 70%, transparent);
          background: color-mix(in srgb, var(--vscode-editor-background) 82%, transparent);
        }
        .cluster-card.selected {
          border-color: color-mix(in srgb, var(--vscode-textLink-foreground) 45%, transparent);
          box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--vscode-textLink-foreground) 25%, transparent);
        }
        .cluster-card-header {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          align-items: start;
        }
        .cluster-meta {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          font-size: 12px;
          opacity: 0.78;
        }
        .cluster-section {
          display: grid;
          gap: 8px;
        }
        .empty {
          padding: 18px;
          border-radius: 12px;
          border: 1px dashed color-mix(in srgb, var(--vscode-panel-border) 70%, transparent);
          opacity: 0.76;
        }
        @media (max-width: 1100px) {
          .content-grid {
            grid-template-columns: 1fr;
          }
        }
        @media (max-width: 720px) {
          body {
            padding: 12px;
          }
          .hero h1 {
            font-size: 22px;
          }
          .toolbar {
            align-items: stretch;
          }
          input, select, button {
            width: 100%;
          }
        }
      </style>
    </head>
    <body>
      <div class="page">
        <section class="hero">
          <div class="hero-top">
            <div class="hero-copy">
              <div class="eyebrow">Patchflow Dashboard</div>
              <h1>Turn branch drift into a clean, reviewable plan.</h1>
              <p>Analyze the current branch, pick the right cluster, preview the clean diff, and see whether GitHub is actually waiting on you.</p>
            </div>
            <div class="hero-pills">${renderPills(analyzeResult)}</div>
          </div>
          ${renderMetrics(analyzeResult)}
        </section>

        <section class="controls">
          <div class="toolbar">
            <button id="refresh">Refresh</button>
            <select id="cluster">${clusterOptions}</select>
            <button id="preview" class="secondary">Refresh Preview</button>
            <button id="clean">Create Clean Branch</button>
          </div>
          <div class="toolbar">
            <input id="prRef" type="text" value="${escapeHtml(payload.prRef ?? "")}" placeholder="PR number or GitHub pull request URL" />
            <button id="loadPr" class="secondary">Load PR</button>
            <button id="clearPr" class="secondary">Use Auto-Detect</button>
          </div>
          <div class="toolbar">
            <input id="cleanBranchName" type="text" value="${escapeHtml(payload.cleanBranchName ?? "")}" placeholder="Optional clean branch name override" />
            <label class="toggle"><input id="switchToClean" type="checkbox" ${payload.switchToClean ? "checked" : ""} /> Switch to clean branch after create</label>
          </div>
        </section>

        ${analyzeError}
        ${cleanMessage}

        <div class="content-grid">
          <div class="stack">
            <section class="panel">
              <div class="panel-header">
                <div>
                  <div class="eyebrow">Selected cluster</div>
                  <h2>Analyze</h2>
                </div>
                <span class="badge ${statusTone(analyzeResult?.status)}">${escapeHtml(analyzeResult?.status ?? "UNAVAILABLE")}</span>
              </div>
              ${renderSelectedCluster(analyzeResult)}
            </section>

            <section class="panel">
              <div class="panel-header">
                <div>
                  <div class="eyebrow">Scope map</div>
                  <h2>Clusters</h2>
                </div>
              </div>
              ${renderClusterCards(analyzeResult)}
            </section>

            <section class="panel">
              <div class="panel-header">
                <div>
                  <div class="eyebrow">Branch rebuild</div>
                  <h2>Clean Preview</h2>
                </div>
              </div>
              ${renderPreview(payload.preview, payload.previewError)}
            </section>
          </div>

          <div class="stack">
            <section class="panel">
              <div class="panel-header">
                <div>
                  <div class="eyebrow">Pull request</div>
                  <h2>PR Status</h2>
                </div>
              </div>
              ${renderStatusSummary(payload.status, payload.statusError)}
            </section>

            <section class="panel">
              <div class="panel-header">
                <div>
                  <div class="eyebrow">Environment</div>
                  <h2>Doctor</h2>
                </div>
              </div>
              ${renderDoctorSummary(payload.doctor, payload.doctorError)}
            </section>
          </div>
        </div>
      </div>
      <script>
        const vscode = acquireVsCodeApi();
        const cluster = document.getElementById("cluster");
        const prRef = document.getElementById("prRef");
        const cleanBranchName = document.getElementById("cleanBranchName");
        const switchToClean = document.getElementById("switchToClean");
        document.getElementById("refresh").addEventListener("click", () => {
          vscode.postMessage({ type: "refresh", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined, switchToClean: switchToClean.checked });
        });
        document.getElementById("preview").addEventListener("click", () => {
          vscode.postMessage({ type: "preview", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined, switchToClean: switchToClean.checked });
        });
        document.getElementById("clean").addEventListener("click", () => {
          vscode.postMessage({ type: "clean", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined, switchToClean: switchToClean.checked });
        });
        cluster.addEventListener("change", () => {
          vscode.postMessage({ type: "selectCluster", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined, switchToClean: switchToClean.checked });
        });
        document.getElementById("loadPr").addEventListener("click", () => {
          vscode.postMessage({ type: "setPr", cluster: cluster.value ? Number(cluster.value) : undefined, prRef: prRef.value || undefined, cleanBranchName: cleanBranchName.value || undefined, switchToClean: switchToClean.checked });
        });
        document.getElementById("clearPr").addEventListener("click", () => {
          prRef.value = "";
          vscode.postMessage({ type: "clearPr", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined, switchToClean: switchToClean.checked });
        });
      </script>
    </body>
  </html>`;
}
