const test = require("node:test");
const assert = require("node:assert/strict");

const { renderDashboardHtml } = require("../dist/dashboard.js");

test("renderDashboardHtml escapes user-provided values and marks the selected cluster", () => {
  const html = renderDashboardHtml({
    prRef: '42"><script>alert(1)</script>',
    cleanBranchName: "patchflow/clean-demo",
    switchToClean: true,
    analyze: {
      schema_version: "1",
      branch: {
        current: "feature/demo",
        base: "main",
        ahead_by: 2,
        behind_by: 1,
        has_uncommitted_changes: false,
      },
      status: "DIRTY",
      confidence: "MEDIUM",
      selected_cluster_index: 2,
      changed_files: ["src/app.ts"],
      worktree_files: [],
      other_files: ["README.md"],
      recommendations: ["clean branch", "update branch"],
      clusters: [
        {
          index: 1,
          label: "docs-only",
          score: 1.25,
          confidence: "LOW",
          commits: [],
          files: ["README.md"],
        },
        {
          index: 2,
          label: "feature<main>",
          score: 12.5,
          confidence: "MEDIUM",
          commits: [{ sha: "abc123", message: "feat: add <thing>", files: ["src/app.ts"] }],
          files: ["src/app.ts"],
        },
      ],
    },
    preview: {
      schema_version: "1",
      branch_name: "patchflow/clean-demo",
      selected_cluster_index: 2,
      selected_commits: [{ sha: "abc123", message: "feat: add <thing>", files: ["src/app.ts"] }],
      excluded_commits: [],
      selected_files: ["src/app.ts"],
      excluded_files: ["README.md"],
      safe: true,
    },
    status: {
      schema_version: "1",
      status: "BLOCKED",
      checks: ["CI waiting"],
      reviews: ["Code owner review required"],
      branch: ["behind main by 1"],
      conflicts: [],
      recommendation: "wait",
    },
    doctor: {
      schema_version: "1",
      overall_status: "WARN",
      patchflow_version: "0.1.0",
      python_version: "3.13.0",
      branch: {
        current: "feature/demo",
        base: "main",
        ahead_by: 2,
        behind_by: 1,
        has_uncommitted_changes: false,
      },
      checks: [
        { name: "git", status: "OK", summary: "git version 2.x" },
        { name: "github_auth", status: "WARN", summary: "No token detected" },
      ],
    },
  });

  assert.match(html, /value="2" selected/);
  assert.ok(html.includes("feature&lt;main&gt;"));
  assert.ok(html.includes("feat: add &lt;thing&gt;"));
  assert.ok(html.includes('42&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;'));
  assert.ok(!html.includes("<script>alert(1)</script>"));
  assert.ok(html.includes("Created patchflow/clean-demo from 1 commits.") === false);
  assert.ok(html.includes("[WARN] github_auth: No token detected"));
  assert.ok(html.includes("Switch to clean branch"));
  assert.ok(html.includes("checked"));
});

test("renderDashboardHtml shows clean success messages", () => {
  const html = renderDashboardHtml({
    cleanResult: {
      schema_version: "1",
      success: true,
      branch_name: "patchflow/clean-fix",
      original_branch: "feature/fix",
      current_branch: "patchflow/clean-fix",
      included_commits: 2,
      included_files: 3,
      safe: true,
    },
  });

  assert.ok(html.includes("Created patchflow/clean-fix from 2 commits. Current branch: patchflow/clean-fix."));
});
