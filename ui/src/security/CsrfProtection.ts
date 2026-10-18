import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto';
import type { NextFunction, Request, RequestHandler, Response } from 'express';
import type { CookiePolicy } from './cookies.js';

export class CsrfError extends Error {}

/** Routes whose body is multipart; their token is checked after the body is parsed. */
const MULTIPART_ROUTES = [/^\/tasks\/[0-9a-f-]{36}\/attachments$/i];

/**
 * Anti-forgery tokens bound to a random HttpOnly cookie: token = HMAC(secret, cookie).
 * Every non-GET request must echo the token in the `_csrf` form field.
 */
export class CsrfProtection {
  constructor(
    private readonly secret: string,
    private readonly cookies: CookiePolicy,
  ) {}

  private tokenFor(cookieValue: string): string {
    return createHmac('sha256', this.secret).update(`csrf:${cookieValue}`).digest('base64url');
  }

  /** Ensures the browser has a CSRF cookie and exposes the matching token to views. */
  issue(): RequestHandler {
    return (req: Request, res: Response, next: NextFunction) => {
      const cookies = req.cookies as Record<string, string | undefined>;
      let value = cookies[this.cookies.csrf];
      if (!value || !/^[A-Za-z0-9_-]{43}$/.test(value)) {
        value = randomBytes(32).toString('base64url');
        res.cookie(this.cookies.csrf, value, this.cookies.options());
        cookies[this.cookies.csrf] = value;
      }
      res.locals.csrfToken = this.tokenFor(value);
      next();
    };
  }

  isValid(req: Request): boolean {
    const cookies = req.cookies as Record<string, string | undefined>;
    const cookieValue = cookies[this.cookies.csrf];
    const body = req.body as Record<string, unknown> | undefined;
    const supplied = body?._csrf;
    if (!cookieValue || typeof supplied !== 'string') {
      return false;
    }
    const expected = Buffer.from(this.tokenFor(cookieValue));
    const actual = Buffer.from(supplied);
    return expected.length === actual.length && timingSafeEqual(expected, actual);
  }

  /** Checks every unsafe request except the multipart routes, which use `verifyParsed`. */
  verify(): RequestHandler {
    return (req: Request, _res: Response, next: NextFunction) => {
      if (req.method === 'GET' || req.method === 'HEAD') {
        next();
        return;
      }
      // Browsers that send Fetch Metadata tell us outright when a request is cross-site.
      if (req.get('sec-fetch-site') === 'cross-site') {
        next(new CsrfError('cross-site request'));
        return;
      }
      if (req.is('multipart/form-data')) {
        // Only the upload route may be multipart; it verifies once multer has parsed the body.
        next(MULTIPART_ROUTES.some((r) => r.test(req.path)) ? undefined : new CsrfError('bad'));
        return;
      }
      next(this.isValid(req) ? undefined : new CsrfError('invalid token'));
    };
  }

  /** For routes whose body is parsed later (multipart uploads). */
  verifyParsed(): RequestHandler {
    return (req: Request, _res: Response, next: NextFunction) => {
      next(this.isValid(req) ? undefined : new CsrfError('invalid token'));
    };
  }
}
