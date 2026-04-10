import * as vscode from "vscode";
import { analyze, clean, cleanPreview, status } from "./patchflowClient";
import type {
  AnalyzeResult,
  CleanErrorResult,
  CleanPreviewResult,
  CleanSuccessResult,
  StatusResult,
} from "./types";

type DashboardPayload = {
  analyze?: AnalyzeResult;
  preview?: CleanPreviewResult;
  status?: StatusResult;
  cleanResult?: CleanSuccessResult | CleanErrorResult;
  analyzeError?: string;
  previewError?: string;
  statusError?: string;
  prRef?: string;
  cleanBranchName?: string;
};

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderList(items: string[]): string {
  if (!items.length) {
    return "<li>none</li>";
  }
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function getHtml(webview: vscode.Webview, payload: DashboardPayload): string {
  const analyzeResult = payload.analyze;
  const preview = payload.preview;
  const statusResult = payload.status;
  const cleanResult = payload.cleanResult;
  const clusterOptions = analyzeResult?.clusters
    .map((cluster) => {
      const selected =
        analyzeResult.selected_cluster_index === cluster.index ? "selected" : "";
      return `<option value="${cluster.index}" ${selected}>[${cluster.index}] ${escapeHtml(
        cluster.label,
      )} | score=${cluster.score.toFixed(2)} | ${escapeHtml(cluster.confidence)}</option>`;
    })
    .join("") ?? "";

  const cleanMessage = cleanResult
    ? "success" in cleanResult && cleanResult.success
      ? `<div class="notice success">Created ${escapeHtml(cleanResult.branch_name)} from ${cleanResult.included_commits} commits.</div>`
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
        body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); padding: 16px; }
        .toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
        .layout { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .panel { border: 1px solid var(--vscode-panel-border); border-radius: 6px; padding: 12px; }
        h2, h3 { margin-top: 0; }
        ul { padding-left: 18px; }
        button, select { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; padding: 8px 12px; }
        input { background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 4px; padding: 8px 12px; min-width: 320px; }
        select { background: var(--vscode-dropdown-background); border: 1px solid var(--vscode-dropdown-border); }
        button.secondary { background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); }
        .notice { margin: 12px 0; padding: 10px 12px; border-radius: 6px; }
        .notice.success { background: color-mix(in srgb, var(--vscode-testing-iconPassed) 15%, transparent); }
        .notice.error { background: color-mix(in srgb, var(--vscode-testing-iconFailed) 15%, transparent); }
        code { font-family: var(--vscode-editor-font-family); }
        .muted { opacity: 0.8; }
      </style>
    </head>
    <body>
      <div class="toolbar">
        <button id="refresh">Refresh</button>
        <select id="cluster">${clusterOptions}</select>
        <button id="preview" class="secondary">Clean Preview</button>
        <button id="clean">Create Clean Branch</button>
      </div>
      <div class="toolbar">
        <input id="prRef" type="text" value="${escapeHtml(payload.prRef ?? "")}" placeholder="PR number or GitHub pull request URL" />
        <button id="loadPr" class="secondary">Load PR</button>
        <button id="clearPr" class="secondary">Auto-detect PR</button>
      </div>
      <div class="toolbar">
        <input id="cleanBranchName" type="text" value="${escapeHtml(payload.cleanBranchName ?? "")}" placeholder="Optional clean branch name override" />
      </div>
      ${analyzeError}
      ${cleanMessage}
      <div class="layout">
        <section class="panel">
          <h2>Analyze</h2>
          ${
            analyzeResult
              ? `
                <p><strong>Branch:</strong> <code>${escapeHtml(analyzeResult.branch.current)}</code></p>
                <p><strong>Base:</strong> <code>${escapeHtml(analyzeResult.branch.base)}</code></p>
                <p><strong>Status:</strong> ${escapeHtml(analyzeResult.status)} | <strong>Confidence:</strong> ${escapeHtml(analyzeResult.confidence)}</p>
                <p class="muted">Ahead ${analyzeResult.branch.ahead_by}, behind ${analyzeResult.branch.behind_by}${analyzeResult.branch.has_uncommitted_changes ? ", uncommitted changes present" : ""}</p>
                <h3>Recommendations</h3>
                <ul>${renderList(analyzeResult.recommendations)}</ul>
                <h3>Selected Cluster Files</h3>
                <ul>${renderList(
                  analyzeResult.clusters.find((cluster) => cluster.index === analyzeResult.selected_cluster_index)?.files ?? [],
                )}</ul>
                <h3>Other Changes</h3>
                <ul>${renderList(analyzeResult.other_files)}</ul>
              `
              : `<p>${escapeHtml(payload.analyzeError ?? "No analysis yet.")}</p>`
          }
        </section>
        <section class="panel">
          <h2>PR Status</h2>
          ${
            statusResult
              ? `
                <p><strong>Status:</strong> ${escapeHtml(statusResult.status)}</p>
                <p><strong>Recommendation:</strong> ${escapeHtml(statusResult.recommendation)}</p>
                <h3>Checks</h3>
                <ul>${renderList(statusResult.checks)}</ul>
                <h3>Reviews</h3>
                <ul>${renderList(statusResult.reviews)}</ul>
                <h3>Branch</h3>
                <ul>${renderList(statusResult.branch)}</ul>
                <h3>Conflicts</h3>
                <ul>${renderList(statusResult.conflicts)}</ul>
              `
              : `<p>${escapeHtml(payload.statusError ?? "No PR status available.")}</p>`
          }
        </section>
        <section class="panel">
          <h2>Clean Preview</h2>
          ${
            preview
              ? `
                <p><strong>Branch:</strong> <code>${escapeHtml(preview.branch_name)}</code></p>
                <p><strong>Selected cluster:</strong> ${preview.selected_cluster_index ?? "none"}</p>
                <h3>Selected Commits</h3>
                <ul>${renderList(preview.selected_commits.map((commit) => commit.message))}</ul>
                <h3>Selected Files</h3>
                <ul>${renderList(preview.selected_files)}</ul>
                <h3>Excluded Files</h3>
                <ul>${renderList(preview.excluded_files)}</ul>
              `
              : `<p>${escapeHtml(payload.previewError ?? "Run a clean preview to see selected and excluded changes.")}</p>`
          }
        </section>
      </div>
      <script>
        const vscode = acquireVsCodeApi();
        const cluster = document.getElementById("cluster");
        const prRef = document.getElementById("prRef");
        const cleanBranchName = document.getElementById("cleanBranchName");
        document.getElementById("refresh").addEventListener("click", () => {
          vscode.postMessage({ type: "refresh", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined });
        });
        document.getElementById("preview").addEventListener("click", () => {
          vscode.postMessage({ type: "preview", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined });
        });
        document.getElementById("clean").addEventListener("click", () => {
          vscode.postMessage({ type: "clean", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined });
        });
        cluster.addEventListener("change", () => {
          vscode.postMessage({ type: "selectCluster", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined });
        });
        document.getElementById("loadPr").addEventListener("click", () => {
          vscode.postMessage({ type: "setPr", cluster: cluster.value ? Number(cluster.value) : undefined, prRef: prRef.value || undefined, cleanBranchName: cleanBranchName.value || undefined });
        });
        document.getElementById("clearPr").addEventListener("click", () => {
          prRef.value = "";
          vscode.postMessage({ type: "clearPr", cluster: cluster.value ? Number(cluster.value) : undefined, cleanBranchName: cleanBranchName.value || undefined });
        });
      </script>
    </body>
  </html>`;
}

export class PatchflowPanel {
  private panel: vscode.WebviewPanel | undefined;
  private analyzeResult: AnalyzeResult | undefined;
  private previewResult: CleanPreviewResult | undefined;
  private statusResult: StatusResult | undefined;
  private cleanResult: CleanSuccessResult | CleanErrorResult | undefined;
  private analyzeError: string | undefined;
  private previewError: string | undefined;
  private statusError: string | undefined;
  private selectedCluster: number | undefined;
  private prRef: string | undefined;
  private cleanBranchName: string | undefined;

  constructor(private readonly context: vscode.ExtensionContext) {}

  public async open(): Promise<void> {
    if (!this.panel) {
      this.panel = vscode.window.createWebviewPanel(
        "patchflowDashboard",
        "Patchflow",
        vscode.ViewColumn.Beside,
        { enableScripts: true },
      );
      this.panel.onDidDispose(() => {
        this.panel = undefined;
      });
      this.panel.webview.onDidReceiveMessage((message) => void this.handleMessage(message));
    }
    this.panel.reveal();
    await this.refresh();
  }

  private async handleMessage(message: {
    type: string;
    cluster?: number;
    prRef?: string;
    cleanBranchName?: string;
  }): Promise<void> {
    this.selectedCluster = message.cluster;
    this.cleanBranchName = message.cleanBranchName;
    if (message.type === "setPr") {
      this.prRef = message.prRef;
      await this.refresh();
      return;
    }
    if (message.type === "clearPr") {
      this.prRef = undefined;
      await this.refresh();
      return;
    }
    if (message.type === "selectCluster") {
      await this.refresh();
      return;
    }
    if (message.type === "preview") {
      await this.refreshPreview();
      return;
    }
    if (message.type === "clean") {
      await this.runClean();
      return;
    }
    await this.refresh();
  }

  private async refresh(): Promise<void> {
    const analyzeTask = analyze(this.selectedCluster);
    const statusTask = status(this.prRef);

    try {
      this.analyzeResult = await analyzeTask;
      this.analyzeError = undefined;
    } catch (error) {
      this.analyzeResult = undefined;
      this.previewResult = undefined;
      this.analyzeError = error instanceof Error ? error.message : String(error);
      this.previewError = "Analyze must succeed before preview is available.";
    }

    try {
      this.statusResult = await statusTask;
      this.statusError = undefined;
    } catch (error) {
      this.statusResult = undefined;
      this.statusError = error instanceof Error ? error.message : String(error);
    }

    if (this.analyzeResult) {
      try {
        this.previewResult = await cleanPreview(this.selectedCluster, this.cleanBranchName);
        this.previewError = undefined;
      } catch (error) {
        this.previewResult = undefined;
        this.previewError = error instanceof Error ? error.message : String(error);
      }
    }
    this.render();
  }

  private async refreshPreview(): Promise<void> {
    try {
      this.previewResult = await cleanPreview(this.selectedCluster, this.cleanBranchName);
      this.previewError = undefined;
    } catch (error) {
      this.previewError = error instanceof Error ? error.message : String(error);
    }
    this.render();
  }

  private async runClean(): Promise<void> {
    try {
      this.cleanResult = await clean(this.selectedCluster, this.cleanBranchName);
      if ("success" in this.cleanResult && this.cleanResult.success) {
        await this.refresh();
      } else {
        this.previewError = this.cleanResult.error.message;
      }
      return;
    } catch (error) {
      this.previewError = error instanceof Error ? error.message : String(error);
    }
    this.render();
  }

  private render(): void {
    if (!this.panel) {
      return;
    }
    this.panel.webview.html = getHtml(this.panel.webview, {
      analyze: this.analyzeResult,
      preview: this.previewResult,
      status: this.statusResult,
      cleanResult: this.cleanResult,
      analyzeError: this.analyzeError,
      previewError: this.previewError,
      statusError: this.statusError,
      prRef: this.prRef,
      cleanBranchName: this.cleanBranchName,
    });
  }
}
