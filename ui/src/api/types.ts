/** Shapes returned by the Taskboard API (see the API's OpenAPI document). */

export type Role = 'admin' | 'member';
export type TaskStatus = 'todo' | 'in_progress' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high';

export const TASK_STATUSES: readonly TaskStatus[] = ['todo', 'in_progress', 'done'];
export const TASK_PRIORITIES: readonly TaskPriority[] = ['low', 'medium', 'high'];
export const SORT_FIELDS = [
  'created_at',
  'updated_at',
  'title',
  'status',
  'priority',
  'due_date',
  'assignee',
] as const;
export type SortField = (typeof SORT_FIELDS)[number];

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface LoginResult {
  token: string;
  expires_at: string;
  user: User;
}

export interface Team {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
}

export interface Member {
  user_id: string;
  email: string;
  display_name: string;
  added_at: string;
}

export interface Project {
  id: string;
  team_id: string;
  name: string;
  webhook_url: string | null;
  webhook_signing_key: string | null;
  archived_at: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface TeamDetail {
  team: Team;
  members: Member[];
  projects: Project[];
}

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id: string | null;
  due_date: string | null;
  labels: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Comment {
  id: string;
  task_id: string;
  author_id: string;
  author_name: string;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: string;
  task_id: string;
  uploader_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface ActivityEvent {
  id: string;
  team_id: string;
  project_id: string | null;
  task_id: string | null;
  actor_id: string;
  actor_name: string;
  event_type: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface TaskQuery {
  q?: string;
  status?: TaskStatus;
  assignee_id?: string;
  label?: string;
  due_before?: string;
  sort?: SortField;
  order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface TaskInput {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  assignee_id?: string | null;
  due_date?: string | null;
  labels?: string[];
}

export interface ProjectUpdate {
  name?: string;
  webhook_url?: string;
  clear_webhook?: boolean;
}

export interface UploadFile {
  filename: string;
  contentType: string;
  data: Buffer;
}

/** A streamed binary response passed straight through to the browser. */
export interface BinaryResponse {
  headers: Record<string, string>;
  body: ReadableStream<Uint8Array>;
}

/** Who is calling: the browser's session token (if any) and its IP address. */
export interface Caller {
  token?: string;
  clientIp: string;
}
