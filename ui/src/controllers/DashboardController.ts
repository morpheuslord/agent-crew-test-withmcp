import type { Request, Response, Router } from 'express';
import { callerOf, field, locals, userOf } from '../http/context.js';
import { requireUser } from '../http/middleware.js';
import { Controller } from './Controller.js';

/** Home page: my teams, my projects and tasks assigned to me; creating teams. */
export class DashboardController extends Controller {
  register(router: Router): void {
    router.get('/', (_req, res) => {
      res.redirect(303, locals(res).user ? '/dashboard' : '/login');
    });
    router.get(
      '/dashboard',
      requireUser(),
      this.page((req, res) => this.show(req, res)),
    );
    router.post(
      '/teams',
      requireUser(),
      this.form(
        (req, res) => this.createTeam(req, res),
        () => '/dashboard',
      ),
    );
  }

  private async show(req: Request, res: Response): Promise<void> {
    const caller = callerOf(req, res);
    const user = userOf(res);
    const [teams, projects, assigned] = await Promise.all([
      this.deps.api.listTeams(caller),
      this.deps.api.listProjects(caller),
      this.deps.api.searchTasks(caller, {
        assignee_id: user.id,
        sort: 'due_date',
        order: 'asc',
        page_size: 50,
      }),
    ]);
    const teamNames = new Map(teams.map((t) => [t.id, t.name]));
    res.render('dashboard', {
      title: 'Dashboard',
      teams,
      projects: projects.map((p) => ({ ...p, teamName: teamNames.get(p.team_id) ?? '' })),
      assigned: assigned.items,
    });
  }

  private async createTeam(req: Request, res: Response): Promise<void> {
    const team = await this.deps.api.createTeam(callerOf(req, res), field(req, 'name'));
    this.done(res, `Team "${team.name}" created.`, `/teams/${team.id}`);
  }
}
