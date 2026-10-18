import { currentRequestId } from '../logging.js';
import { ApiError, assertUuid, type FieldError } from './ApiError.js';
import type { TaskboardApi } from './TaskboardApi.js';
import type {
  ActivityEvent,
  Attachment,
  BinaryResponse,
  Caller,
  Comment,
  LoginResult,
  Member,
  Page,
  Project,
  ProjectUpdate,
  Task,
  TaskInput,
  TaskQuery,
  Team,
  TeamDetail,
  UploadFile,
  User,
} from './types.js';

type FetchFn = typeof fetch;

interface RequestOptions {
  method?: string;
  json?: unknown;
  form?: FormData;
  query?: TaskQuery | Record<string, string | number | undefined>;
}

interface ErrorBody {
  error?: { code?: string; message?: string; fields?: FieldError[] };
}

/** The only code that talks to the API: adds service auth, the user's token and the request id. */
export class HttpApiClient implements TaskboardApi {
  constructor(
    private readonly baseUrl: string,
    private readonly serviceSecret: string,
    private readonly timeoutMs: number,
    private readonly fetchFn: FetchFn = fetch,
  ) {}

  private url(path: string, query?: RequestOptions['query']): string {
    const url = new URL(`${this.baseUrl}/api/v1${path}`);
    for (const [key, value] of Object.entries(query ?? {})) {
      if (value !== undefined && value !== '') {
        url.searchParams.set(key, String(value));
      }
    }
    return url.toString();
  }

  private headers(caller: Caller): Record<string, string> {
    const headers: Record<string, string> = {
      'X-Service-Token': this.serviceSecret,
      'X-Request-ID': currentRequestId(),
      'X-Client-IP': caller.clientIp,
      Accept: 'application/json',
    };
    if (caller.token) {
      headers.Authorization = `Bearer ${caller.token}`;
    }
    return headers;
  }

