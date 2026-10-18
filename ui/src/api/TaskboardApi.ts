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

/** Everything the UI can ask of the API. Controllers depend on this interface only. */
export interface TaskboardApi {
  register(caller: Caller, email: string, displayName: string, password: string): Promise<User>;
  login(caller: Caller, email: string, password: string): Promise<LoginResult>;
  logout(caller: Caller): Promise<void>;
  me(caller: Caller): Promise<User>;
  changePassword(caller: Caller, current: string, next: string): Promise<LoginResult>;
  forgotPassword(caller: Caller, email: string): Promise<void>;
  resetPassword(caller: Caller, token: string, password: string): Promise<void>;

  listTeams(caller: Caller): Promise<Team[]>;
  createTeam(caller: Caller, name: string): Promise<Team>;
  getTeam(caller: Caller, teamId: string): Promise<TeamDetail>;
  addMember(caller: Caller, teamId: string, email: string): Promise<Member>;
  removeMember(caller: Caller, teamId: string, userId: string): Promise<void>;
  createProject(
    caller: Caller,
    teamId: string,
    name: string,
    webhookUrl?: string,
  ): Promise<Project>;

  listProjects(caller: Caller): Promise<Project[]>;
  getProject(caller: Caller, projectId: string): Promise<Project>;
  updateProject(caller: Caller, projectId: string, update: ProjectUpdate): Promise<Project>;
  archiveProject(caller: Caller, projectId: string): Promise<Project>;
  listProjectTasks(caller: Caller, projectId: string, query: TaskQuery): Promise<Page<Task>>;
  createTask(caller: Caller, projectId: string, input: TaskInput): Promise<Task>;
  exportCsv(caller: Caller, projectId: string): Promise<BinaryResponse>;
  projectActivity(caller: Caller, projectId: string, page: number): Promise<Page<ActivityEvent>>;

  getTask(caller: Caller, taskId: string): Promise<Task>;
  updateTask(caller: Caller, taskId: string, input: TaskInput): Promise<Task>;
  deleteTask(caller: Caller, taskId: string): Promise<void>;
  listComments(caller: Caller, taskId: string): Promise<Comment[]>;
  addComment(caller: Caller, taskId: string, body: string): Promise<Comment>;
  editComment(caller: Caller, commentId: string, body: string): Promise<Comment>;
  deleteComment(caller: Caller, commentId: string): Promise<void>;
  listAttachments(caller: Caller, taskId: string): Promise<Attachment[]>;
  uploadAttachment(caller: Caller, taskId: string, file: UploadFile): Promise<Attachment>;
  downloadAttachment(caller: Caller, attachmentId: string): Promise<BinaryResponse>;
  searchTasks(caller: Caller, query: TaskQuery): Promise<Page<Task>>;

  listUsers(caller: Caller, page: number): Promise<Page<User>>;
  updateUser(
    caller: Caller,
    userId: string,
    update: { role?: 'admin' | 'member'; is_active?: boolean },
  ): Promise<User>;
  globalActivity(caller: Caller, page: number): Promise<Page<ActivityEvent>>;

  ready(): Promise<boolean>;
}
