import { ApiError, assertUuid } from '../src/api/ApiError.js';
import type { TaskboardApi } from '../src/api/TaskboardApi.js';
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
} from '../src/api/types.js';

export const IDS = {
  user: '11111111-1111-4111-8111-111111111111',
  admin: '22222222-2222-4222-8222-222222222222',
  team: '33333333-3333-4333-8333-333333333333',
  project: '44444444-4444-4444-8444-444444444444',
  task: '55555555-5555-4555-8555-555555555555',
  comment: '66666666-6666-4666-8666-666666666666',
  attachment: '77777777-7777-4777-8777-777777777777',
};

const NOW = '2026-10-18T09:00:00Z';

export const member: User = {
  id: IDS.user,
  email: 'mo@example.test',
  display_name: 'Mo',
  role: 'member',
  is_active: true,
  created_at: NOW,
};
export const admin: User = { ...member, id: IDS.admin, email: 'root@example.test', role: 'admin' };

export const team: Team = { id: IDS.team, name: 'Core', owner_id: IDS.user, created_at: NOW };
export const project: Project = {
  id: IDS.project,
  team_id: IDS.team,
  name: 'Board',
  webhook_url: 'https://hooks.example.test/x',
  webhook_signing_key: 'signing-key',
  archived_at: null,
  is_archived: false,
  created_at: NOW,
  updated_at: NOW,
};
export const task: Task = {
  id: IDS.task,
  project_id: IDS.project,
  title: 'Write docs',
  description: '**bold** <script>alert(1)</script> [x](javascript:alert(2))',
  status: 'todo',
  priority: 'high',
  assignee_id: IDS.user,
  due_date: '2026-11-01',
  labels: ['docs'],
  created_by: IDS.user,
  created_at: NOW,
  updated_at: NOW,
};
const membersList: Member[] = [
  { user_id: IDS.user, email: member.email, display_name: 'Mo', added_at: NOW },
];

function page<T>(items: T[]): Page<T> {
  return { items, total: items.length, page: 1, page_size: 50 };
}

function stream(text: string): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(text));
      controller.close();
    },
  });
}

/** In-memory TaskboardApi: tokens "member-token" and "admin-token" are signed in. */
export class FakeApi implements TaskboardApi {
  readonly calls: { method: string; args: unknown[] }[] = [];
  private failures = new Map<string, ApiError>();
  readyState = true;

  failNext(method: string, error: ApiError): void {
    this.failures.set(method, error);
  }

  private async record(method: string, ...args: unknown[]): Promise<void> {
    this.calls.push({ method, args });
    const failure = this.failures.get(method);
    if (failure) {
      this.failures.delete(method);
      await Promise.reject(failure);
    }
  }

  called(method: string): unknown[][] {
    return this.calls.filter((c) => c.method === method).map((c) => c.args);
  }

