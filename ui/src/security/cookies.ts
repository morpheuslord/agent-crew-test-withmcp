import type { CookieOptions } from 'express';

/**
 * Cookie names and attributes. With COOKIE_SECURE=true the names carry the `__Host-` prefix, which
 * browsers only accept with Secure, Path=/ and no Domain, so the cookies cannot be planted by a
 * sibling subdomain.
 */
export class CookiePolicy {
  readonly session: string;
  readonly csrf: string;
  readonly flash: string;

  constructor(private readonly secure: boolean) {
    const prefix = secure ? '__Host-' : '';
    this.session = `${prefix}tb_session`;
    this.csrf = `${prefix}tb_csrf`;
    this.flash = `${prefix}tb_flash`;
  }

  options(maxAgeMs?: number): CookieOptions {
    const options: CookieOptions = {
      httpOnly: true,
      secure: this.secure,
      sameSite: 'lax',
      path: '/',
    };
    if (maxAgeMs !== undefined) {
      options.maxAge = maxAgeMs;
    }
    return options;
  }

  clearOptions(): CookieOptions {
    return { httpOnly: true, secure: this.secure, sameSite: 'lax', path: '/' };
  }
}
