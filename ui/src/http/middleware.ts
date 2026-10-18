import { randomUUID } from 'node:crypto';
import type { NextFunction, Request, RequestHandler, Response } from 'express';
import type { Logger } from 'pino';
import { ApiError } from '../api/ApiError.js';
import type { TaskboardApi } from '../api/TaskboardApi.js';
import { requestScope } from '../logging.js';
import type { CookiePolicy } from '../security/cookies.js';
import { callerOf, locals, type Flash } from './context.js';

/** Assigns a request id, runs the rest of the chain inside its scope, and logs one access line. */
export class RequestContext {
  constructor(private readonly logger: Logger) {}

  handler(): RequestHandler {
    return (req: Request, res: Response, next: NextFunction) => {
      const requestId = randomUUID();
      const started = process.hrtime.bigint();
      locals(res).requestId = requestId;
      res.setHeader('X-Request-ID', requestId);
      requestScope.run({ requestId }, () => {
        res.on('finish', () => {
          const durationMs = Number(process.hrtime.bigint() - started) / 1e6;
          // The path only: query strings can carry search text or reset tokens.
          this.logger.info(
            {
              method: req.method,
              path: req.path,
              status: res.statusCode,
              duration_ms: Math.round(durationMs),
            },
            'request',
          );
        });
        next();
      });
    };
  }
}

/** Loads the signed-in user from the API for every request that carries a session cookie. */
export class SessionLoader {
  constructor(
    private readonly api: TaskboardApi,
    private readonly cookies: CookiePolicy,
  ) {}

  handler(): RequestHandler {
    return async (req: Request, res: Response, next: NextFunction) => {
      const cookies = req.cookies as Record<string, string | undefined>;
      const token = cookies[this.cookies.session];
      if (!token || token.length > 200) {
        next();
        return;
      }
      try {
        const user = await this.api.me({ token, clientIp: callerOf(req, res).clientIp });
        locals(res).user = user;
        locals(res).sessionToken = token;
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          res.clearCookie(this.cookies.session, this.cookies.clearOptions());
        } else {
          next(error);
          return;
        }
      }
      next();
    };
  }
}

/** One-shot messages carried across a redirect in a signed cookie. */
export class FlashMessages {
  constructor(private readonly cookies: CookiePolicy) {}

  handler(): RequestHandler {
    return (req: Request, res: Response, next: NextFunction) => {
      const signed = req.signedCookies as Record<string, string | false | undefined>;
      const raw = signed[this.cookies.flash];
      if (typeof raw === 'string') {
        try {
          const parsed = JSON.parse(raw) as Partial<Flash>;
          if ((parsed.type === 'success' || parsed.type === 'error') && parsed.text) {
            locals(res).flash = { type: parsed.type, text: parsed.text.slice(0, 500) };
          }
        } catch {
          // Ignore malformed values.
        }
        res.clearCookie(this.cookies.flash, this.cookies.clearOptions());
      }
      next();
    };
  }

  set(res: Response, type: Flash['type'], text: string): void {
    res.cookie(this.cookies.flash, JSON.stringify({ type, text }), {
      ...this.cookies.options(60_000),
      signed: true,
    });
  }
}

/** Redirects anonymous visitors to the login page, remembering where they were going. */
export function requireUser(): RequestHandler {
  return (req: Request, res: Response, next: NextFunction) => {
    if (locals(res).user) {
      next();
      return;
    }
    const target = req.method === 'GET' ? req.originalUrl : '/dashboard';
    res.redirect(303, `/login?next=${encodeURIComponent(target)}`);
  };
}

/**
 * Hides admin pages from members. This is presentation only: the API enforces the admin role on
 * every admin endpoint regardless of what the UI shows.
 */
export function requireAdmin(): RequestHandler {
  return (_req: Request, res: Response, next: NextFunction) => {
    if (locals(res).user?.role === 'admin') {
      next();
      return;
    }
    next(new ApiError(403, 'permission_denied', 'You are not allowed to do that.'));
  };
}
