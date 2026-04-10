const test = require("node:test");
const assert = require("node:assert/strict");

const { formatPatchflowInvocationError } = require("../dist/clientErrors.js");

test("formatPatchflowInvocationError explains missing CLI binaries", () => {
  const message = formatPatchflowInvocationError({ code: "ENOENT" });
  assert.ok(message.includes("Patchflow CLI was not found."));
  assert.ok(message.includes("Patchflow > Cli Path"));
});

test("formatPatchflowInvocationError prefers stderr when present", () => {
  assert.equal(
    formatPatchflowInvocationError({ stderr: "fatal: bad state\n", message: "ignored" }),
    "fatal: bad state",
  );
});

test("formatPatchflowInvocationError falls back to the error message", () => {
  assert.equal(
    formatPatchflowInvocationError({ message: "plain error" }),
    "plain error",
  );
});