  private async send(caller: Caller, path: string, options: RequestOptions): Promise<Response> {
    const headers = this.headers(caller);
    let body: string | FormData | undefined;
    if (options.json !== undefined) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(options.json);
    } else if (options.form) {
      body = options.form;
    }
    let response: Response;
    try {
      response = await this.fetchFn(this.url(path, options.query), {
        method: options.method ?? 'GET',
        headers,
        body,
        redirect: 'error',
        signal: AbortSignal.timeout(this.timeoutMs),
      });
    } catch {
      throw new ApiError(502, 'api_unavailable', 'The service is unavailable. Try again shortly.');
    }
    if (!response.ok) {
      throw await this.toError(response);
    }
    return response;
  }

  private async toError(response: Response): Promise<ApiError> {
    let body: ErrorBody;
    try {
      body = (await response.json()) as ErrorBody;
    } catch {
      body = {};
    }
    const error = body.error ?? {};
    return new ApiError(
      response.status,
      error.code ?? 'error',
      error.message ?? 'The request failed.',
      error.fields ?? [],
    );
  }

  private async json<T>(caller: Caller, path: string, options: RequestOptions = {}): Promise<T> {
    const response = await this.send(caller, path, options);
    return (await response.json()) as T;
  }

  private async empty(caller: Caller, path: string, options: RequestOptions): Promise<void> {
    await this.send(caller, path, options);
  }

  private async binary(caller: Caller, path: string): Promise<BinaryResponse> {
    const response = await this.send(caller, path, {});
    const headers: Record<string, string> = {};
    for (const name of ['content-type', 'content-disposition', 'content-length']) {
      const value = response.headers.get(name);
      if (value !== null) {
        headers[name] = value;
      }
    }
    if (!response.body) {
      throw new ApiError(502, 'api_unavailable', 'Empty response from the service.');
    }
    return { headers, body: response.body };
  }

  register(caller: Caller, email: string, displayName: string, password: string): Promise<User> {
    return this.json(caller, '/auth/register', {
      method: 'POST',
      json: { email, display_name: displayName, password },
    });
  }

  login(caller: Caller, email: string, password: string): Promise<LoginResult> {
    return this.json(caller, '/auth/login', { method: 'POST', json: { email, password } });
  }

  logout(caller: Caller): Promise<void> {
    return this.empty(caller, '/auth/logout', { method: 'POST' });
  }

  me(caller: Caller): Promise<User> {
    return this.json(caller, '/auth/me');
  }

  changePassword(caller: Caller, current: string, next: string): Promise<LoginResult> {
    return this.json(caller, '/auth/password/change', {
      method: 'POST',
      json: { current_password: current, new_password: next },
    });
  }

  forgotPassword(caller: Caller, email: string): Promise<void> {
    return this.empty(caller, '/auth/password/forgot', { method: 'POST', json: { email } });
  }

  resetPassword(caller: Caller, token: string, password: string): Promise<void> {
    return this.empty(caller, '/auth/password/reset', {
      method: 'POST',
      json: { token, new_password: password },
    });
  }

  listTeams(caller: Caller): Promise<Team[]> {
    return this.json(caller, '/teams');
  }

  createTeam(caller: Caller, name: string): Promise<Team> {
    return this.json(caller, '/teams', { method: 'POST', json: { name } });
  }

  getTeam(caller: Caller, teamId: string): Promise<TeamDetail> {
    return this.json(caller, `/teams/${assertUuid(teamId)}`);
  }

  addMember(caller: Caller, teamId: string, email: string): Promise<Member> {
    return this.json(caller, `/teams/${assertUuid(teamId)}/members`, {
      method: 'POST',
      json: { email },
    });
  }

  removeMember(caller: Caller, teamId: string, userId: string): Promise<void> {
    return this.empty(caller, `/teams/${assertUuid(teamId)}/members/${assertUuid(userId)}`, {
      method: 'DELETE',
    });
  }

  createProject(
    caller: Caller,
    teamId: string,
    name: string,
    webhookUrl?: string,
  ): Promise<Project> {
    return this.json(caller, `/teams/${assertUuid(teamId)}/projects`, {
      method: 'POST',
      json: webhookUrl ? { name, webhook_url: webhookUrl } : { name },
    });
  }

  listProjects(caller: Caller): Promise<Project[]> {
    return this.json(caller, '/projects');
  }

  getProject(caller: Caller, projectId: string): Promise<Project> {
    return this.json(caller, `/projects/${assertUuid(projectId)}`);
  }

  updateProject(caller: Caller, projectId: string, update: ProjectUpdate): Promise<Project> {
    return this.json(caller, `/projects/${assertUuid(projectId)}`, {
      method: 'PATCH',
      json: update,
    });
  }

  archiveProject(caller: Caller, projectId: string): Promise<Project> {
    return this.json(caller, `/projects/${assertUuid(projectId)}/archive`, { method: 'POST' });
  }

  listProjectTasks(caller: Caller, projectId: string, query: TaskQuery): Promise<Page<Task>> {
    return this.json(caller, `/projects/${assertUuid(projectId)}/tasks`, { query });
  }

  createTask(caller: Caller, projectId: string, input: TaskInput): Promise<Task> {
    return this.json(caller, `/projects/${assertUuid(projectId)}/tasks`, {
      method: 'POST',
      json: input,
    });
  }

  exportCsv(caller: Caller, projectId: string): Promise<BinaryResponse> {
    return this.binary(caller, `/projects/${assertUuid(projectId)}/export.csv`);
  }

  projectActivity(caller: Caller, projectId: string, page: number): Promise<Page<ActivityEvent>> {
    return this.json(caller, `/projects/${assertUuid(projectId)}/activity`, {
      query: { page, page_size: 50 },
    });
  }

  getTask(caller: Caller, taskId: string): Promise<Task> {
    return this.json(caller, `/tasks/${assertUuid(taskId)}`);
  }

  updateTask(caller: Caller, taskId: string, input: TaskInput): Promise<Task> {
    return this.json(caller, `/tasks/${assertUuid(taskId)}`, { method: 'PATCH', json: input });
  }

  deleteTask(caller: Caller, taskId: string): Promise<void> {
    return this.empty(caller, `/tasks/${assertUuid(taskId)}`, { method: 'DELETE' });
  }

  listComments(caller: Caller, taskId: string): Promise<Comment[]> {
    return this.json(caller, `/tasks/${assertUuid(taskId)}/comments`);
  }

  addComment(caller: Caller, taskId: string, body: string): Promise<Comment> {
    return this.json(caller, `/tasks/${assertUuid(taskId)}/comments`, {
      method: 'POST',
      json: { body },
    });
  }

  editComment(caller: Caller, commentId: string, body: string): Promise<Comment> {
    return this.json(caller, `/comments/${assertUuid(commentId)}`, {
      method: 'PATCH',
      json: { body },
    });
  }

  deleteComment(caller: Caller, commentId: string): Promise<void> {
    return this.empty(caller, `/comments/${assertUuid(commentId)}`, { method: 'DELETE' });
  }

  listAttachments(caller: Caller, taskId: string): Promise<Attachment[]> {
    return this.json(caller, `/tasks/${assertUuid(taskId)}/attachments`);
  }

  uploadAttachment(caller: Caller, taskId: string, file: UploadFile): Promise<Attachment> {
    const form = new FormData();
    const blob = new Blob([new Uint8Array(file.data)], { type: file.contentType });
    form.append('file', blob, file.filename);
    return this.json(caller, `/tasks/${assertUuid(taskId)}/attachments`, {
      method: 'POST',
      form,
    });
  }

  downloadAttachment(caller: Caller, attachmentId: string): Promise<BinaryResponse> {
    return this.binary(caller, `/attachments/${assertUuid(attachmentId)}/download`);
  }

  searchTasks(caller: Caller, query: TaskQuery): Promise<Page<Task>> {
    return this.json(caller, '/search/tasks', { query });
  }

  listUsers(caller: Caller, page: number): Promise<Page<User>> {
    return this.json(caller, '/admin/users', { query: { page, page_size: 50 } });
  }

  updateUser(
    caller: Caller,
    userId: string,
    update: { role?: 'admin' | 'member'; is_active?: boolean },
  ): Promise<User> {
    return this.json(caller, `/admin/users/${assertUuid(userId)}`, {
      method: 'PATCH',
      json: update,
    });
  }

  globalActivity(caller: Caller, page: number): Promise<Page<ActivityEvent>> {
    return this.json(caller, '/admin/activity', { query: { page, page_size: 50 } });
  }

  async ready(): Promise<boolean> {
    try {
      const response = await this.fetchFn(`${this.baseUrl}/readyz`, {
        signal: AbortSignal.timeout(this.timeoutMs),
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}
