import type { Request, Response } from 'express';
import type { Caller, User } from '../api/types.js';

export interface Flash {
  type: 'success' | 'error';
  text: string;
}

/** Typed view of `res.locals`, filled in by the middleware chain. */
export interface AppLocals {
  requestId: string;
  csrfToken: string;
  user?: User;
  sessionToken?: string;
  flash?: Flash;
}

export function locals(res: Response): AppLocals {
  return res.locals as AppLocals;
}

/** The API caller for this request: the browser's session token and IP. */
export function callerOf(req: Request, res: Response): Caller {
  const token = locals(res).sessionToken;
  const clientIp = req.ip ?? req.socket.remoteAddress ?? 'unknown';
  return token ? { token, clientIp } : { clientIp };
}

/** The signed-in user; only call after `requireUser`. */
export function userOf(res: Response): User {
  const user = locals(res).user;
  if (!user) {
    throw new Error('requireUser middleware missing');
  }
  return user;
}

/** Read a string field from a parsed form body. */
export function field(req: Request, name: string): string {
  const body = req.body as Record<string, unknown> | undefined;
  const value = body?.[name];
  return typeof value === 'string' ? value : '';
}

/** Read a string query parameter (first value only). */
export function queryParam(req: Request, name: string): string {
  const value: unknown = req.query[name];
  if (typeof value === 'string') {
    return value;
  }
  if (Array.isArray(value) && typeof value[0] === 'string') {
    return value[0];
  }
  return '';
}

/** A route parameter, as a string. */
export function param(req: Request, name: string): string {
  const value: unknown = req.params[name];
  return typeof value === 'string' ? value : '';
}
