import type { Request, Response, Router } from 'express';
import { SORT_FIELDS, TASK_STATUSES } from '../api/types.js';
import { callerOf, field, param, queryParam } from '../http/context.js';
import { requireAdmin, requireUser } from '../http/middleware.js';
import { Controller } from './Controller.js';
import { readTaskQuery } from './forms.js';

function pageNumber(req: Request): number {
  const page = Number.parseInt(queryParam(req, 'page'), 10);
  return Number.isInteger(page) && page >= 1 && page <= 10_000 ? page : 1;
}

/** Cross-project task search with filters, sorting and paging. */
export class SearchController extends Controller {
  register(router: Router): void {
    router.get(
      '/search',
      requireUser(),
      this.page((req, res) => this.search(req, res)),
    );
  }

  private async search(req: Request, res: Response): Promise<void> {
    const query = readTaskQuery(req);
    const results = await this.deps.api.searchTasks(callerOf(req, res), query);
    const pages = Math.max(1, Math.ceil(results.total / results.page_size));
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (key !== 'page' && key !== 'page_size' && value !== undefined) {
        params.set(key, String(value));
      }
    }
    res.render('search', {
      title: 'Search',
      query,
      results,
      pages,
      baseQuery: params.toString(),
      statuses: TASK_STATUSES,
      sortFields: SORT_FIELDS,
    });
  }
}

/** The signed-in user's profile and password change. */
export class ProfileController extends Controller {
  register(router: Router): void {
    router.get('/profile', requireUser(), (_req, res) => {
      res.render('profile', { title: 'Profile' });
    });
    router.post(
      '/profile/password',
      requireUser(),
      this.form(
        (req, res) => this.changePassword(req, res),
        () => '/profile',
      ),
    );
  }

  private async changePassword(req: Request, res: Response): Promise<void> {
    if (field(req, 'new_password') !== field(req, 'new_password_confirm')) {
      this.deps.flash.set(res, 'error', 'The new passwords do not match.');
      res.redirect(303, '/profile');
      return;
    }
    const result = await this.deps.api.changePassword(
      callerOf(req, res),
      field(req, 'current_password'),
      field(req, 'new_password'),
    );
    // The API ended every session, including this one, and issued a fresh token.
    const maxAge = Math.max(0, new Date(result.expires_at).getTime() - Date.now());
    res.cookie(this.deps.cookies.session, result.token, this.deps.cookies.options(maxAge));
    this.done(res, 'Password changed. Other sessions have been signed out.', '/profile');
  }
}

/** Admin pages. The API enforces the admin role; the guard only keeps members off the pages. */
export class AdminController extends Controller {
  register(router: Router): void {
    router.get(
      '/admin/users',
      requireUser(),
      requireAdmin(),
      this.page((req, res) => this.users(req, res)),
    );
    router.post(
      '/admin/users/:userId',
      requireUser(),
      requireAdmin(),
      this.form(
        (req, res) => this.updateUser(req, res),
        () => '/admin/users',
      ),
    );
    router.get(
      '/admin/activity',
      requireUser(),
      requireAdmin(),
      this.page((req, res) => this.activity(req, res)),
    );
  }

  private async users(req: Request, res: Response): Promise<void> {
    const page = pageNumber(req);
    const users = await this.deps.api.listUsers(callerOf(req, res), page);
    res.render('admin-users', {
      title: 'Users',
      users,
      pages: Math.max(1, Math.ceil(users.total / users.page_size)),
    });
  }

  private async updateUser(req: Request, res: Response): Promise<void> {
    const action = field(req, 'action');
    const update =
      action === 'make_admin'
        ? { role: 'admin' as const }
        : action === 'make_member'
          ? { role: 'member' as const }
          : action === 'deactivate'
            ? { is_active: false }
            : action === 'activate'
              ? { is_active: true }
              : null;
    if (!update) {
      this.deps.flash.set(res, 'error', 'Unknown action.');
      res.redirect(303, '/admin/users');
      return;
    }
    const user = await this.deps.api.updateUser(callerOf(req, res), param(req, 'userId'), update);
    this.done(res, `${user.display_name} updated.`, '/admin/users');
  }

  private async activity(req: Request, res: Response): Promise<void> {
    const page = pageNumber(req);
    const events = await this.deps.api.globalActivity(callerOf(req, res), page);
    res.render('admin-activity', {
      title: 'Activity',
      lines: this.deps.views.activity(events.items),
      page,
      pages: Math.max(1, Math.ceil(events.total / events.page_size)),
    });
  }
}

/** Liveness and readiness probes for the load balancer and Compose. */
export class HealthController extends Controller {
  register(router: Router): void {
    router.get('/healthz', (_req, res) => {
      res.json({ status: 'ok' });
    });
    router.get(
      '/readyz',
      this.page(async (_req, res) => {
        const ready = await this.deps.api.ready();
        res.status(ready ? 200 : 503).json({ status: ready ? 'ready' : 'not_ready' });
      }),
    );
  }
}
