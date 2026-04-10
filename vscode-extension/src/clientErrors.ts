export function formatPatchflowInvocationError(error: unknown): string {
  if (typeof error === "object" && error !== null) {
    const candidate = error as {
      code?: string;
      stderr?: string;
      message?: string;
    };
    if (candidate.code === "ENOENT") {
      return [
        "Patchflow CLI was not found.",
        "Install Patchflow in your current environment or set Patchflow > Cli Path in VS Code settings.",
      ].join(" ");
    }
    if (candidate.stderr && candidate.stderr.trim()) {
      return candidate.stderr.trim();
    }
    if (candidate.message) {
      return candidate.message;
    }
  }
  return String(error);
}
