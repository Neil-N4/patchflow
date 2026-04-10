import * as vscode from "vscode";
import { analyze, clean, cleanPreview, status } from "./patchflowClient";
import type {
  AnalyzeResult,
  CleanErrorResult,
  CleanPreviewResult,
  CleanSuccessResult,
  StatusResult,
} from "./types";
import { renderDashboardHtml } from "./dashboard";

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
    this.panel.webview.html = renderDashboardHtml({
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
