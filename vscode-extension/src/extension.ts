import * as vscode from "vscode";
import { PatchflowPanel } from "./webview";

export function activate(context: vscode.ExtensionContext): void {
  const panel = new PatchflowPanel(context);
  const disposable = vscode.commands.registerCommand("patchflow.open", async () => {
    await panel.open();
  });
  context.subscriptions.push(disposable);
}

export function deactivate(): void {
  // No-op.
}
