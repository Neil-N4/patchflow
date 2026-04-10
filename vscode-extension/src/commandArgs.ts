export function buildAnalyzeArgs(clusterIndex?: number): string[] {
  const args = ["analyze", "--json"];
  if (clusterIndex !== undefined) {
    args.push("--cluster", String(clusterIndex));
  }
  return args;
}

export function buildStatusArgs(prRef?: string): string[] {
  const args = ["status", "--json"];
  if (prRef) {
    args.push("--pr", prRef);
  }
  return args;
}

export function buildCleanArgs(options?: {
  clusterIndex?: number;
  branchName?: string;
  dryRun?: boolean;
}): string[] {
  const args = ["clean"];
  if (options?.dryRun) {
    args.push("--dry-run");
  } else {
    args.push("--yes");
  }
  args.push("--json");
  if (options?.clusterIndex !== undefined) {
    args.push("--cluster", String(options.clusterIndex));
  }
  if (options?.branchName) {
    args.push("--branch-name", options.branchName);
  }
  return args;
}

export function parseCleanError(stderr: string): string {
  const trimmed = stderr.trim();
  const prefix = "Error: ";
  return trimmed.startsWith(prefix) ? trimmed.slice(prefix.length) : trimmed;
}
