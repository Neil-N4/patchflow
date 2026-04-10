const test = require("node:test");
const assert = require("node:assert/strict");

const {
  buildAnalyzeArgs,
  buildStatusArgs,
  buildDoctorArgs,
  buildCleanArgs,
  parseCleanError,
} = require("../dist/commandArgs.js");

test("buildAnalyzeArgs includes optional cluster", () => {
  assert.deepEqual(buildAnalyzeArgs(), ["analyze", "--json"]);
  assert.deepEqual(buildAnalyzeArgs(2), ["analyze", "--json", "--cluster", "2"]);
});

test("buildStatusArgs includes optional pr ref", () => {
  assert.deepEqual(buildStatusArgs(), ["status", "--json"]);
  assert.deepEqual(buildStatusArgs("22894"), ["status", "--json", "--pr", "22894"]);
});

test("buildDoctorArgs is fixed and JSON-based", () => {
  assert.deepEqual(buildDoctorArgs(), ["doctor", "--json"]);
});

test("buildCleanArgs handles dry-run and branch overrides", () => {
  assert.deepEqual(buildCleanArgs(), ["clean", "--yes", "--json"]);
  assert.deepEqual(buildCleanArgs({ dryRun: true, clusterIndex: 3, branchName: "patchflow/clean-test" }), [
    "clean",
    "--dry-run",
    "--json",
    "--cluster",
    "3",
    "--branch-name",
    "patchflow/clean-test",
  ]);
});

test("parseCleanError strips the CLI error prefix", () => {
  assert.equal(parseCleanError('Error: {"success":false}\n'), '{"success":false}');
  assert.equal(parseCleanError('{"success":false}\n'), '{"success":false}');
});
