import { Readable } from 'node:stream';
import type { Request, Response, Router } from 'express';
import type { BinaryResponse } from '../api/types.js';
import { callerOf, field, param, userOf } from '../http/context.js';
import { requireUser } from '../http/middleware.js';
import { Controller } from './Controller.js';
import { readTaskForm } from './forms.js';

/** Streams an API file response to the browser as a download that can never render inline. */
export function sendDownload(res: Response, file: BinaryResponse, fallbackType: string): void {
  const disposition = file.headers['content-disposition'] ?? '';
  res.status(200);
  res.setHeader('Content-Type', file.headers['content-type'] ?? fallbackType);
  res.setHeader(
    'Content-Disposition',
    disposition.startsWith('attachment') ? disposition : 'attachment',
  );
  if (file.headers['content-length']) {
    res.setHeader('Content-Length', file.headers['content-length']);
  }
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Content-Security-Policy', "sandbox; default-src 'none'");
  Readable.fromWeb(file.body).pipe(res);
}

/** Project board: tasks by status, creating tasks, settings, archive, CSV export, activity. */
export class ProjectController extends Controller {
  register(router: Router): void {
    const back = (req: Request): string =>
      `/projects/${encodeURIComponent(param(req, 'projectId'))}`;
    router.get(
      '/projects/:projectId',
      requireUser(),
      this.page((req, res) => this.show(req, res)),
    );
    router.post(
      '/projects/:projectId/tasks',
      requireUser(),
      this.form((req, res) => this.createTask(req, res), back),
    );
    router.post(
      '/projects/:projectId/settings',
      requireUser(),
      this.form((req, res) => this.updateSettings(req, res), back),
    );
    router.post(
      '/projects/:projectId/archive',
      requireUser(),
      this.form((req, res) => this.archive(req, res), back),
    );
    router.get(
      '/projects/:projectId/export.csv',
      requireUser(),
      this.page((req, res) => this.exportCsv(req, res)),
    );
  }

  private async show(req: Request, res: Response): Promise<void> {
    const caller = callerOf(req, res);
    const projectId = param(req, 'projectId');
    const project = await this.deps.api.getProject(caller, projectId);
    const [detail, tasks, activity] = await Promise.all([
      this.deps.api.getTeam(caller, project.team_id),
      this.deps.api.listProjectTasks(caller, project.id, {
        sort: 'priority',
        order: 'desc',
        page_size: 200,
      }),
      this.deps.api.projectActivity(caller, project.id, 1),
    ]);
    res.render('project', {
      title: project.name,
      project,
      team: detail.team,
      members: detail.members,
      columns: this.deps.views.board(tasks.items, detail.members),
      activity: this.deps.views.activity(activity.items),
      canManage: this.deps.views.canManageTeam(userOf(res), detail),
    });
  }

  private async createTask(req: Request, res: Response): Promise<void> {
    const projectId = param(req, 'projectId');
    const task = await this.deps.api.createTask(callerOf(req, res), projectId, readTaskForm(req));
    this.done(res, `Task "${task.title}" created.`, `/projects/${projectId}`);
  }

  private async updateSettings(req: Request, res: Response): Promise<void> {
    const projectId = param(req, 'projectId');
    const webhook = field(req, 'webhook_url').trim();
    const clear = field(req, 'clear_webhook') === 'on';
    await this.deps.api.updateProject(callerOf(req, res), projectId, {
      name: field(req, 'name'),
      ...(clear ? { clear_webhook: true } : webhook ? { webhook_url: webhook } : {}),
    });
    this.done(res, 'Project settings saved.', `/projects/${projectId}`);
  }

  private async archive(req: Request, res: Response): Promise<void> {
    const projectId = param(req, 'projectId');
    await this.deps.api.archiveProject(callerOf(req, res), projectId);
    this.done(res, 'Project archived. It is now read-only.', `/projects/${projectId}`);
  }

  private async exportCsv(req: Request, res: Response): Promise<void> {
    const file = await this.deps.api.exportCsv(callerOf(req, res), param(req, 'projectId'));
    sendDownload(res, file, 'text/csv; charset=utf-8');
  }
}
