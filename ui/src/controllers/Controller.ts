import type { NextFunction, Request, RequestHandler, Response, Router } from 'express';
import type { Logger } from 'pino';
import { ApiError } from '../api/ApiError.js';
import type { TaskboardApi } from '../api/TaskboardApi.js';
import type { FlashMessages } from '../http/middleware.js';
import type { CookiePolicy } from '../security/cookies.js';
import type { ViewModels } from '../viewmodels/ViewModels.js';

export interface ControllerDeps {
  api: TaskboardApi;
  flash: FlashMessages;
  cookies: CookiePolicy;
  views: ViewModels;
  logger: Logger;
  maxUploadBytes: number;
}

type AsyncHandler = (req: Request, res: Response) => Promise<void>;

/** Errors a user can fix by changing their input; shown as a message on the previous page. */
const RECOVERABLE = new Set([400, 409, 413, 422, 429]);

export abstract class Controller {
  constructor(protected readonly deps: ControllerDeps) {}

  abstract register(router: Router): void;

  /** Adapts an async handler for Express, forwarding failures to the error handler. */
  protected page(handler: AsyncHandler): RequestHandler {
    return (req: Request, res: Response, next: NextFunction) => {
      handler(req, res).catch(next);
    };
  }

  /**
   * Wraps a form submission. Validation, conflict and rate-limit errors become a flash message
   * and a redirect back to `back(req)`; anything else goes to the error handler.
   */
  protected form(handler: AsyncHandler, back: (req: Request) => string): RequestHandler {
    return (req: Request, res: Response, next: NextFunction) => {
      handler(req, res).catch((error: unknown) => {
        if (error instanceof ApiError && RECOVERABLE.has(error.status)) {
          this.deps.flash.set(res, 'error', error.describe());
          res.redirect(303, back(req));
          return;
        }
        next(error);
      });
    };
  }

  protected done(res: Response, message: string, to: string): void {
    this.deps.flash.set(res, 'success', message);
    res.redirect(303, to);
  }
}
