export interface CommitRecord {
  commit_hash: string;
  author: string;
  message: string;
  timestamp: string;
  diff?: string | null;
}

export interface ContributorRecord {
  external_id: string;
  name: string;
  commit_count: number;
  first_seen?: string | null;
  last_seen?: string | null;
}

export interface PullRequestRecord {
  external_id: string;
  title: string;
  body?: string | null;
  author: string;
  state: string;
  created_at: string;
  merged_at?: string | null;
}

export interface IssueRecord {
  external_id: string;
  title: string;
  body?: string | null;
  author: string;
  state: string;
  created_at: string;
}

export interface TimelineEvent {
  event_type: "commit" | "pull_request" | "issue" | string;
  timestamp: string;
  title: string;
  author: string;
  summary?: string | null;
  identifier: string;
}