  async register(caller: Caller, email: string, name: string, password: string): Promise<User> {
    await this.record('register', caller, email, name, password);
    return { ...member, email, display_name: name };
  }
  async login(caller: Caller, email: string, password: string): Promise<LoginResult> {
    await this.record('login', caller, email, password);
    if (password !== 'correct-horse-battery') {
      throw new ApiError(401, 'invalid_credentials', 'Invalid email or password.');
    }
    const user = email.startsWith('root') ? admin : member;
    const token = user.role === 'admin' ? 'admin-token' : 'member-token';
    return { token, expires_at: '2099-01-01T00:00:00Z', user };
  }
  async logout(caller: Caller): Promise<void> {
    await this.record('logout', caller);
  }
  async me(caller: Caller): Promise<User> {
    await this.record('me', caller);
    if (caller.token === 'member-token') return member;
    if (caller.token === 'admin-token') return admin;
    throw new ApiError(401, 'authentication_required', 'Authentication required.');
  }
  async changePassword(caller: Caller, current: string, next: string): Promise<LoginResult> {
    await this.record('changePassword', caller, current, next);
    return { token: 'member-token', expires_at: '2099-01-01T00:00:00Z', user: member };
  }
  async forgotPassword(caller: Caller, email: string): Promise<void> {
    await this.record('forgotPassword', caller, email);
  }
  async resetPassword(caller: Caller, token: string, password: string): Promise<void> {
    await this.record('resetPassword', caller, token, password);
  }
  async listTeams(caller: Caller): Promise<Team[]> {
    await this.record('listTeams', caller);
    return [team];
  }
  async createTeam(caller: Caller, name: string): Promise<Team> {
    await this.record('createTeam', caller, name);
    return { ...team, name };
  }
  async getTeam(caller: Caller, teamId: string): Promise<TeamDetail> {
    await this.record('getTeam', caller, teamId);
    return { team, members: membersList, projects: [project] };
  }
  async addMember(caller: Caller, teamId: string, email: string): Promise<Member> {
    await this.record('addMember', caller, teamId, email);
    return { user_id: IDS.admin, email, display_name: 'Ada', added_at: NOW };
  }
  async removeMember(caller: Caller, teamId: string, userId: string): Promise<void> {
    await this.record('removeMember', caller, teamId, userId);
  }
  async createProject(c: Caller, teamId: string, name: string, url?: string): Promise<Project> {
    await this.record('createProject', c, teamId, name, url);
    return { ...project, name };
  }
  async listProjects(caller: Caller): Promise<Project[]> {
    await this.record('listProjects', caller);
    return [project];
  }
  async getProject(caller: Caller, projectId: string): Promise<Project> {
    assertUuid(projectId);
    await this.record('getProject', caller, projectId);
    return project;
  }
  async updateProject(c: Caller, projectId: string, update: ProjectUpdate): Promise<Project> {
    await this.record('updateProject', c, projectId, update);
    return project;
  }
  async archiveProject(caller: Caller, projectId: string): Promise<Project> {
    await this.record('archiveProject', caller, projectId);
    return { ...project, is_archived: true, archived_at: NOW };
  }
  async listProjectTasks(c: Caller, projectId: string, query: TaskQuery): Promise<Page<Task>> {
    await this.record('listProjectTasks', c, projectId, query);
    return page([task, { ...task, id: IDS.comment, status: 'done' }]);
  }
  async createTask(caller: Caller, projectId: string, input: TaskInput): Promise<Task> {
    await this.record('createTask', caller, projectId, input);
    return { ...task, title: input.title ?? task.title };
  }
  async exportCsv(caller: Caller, projectId: string): Promise<BinaryResponse> {
    await this.record('exportCsv', caller, projectId);
    return {
      headers: {
        'content-type': 'text/csv; charset=utf-8',
        'content-disposition': 'attachment; filename="project.csv"',
      },
      body: stream('id,title\r\n'),
    };
  }
  async projectActivity(c: Caller, projectId: string, n: number): Promise<Page<ActivityEvent>> {
    await this.record('projectActivity', c, projectId, n);
    return page([
      {
        id: IDS.comment,
        team_id: IDS.team,
        project_id: IDS.project,
        task_id: IDS.task,
        actor_id: IDS.user,
        actor_name: 'Mo',
        event_type: 'status_changed',
        details: { title: 'Write docs', old_status: 'todo', new_status: 'done' },
        created_at: NOW,
      },
    ]);
  }
  async getTask(caller: Caller, taskId: string): Promise<Task> {
    await this.record('getTask', caller, taskId);
    return task;
  }
  async updateTask(caller: Caller, taskId: string, input: TaskInput): Promise<Task> {
    await this.record('updateTask', caller, taskId, input);
    return task;
  }
  async deleteTask(caller: Caller, taskId: string): Promise<void> {
    await this.record('deleteTask', caller, taskId);
  }
  async listComments(caller: Caller, taskId: string): Promise<Comment[]> {
    await this.record('listComments', caller, taskId);
    return [
      {
        id: IDS.comment,
        task_id: IDS.task,
        author_id: IDS.user,
        author_name: 'Mo',
        body: 'Looks <img src=x onerror=alert(3)> good',
        created_at: NOW,
        updated_at: NOW,
      },
    ];
  }
  async addComment(caller: Caller, taskId: string, body: string): Promise<Comment> {
    await this.record('addComment', caller, taskId, body);
    return (await this.listComments(caller, taskId))[0] as Comment;
  }
  async editComment(caller: Caller, commentId: string, body: string): Promise<Comment> {
    await this.record('editComment', caller, commentId, body);
    return (await this.listComments(caller, IDS.task))[0] as Comment;
  }
  async deleteComment(caller: Caller, commentId: string): Promise<void> {
    await this.record('deleteComment', caller, commentId);
  }
  async listAttachments(caller: Caller, taskId: string): Promise<Attachment[]> {
    await this.record('listAttachments', caller, taskId);
    return [
      {
        id: IDS.attachment,
        task_id: IDS.task,
        uploader_id: IDS.user,
        filename: 'notes.txt',
        content_type: 'text/plain',
        size_bytes: 2048,
        created_at: NOW,
      },
    ];
  }
  async uploadAttachment(caller: Caller, taskId: string, file: UploadFile): Promise<Attachment> {
    await this.record('uploadAttachment', caller, taskId, file);
    return (await this.listAttachments(caller, taskId))[0] as Attachment;
  }
  async downloadAttachment(caller: Caller, attachmentId: string): Promise<BinaryResponse> {
    await this.record('downloadAttachment', caller, attachmentId);
    return {
      headers: {
        'content-type': 'application/octet-stream',
        'content-disposition': 'attachment; filename="notes.txt"',
        'content-length': '5',
      },
      body: stream('hello'),
    };
  }
  async searchTasks(caller: Caller, query: TaskQuery): Promise<Page<Task>> {
    await this.record('searchTasks', caller, query);
    return { items: [task], total: 60, page: query.page ?? 1, page_size: 25 };
  }
  async listUsers(caller: Caller, n: number): Promise<Page<User>> {
    await this.record('listUsers', caller, n);
    return page([admin, member]);
  }
  async updateUser(
    caller: Caller,
    userId: string,
    update: { role?: 'admin' | 'member'; is_active?: boolean },
  ): Promise<User> {
    await this.record('updateUser', caller, userId, update);
    return member;
  }
  async globalActivity(caller: Caller, n: number): Promise<Page<ActivityEvent>> {
    await this.record('globalActivity', caller, n);
    return this.projectActivity(caller, IDS.project, n);
  }
  ready(): Promise<boolean> {
    return Promise.resolve(this.readyState);
  }
}
