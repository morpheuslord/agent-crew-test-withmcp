import type { Request, Response, Router } from 'express';
import { callerOf, field, param, userOf } from '../http/context.js';
import { requireUser } from '../http/middleware.js';
import { Controller } from './Controller.js';

/** Team page: members, adding and removing members, creating projects. */
export class TeamController extends Controller {
  register(router: Router): void {
    const back = (req: Request): string => `/teams/${encodeURIComponent(param(req, 'teamId'))}`;
    router.get(
      '/teams/:teamId',
      requireUser(),
      this.page((req, res) => this.show(req, res)),
    );
    router.post(
      '/teams/:teamId/members',
      requireUser(),
      this.form((req, res) => this.addMember(req, res), back),
    );
    router.post(
      '/teams/:teamId/members/:userId/remove',
      requireUser(),
      this.form((req, res) => this.removeMember(req, res), back),
    );
    router.post(
      '/teams/:teamId/projects',
      requireUser(),
      this.form((req, res) => this.createProject(req, res), back),
    );
  }

  private async show(req: Request, res: Response): Promise<void> {
    const detail = await this.deps.api.getTeam(callerOf(req, res), param(req, 'teamId'));
    res.render('team', {
      title: detail.team.name,
      detail,
      canManage: this.deps.views.canManageTeam(userOf(res), detail),
    });
  }

  private async addMember(req: Request, res: Response): Promise<void> {
    const teamId = param(req, 'teamId');
    const member = await this.deps.api.addMember(callerOf(req, res), teamId, field(req, 'email'));
    this.done(res, `${member.display_name} added to the team.`, `/teams/${teamId}`);
  }

  private async removeMember(req: Request, res: Response): Promise<void> {
    const teamId = param(req, 'teamId');
    await this.deps.api.removeMember(callerOf(req, res), teamId, param(req, 'userId'));
    this.done(res, 'Member removed.', `/teams/${teamId}`);
  }

  private async createProject(req: Request, res: Response): Promise<void> {
    const teamId = param(req, 'teamId');
    const webhook = field(req, 'webhook_url').trim();
    const project = await this.deps.api.createProject(
      callerOf(req, res),
      teamId,
      field(req, 'name'),
      webhook || undefined,
    );
    this.done(res, `Project "${project.name}" created.`, `/projects/${project.id}`);
  }
}
