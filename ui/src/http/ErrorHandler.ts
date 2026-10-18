import type { ErrorRequestHandler, NextFunction, Request, Response } from 'express';
import type { Logger } from 'pino';
import { ApiError } from '../api/ApiError.js';
import { CsrfError } from '../security/CsrfProtection.js';
import type { CookiePolicy } from '../security/cookies.js';
import { locals } from './context.js';

const TITLES: Record<number, string> = {
  403: 'Not allowed',
  404: 'Not found',
  413: 'Too large',
  429: 'Too many requests',
  502: 'Service unavailable',
};

/** The one place where errors become pages. Users see a short message and the request id. */
export class ErrorHandler {
  constructor(
    private readonly logger: Logger,
    private readonly cookies: CookiePolicy,
  ) {}

  notFound() {
    return (_req: Request, res: Response): void => {
      this.render(res, 404, 'The page you asked for does not exist.');
    };
  }

  handler(): ErrorRequestHandler {
    return (error: unknown, req: Request, res: Response, next: NextFunction): void => {
      if (res.headersSent) {
        next(error);
        return;
      }
      if (error instanceof CsrfError) {
        this.logger.warn({ path: req.path }, 'csrf check failed');
        this.render(res, 403, 'Your form expired or came from another site. Please try again.');
        return;
      }
      if (error instanceof ApiError) {
        if (error.status === 401) {
          res.clearCookie(this.cookies.session, this.cookies.clearOptions());
          res.redirect(303, '/login');
          return;
        }
        const status = error.status >= 500 ? 502 : error.status;
        if (status >= 500) {
          this.logger.error({ code: error.code }, 'api unavailable');
        }
        this.render(res, status, status >= 500 ? 'The service is unavailable.' : error.describe());
        return;
      }
      this.logger.error({ err: error }, 'unhandled error');
      this.render(res, 500, 'Something went wrong.');
    };
  }

  private render(res: Response, status: number, message: string): void {
    res.status(status).render('error', {
      title: TITLES[status] ?? 'Error',
      message,
      requestId: locals(res).requestId,
    });
  }
}
