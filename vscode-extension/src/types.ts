export type AnalyzeCommit = {
  sha: string;
  message: string;
  files: string[];
};

export type AnalyzeCluster = {
  index: number;
  label: string;
  score: number;
  confidence: string;
  commits: AnalyzeCommit[];
  files: string[];
};

export type AnalyzeResult = {
  schema_version: string;
  branch: {
    current: string;
    base: string;
    ahead_by: number;
    behind_by: number;
    has_uncommitted_changes: boolean;
  };
  status: string;
  confidence: string;
  selected_cluster_index: number | null;
  changed_files: string[];
  worktree_files: string[];
  other_files: string[];
  recommendations: string[];
  clusters: AnalyzeCluster[];
};

export type StatusResult = {
  schema_version: string;
  status: string;
  checks: string[];
  reviews: string[];
  branch: string[];
  conflicts: string[];
  recommendation: string;
};

export type DoctorCheck = {
  name: string;
  status: string;
  summary: string;
};

export type DoctorResult = {
  schema_version: string;
  overall_status: string;
  patchflow_version: string;
  python_version: string;
  checks: DoctorCheck[];
  branch: {
    current: string;
    base: string;
    ahead_by: number;
    behind_by: number;
    has_uncommitted_changes: boolean;
  } | null;
};

export type CleanPreviewCommit = {
  sha: string;
  message: string;
  files: string[];
};

export type CleanPreviewResult = {
  schema_version: string;
  branch_name: string;
  selected_cluster_index: number | null;
  selected_commits: CleanPreviewCommit[];
  excluded_commits: CleanPreviewCommit[];
  selected_files: string[];
  excluded_files: string[];
  safe: boolean;
};

export type CleanSuccessResult = {
  schema_version: string;
  success: true;
  branch_name: string;
  original_branch: string;
  current_branch: string;
  included_commits: number;
  included_files: number;
  safe: boolean;
};

export type CleanErrorResult = {
  schema_version: string;
  success: false;
  error: {
    code: string;
    message: string;
  };
};
