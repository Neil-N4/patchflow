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
import {
  buildAnalyzeArgs,
  buildCleanArgs,
  buildStatusArgs,
  parseCleanError,
} from "./commandArgs";

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
  const { stdout } = await runPatchflowJson(buildAnalyzeArgs(clusterIndex));
  return JSON.parse(stdout) as AnalyzeResult;
}

export async function status(prRef?: string): Promise<StatusResult> {
  const { stdout } = await runPatchflowJson(buildStatusArgs(prRef));
  return JSON.parse(stdout) as StatusResult;
}

export async function cleanPreview(
  clusterIndex?: number,
  branchName?: string,
): Promise<CleanPreviewResult> {
  const { stdout } = await runPatchflowJson(
    buildCleanArgs({ clusterIndex, branchName, dryRun: true }),
  );
  return JSON.parse(stdout) as CleanPreviewResult;
}

export async function clean(
  clusterIndex?: number,
  branchName?: string,
): Promise<CleanSuccessResult | CleanErrorResult> {
  try {
    const { stdout } = await runPatchflowJson(
      buildCleanArgs({ clusterIndex, branchName }),
    );
    return JSON.parse(stdout) as CleanSuccessResult;
  } catch (error) {
    if (
      typeof error === "object" &&
      error !== null &&
      "stderr" in error &&
      typeof (error as { stderr?: string }).stderr === "string"
    ) {
      return JSON.parse(
        parseCleanError((error as { stderr: string }).stderr),
      ) as CleanErrorResult;
    }
    throw error;
  }
}
