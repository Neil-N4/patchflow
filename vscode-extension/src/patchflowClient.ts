import { execFile } from "node:child_process";
import { promisify } from "node:util";
import * as vscode from "vscode";
import type {
  AnalyzeResult,
  CleanErrorResult,
  CleanPreviewResult,
  CleanSuccessResult,
  StatusResult,
} from "./types";

const execFileAsync = promisify(execFile);

function getWorkspaceFolder(): string {
  const folder = vscode.workspace.workspaceFolders?.[0];
  if (!folder) {
    throw new Error("Open a workspace folder to use Patchflow.");
  }
  return folder.uri.fsPath;
}

async function runPatchflowJson(
  args: string[],
): Promise<{ stdout: string; stderr: string }> {
  const cwd = getWorkspaceFolder();
  return execFileAsync("patchflow", args, { cwd });
}

export async function analyze(clusterIndex?: number): Promise<AnalyzeResult> {
  const args = ["analyze", "--json"];
  if (clusterIndex !== undefined) {
    args.push("--cluster", String(clusterIndex));
  }
  const { stdout } = await runPatchflowJson(args);
  return JSON.parse(stdout) as AnalyzeResult;
}

export async function status(prRef?: string): Promise<StatusResult> {
  const args = ["status", "--json"];
  if (prRef) {
    args.push("--pr", prRef);
  }
  const { stdout } = await runPatchflowJson(args);
  return JSON.parse(stdout) as StatusResult;
}

export async function cleanPreview(
  clusterIndex?: number,
): Promise<CleanPreviewResult> {
  const args = ["clean", "--dry-run", "--json"];
  if (clusterIndex !== undefined) {
    args.push("--cluster", String(clusterIndex));
  }
  const { stdout } = await runPatchflowJson(args);
  return JSON.parse(stdout) as CleanPreviewResult;
}

export async function clean(
  clusterIndex?: number,
): Promise<CleanSuccessResult | CleanErrorResult> {
  const args = ["clean", "--yes", "--json"];
  if (clusterIndex !== undefined) {
    args.push("--cluster", String(clusterIndex));
  }
  try {
    const { stdout } = await runPatchflowJson(args);
    return JSON.parse(stdout) as CleanSuccessResult;
  } catch (error) {
    if (
      typeof error === "object" &&
      error !== null &&
      "stderr" in error &&
      typeof (error as { stderr?: string }).stderr === "string"
    ) {
      const stderr = (error as { stderr: string }).stderr;
      const prefix = "Error: ";
      const raw = stderr.startsWith(prefix) ? stderr.slice(prefix.length) : stderr;
      return JSON.parse(raw) as CleanErrorResult;
    }
    throw error;
  }
}
