import type {
  ActivityEvent,
  Attachment,
  Comment,
  Member,
  Project,
  Task,
  TaskStatus,
  TeamDetail,
  User,
} from '../api/types.js';
import type { MarkdownRenderer } from '../security/MarkdownRenderer.js';

export const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'To do',
  in_progress: 'In progress',
  done: 'Done',
};

export interface BoardColumn {
  status: TaskStatus;
  label: string;
  tasks: (Task & { assigneeName: string })[];
}

export interface CommentView extends Comment {
  bodyHtml: string;
  canEdit: boolean;
}

export interface ActivityLine {
  when: string;
  actor: string;
  text: string;
}

/** Turns API data into what the templates need, keeping logic out of the views. */
export class ViewModels {
  constructor(private readonly markdown: MarkdownRenderer) {}

  memberNames(members: Member[]): Map<string, string> {
    return new Map(members.map((m) => [m.user_id, m.display_name]));
  }

  canManageTeam(user: User, detail: TeamDetail): boolean {
    return user.role === 'admin' || detail.team.owner_id === user.id;
  }

  board(tasks: Task[], members: Member[]): BoardColumn[] {
    const names = this.memberNames(members);
    return (Object.keys(STATUS_LABELS) as TaskStatus[]).map((status) => ({
      status,
      label: STATUS_LABELS[status],
      tasks: tasks
        .filter((t) => t.status === status)
        .map((t) => ({
          ...t,
          assigneeName: t.assignee_id ? (names.get(t.assignee_id) ?? '') : '',
        })),
    }));
  }

  /** Markdown is rendered and sanitized here; templates print `*Html` fields unescaped. */
  taskDetail(task: Task, comments: Comment[], attachments: Attachment[], user: User) {
    return {
      task,
      descriptionHtml: this.markdown.render(task.description),
      comments: comments.map((c): CommentView => ({
        ...c,
        bodyHtml: this.markdown.render(c.body),
        canEdit: c.author_id === user.id,
      })),
      attachments: attachments.map((a) => ({ ...a, size: this.humanSize(a.size_bytes) })),
    };
  }

  activity(events: ActivityEvent[]): ActivityLine[] {
    return events.map((e) => ({
      when: e.created_at.slice(0, 16).replace('T', ' '),
      actor: e.actor_name,
      text: this.describe(e),
    }));
  }

  projectsByTeam(projects: Project[]): Map<string, Project[]> {
    const grouped = new Map<string, Project[]>();
    for (const project of projects) {
      grouped.set(project.team_id, [...(grouped.get(project.team_id) ?? []), project]);
    }
    return grouped;
  }

  humanSize(bytes: number): string {
    if (bytes < 1024) {
      return `${String(bytes)} B`;
    }
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  private describe(e: ActivityEvent): string {
    const text = (key: string): string => {
      const value = e.details[key];
      return typeof value === 'string' ? value : '';
    };
    switch (e.event_type) {
      case 'task_created':
        return `created task "${text('title')}"`;
      case 'task_updated':
        return `updated task "${text('title')}"`;
      case 'status_changed':
        return `moved "${text('title')}" from ${text('old_status')} to ${text('new_status')}`;
      case 'comment_added':
        return `commented on "${text('title')}"`;
      case 'attachment_added':
        return `attached ${text('filename')} to "${text('title')}"`;
      case 'member_added':
        return `added ${text('display_name')} to the team`;
      case 'member_removed':
        return `removed ${text('display_name')} from the team`;
      default:
        return e.event_type;
    }
  }
}
