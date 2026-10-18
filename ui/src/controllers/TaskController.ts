import type { NextFunction, Request, RequestHandler, Response, Router } from 'express';
import multer from 'multer';
import { isUuid } from '../api/ApiError.js';
import { callerOf, field, param, userOf } from '../http/context.js';
import { requireUser } from '../http/middleware.js';
import type { CsrfProtection } from '../security/CsrfProtection.js';
import { Controller, type ControllerDeps } from './Controller.js';
import { readTaskForm } from './forms.js';
import { sendDownload } from './ProjectController.js';

/** Task detail: editing, deleting, comments and attachments. */
export class TaskController extends Controller {
  private readonly upload: RequestHandler;

  constructor(
    deps: ControllerDeps,
    private readonly csrf: CsrfProtection,
  ) {
    super(deps);
    // One file, held in memory up to the limit, then forwarded to the API (which re-checks size).
    this.upload = multer({
      storage: multer.memoryStorage(),
      limits: { fileSize: deps.maxUploadBytes, files: 1, fields: 4, parts: 5 },
    }).single('file');
  }

  register(router: Router): void {
    const back = (req: Request): string => `/tasks/${encodeURIComponent(param(req, 'taskId'))}`;
    const backFromComment = (req: Request): string => {
      const taskId = field(req, 'task_id');
      return isUuid(taskId) ? `/tasks/${taskId}` : '/dashboard';
    };
    router.get(
      '/tasks/:taskId',
      requireUser(),
      this.page((req, res) => this.show(req, res)),
    );
    router.post(
      '/tasks/:taskId',
      requireUser(),
      this.form((req, res) => this.update(req, res), back),
    );
    router.post(
      '/tasks/:taskId/delete',
      requireUser(),
      this.form((req, res) => this.remove(req, res), back),
    );
    router.post(
      '/tasks/:taskId/comments',
      requireUser(),
      this.form((req, res) => this.comment(req, res), back),
    );
    router.post(
      '/comments/:commentId',
      requireUser(),
      this.form((req, res) => this.editComment(req, res), backFromComment),
    );
    router.post(
      '/comments/:commentId/delete',
      requireUser(),
      this.form((req, res) => this.deleteComment(req, res), backFromComment),
    );
    router.post(
      '/tasks/:taskId/attachments',
      requireUser(),
      this.parseUpload(back),
      this.csrf.verifyParsed(),
      this.form((req, res) => this.uploadFile(req, res), back),
    );
    router.get(
      '/attachments/:attachmentId/download',
      requireUser(),
      this.page((req, res) => this.download(req, res)),
    );
  }

  /** Runs multer and turns its limit errors into a friendly message. */
  private parseUpload(back: (req: Request) => string): RequestHandler {
    return (req: Request, res: Response, next: NextFunction) => {
      this.upload(req, res, (error: unknown) => {
        if (error instanceof multer.MulterError) {
          const limitMb = Math.floor(this.deps.maxUploadBytes / (1024 * 1024));
          const message =
            error.code === 'LIMIT_FILE_SIZE'
              ? `Attachments are limited to ${String(limitMb)} MB.`
              : 'The upload could not be processed.';
          this.deps.flash.set(res, 'error', message);
          res.redirect(303, back(req));
          return;
        }
        next(error);
      });
    };
  }

  private async show(req: Request, res: Response): Promise<void> {
    const caller = callerOf(req, res);
    const task = await this.deps.api.getTask(caller, param(req, 'taskId'));
    const project = await this.deps.api.getProject(caller, task.project_id);
    const [detail, comments, attachments] = await Promise.all([
      this.deps.api.getTeam(caller, project.team_id),
      this.deps.api.listComments(caller, task.id),
      this.deps.api.listAttachments(caller, task.id),
    ]);
    res.render('task', {
      title: task.title,
      project,
      members: detail.members,
      assigneeName: this.deps.views.memberNames(detail.members).get(task.assignee_id ?? '') ?? '',
      ...this.deps.views.taskDetail(task, comments, attachments, userOf(res)),
    });
  }

  private async update(req: Request, res: Response): Promise<void> {
    const taskId = param(req, 'taskId');
    await this.deps.api.updateTask(callerOf(req, res), taskId, readTaskForm(req));
    this.done(res, 'Task saved.', `/tasks/${taskId}`);
  }

  private async remove(req: Request, res: Response): Promise<void> {
    const caller = callerOf(req, res);
    const task = await this.deps.api.getTask(caller, param(req, 'taskId'));
    await this.deps.api.deleteTask(caller, task.id);
    this.done(res, 'Task deleted.', `/projects/${task.project_id}`);
  }

  private async comment(req: Request, res: Response): Promise<void> {
    const taskId = param(req, 'taskId');
    await this.deps.api.addComment(callerOf(req, res), taskId, field(req, 'body'));
    this.done(res, 'Comment added.', `/tasks/${taskId}`);
  }

  private async editComment(req: Request, res: Response): Promise<void> {
    const comment = await this.deps.api.editComment(
      callerOf(req, res),
      param(req, 'commentId'),
      field(req, 'body'),
    );
    this.done(res, 'Comment updated.', `/tasks/${comment.task_id}`);
  }

  private async deleteComment(req: Request, res: Response): Promise<void> {
    await this.deps.api.deleteComment(callerOf(req, res), param(req, 'commentId'));
    const taskId = field(req, 'task_id');
    this.done(res, 'Comment deleted.', isUuid(taskId) ? `/tasks/${taskId}` : '/dashboard');
  }

  private async uploadFile(req: Request, res: Response): Promise<void> {
    const taskId = param(req, 'taskId');
    const file = req.file;
    if (!file) {
      this.deps.flash.set(res, 'error', 'Choose a file to upload.');
      res.redirect(303, `/tasks/${encodeURIComponent(taskId)}`);
      return;
    }
    const attachment = await this.deps.api.uploadAttachment(callerOf(req, res), taskId, {
      filename: file.originalname,
      contentType: file.mimetype,
      data: file.buffer,
    });
    this.done(res, `Attached ${attachment.filename}.`, `/tasks/${taskId}`);
  }

  private async download(req: Request, res: Response): Promise<void> {
    const file = await this.deps.api.downloadAttachment(
      callerOf(req, res),
      param(req, 'attachmentId'),
    );
    sendDownload(res, file, 'application/octet-stream');
  }
}
