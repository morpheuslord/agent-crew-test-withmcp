import type { Request, Response, Router } from 'express';
import { ApiError } from '../api/ApiError.js';
import type { LoginResult } from '../api/types.js';
import { callerOf, field, locals, queryParam } from '../http/context.js';
import { safeRedirect } from '../security/redirects.js';
import { Controller } from './Controller.js';

/** Login, registration, logout and password reset pages. */
export class AuthController extends Controller {
  register(router: Router): void {
    router.get('/login', (req, res) => {
      this.renderLogin(req, res);
    });
    router.post(
      '/login',
      this.page((req, res) => this.login(req, res)),
    );
    router.get('/register', (_req, res) => {
      res.render('register', { title: 'Register', values: {}, error: null });
    });
    router.post(
      '/register',
      this.page((req, res) => this.registerUser(req, res)),
    );
    router.post(
      '/logout',
      this.page((req, res) => this.logout(req, res)),
    );
    router.get('/forgot-password', (_req, res) => {
      res.render('forgot-password', { title: 'Forgot password' });
    });
    router.post(
      '/forgot-password',
      this.form(
        (req, res) => this.forgot(req, res),
        () => '/forgot-password',
      ),
    );
    router.get('/reset-password', (req, res) => {
      res.render('reset-password', { title: 'Reset password', token: queryParam(req, 'token') });
    });
    router.post(
      '/reset-password',
      this.page((req, res) => this.reset(req, res)),
    );
  }

  private renderLogin(req: Request, res: Response, error: string | null = null): void {
    if (locals(res).user && !error) {
      res.redirect(303, '/dashboard');
      return;
    }
    res.status(error ? 400 : 200).render('login', {
      title: 'Log in',
      next: safeRedirect(field(req, 'next') || queryParam(req, 'next')),
      email: field(req, 'email'),
      error,
    });
  }

  private startSession(res: Response, result: LoginResult): void {
    const maxAge = Math.max(0, new Date(result.expires_at).getTime() - Date.now());
    res.cookie(this.deps.cookies.session, result.token, this.deps.cookies.options(maxAge));
  }

  private async login(req: Request, res: Response): Promise<void> {
    const caller = callerOf(req, res);
    try {
      const result = await this.deps.api.login(caller, field(req, 'email'), field(req, 'password'));
      if (caller.token) {
        // Never keep two sessions for one browser: end the one the cookie pointed at.
        await this.deps.api.logout(caller).catch(() => undefined);
      }
      this.startSession(res, result);
      res.redirect(303, safeRedirect(field(req, 'next')));
    } catch (error) {
      if (error instanceof ApiError && error.status < 500) {
        this.renderLogin(req, res, error.status === 422 ? error.describe() : error.message);
        return;
      }
      throw error;
    }
  }

  private async registerUser(req: Request, res: Response): Promise<void> {
    const caller = callerOf(req, res);
    const values = { email: field(req, 'email'), display_name: field(req, 'display_name') };
    const password = field(req, 'password');
    if (password !== field(req, 'password_confirm')) {
      res.status(400).render('register', {
        title: 'Register',
        values,
        error: 'The passwords do not match.',
      });
      return;
    }
    try {
      await this.deps.api.register(caller, values.email, values.display_name, password);
      const result = await this.deps.api.login(caller, values.email, password);
      this.startSession(res, result);
      this.done(res, 'Welcome to Taskboard.', '/dashboard');
    } catch (error) {
      if (error instanceof ApiError && error.status < 500) {
        res.status(400).render('register', { title: 'Register', values, error: error.describe() });
        return;
      }
      throw error;
    }
  }

  private async logout(req: Request, res: Response): Promise<void> {
    const caller = callerOf(req, res);
    if (caller.token) {
      await this.deps.api.logout(caller).catch(() => undefined);
    }
    res.clearCookie(this.deps.cookies.session, this.deps.cookies.clearOptions());
    this.done(res, 'You have been logged out.', '/login');
  }

  private async forgot(req: Request, res: Response): Promise<void> {
    await this.deps.api.forgotPassword(callerOf(req, res), field(req, 'email'));
    this.done(res, 'If an account exists for that email, a reset link has been sent.', '/login');
  }

  private async reset(req: Request, res: Response): Promise<void> {
    const token = field(req, 'token');
    const password = field(req, 'password');
    const render = (error: string): void => {
      res.status(400).render('reset-password', { title: 'Reset password', token, error });
    };
    if (password !== field(req, 'password_confirm')) {
      render('The passwords do not match.');
      return;
    }
    try {
      await this.deps.api.resetPassword(callerOf(req, res), token, password);
      this.done(res, 'Your password has been reset. You can now log in.', '/login');
    } catch (error) {
      if (error instanceof ApiError && error.status < 500) {
        render(error.describe());
        return;
      }
      throw error;
    }
  }
}
