import { describe, expect, it } from 'vitest';
import { ApiError } from '../src/api/ApiError.js';
import { csrfFrom, harness, signIn } from './helpers.js';

describe('security headers and CSRF', () => {
  it('sets a strict CSP and other headers', async () => {
    const { agent } = harness();
    const response = await agent.get('/login').expect(200);
    const csp = String(response.headers['content-security-policy']);
    expect(csp).toContain("script-src 'none'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(response.headers['x-content-type-options']).toBe('nosniff');
    expect(response.headers['referrer-policy']).toBe('no-referrer');
    expect(response.headers['cache-control']).toBe('no-store');
    expect(response.headers['x-request-id']).toMatch(/^[0-9a-f-]{36}$/);
    expect(response.headers['x-powered-by']).toBeUndefined();
  });

  it('sends HSTS and secure cookies when configured for HTTPS', async () => {
    const { agent } = harness({ cookieSecure: true });
    const response = await agent.get('/login').expect(200);
    expect(response.headers['strict-transport-security']).toContain('max-age=31536000');
    const cookie = String(response.headers['set-cookie']);
    expect(cookie).toContain('__Host-tb_csrf=');
    expect(cookie).toContain('Secure');
  });

  it('rejects POSTs without a valid token', async () => {
    const { agent, api } = harness();
    await agent.get('/login');
    const missing = await agent.post('/login').type('form').send({ email: 'a@b.c' });
    expect(missing.status).toBe(403);
    const forged = await agent.post('/login').type('form').send({ _csrf: 'forged', email: 'x' });
    expect(forged.status).toBe(403);
    expect(api.called('login')).toHaveLength(0);
  });

  it('rejects cross-site requests and stray multipart bodies', async () => {
    const { agent } = harness();
    const csrf = await csrfFrom(agent);
    const cross = await agent
      .post('/login')
      .set('Sec-Fetch-Site', 'cross-site')
      .type('form')
      .send({ _csrf: csrf });
    expect(cross.status).toBe(403);
    const multipart = await agent.post('/login').field('_csrf', csrf).field('email', 'x');
    expect(multipart.status).toBe(403);
  });
});

describe('login and logout', () => {
  it('logs in, sets an HttpOnly session cookie and redirects to a safe path', async () => {
    const { agent, api } = harness();
    const csrf = await csrfFrom(agent, '/login?next=%2Ftasks%2Fabc');
    const response = await agent
      .post('/login')
      .type('form')
      .send({
        _csrf: csrf,
        email: 'mo@example.test',
        password: 'correct-horse-battery',
        next: '/search',
      })
      .expect(303);
    expect(response.headers.location).toBe('/search');
    const cookie = String(response.headers['set-cookie']);
    expect(cookie).toContain('tb_session=member-token');
    expect(cookie).toContain('HttpOnly');
    expect(cookie).toContain('SameSite=Lax');
    const caller = api.called('login')[0]?.[0] as { clientIp?: unknown } | undefined;
    expect(typeof caller?.clientIp).toBe('string');
  });

  it('never redirects off-site after login', async () => {
    const { agent } = harness();
    const csrf = await csrfFrom(agent);
    const response = await agent
      .post('/login')
      .type('form')
      .send({
        _csrf: csrf,
        email: 'mo@example.test',
        password: 'correct-horse-battery',
        next: '//evil.test',
      })
      .expect(303);
    expect(response.headers.location).toBe('/dashboard');
  });

  it('shows a generic error for bad credentials and keeps the email', async () => {
    const { agent } = harness();
    const csrf = await csrfFrom(agent);
    const response = await agent
      .post('/login')
      .type('form')
      .send({ _csrf: csrf, email: 'mo@example.test', password: 'nope' })
      .expect(400);
    expect(response.text).toContain('Invalid email or password.');
    expect(response.text).toContain('value="mo@example.test"');
  });

  it('ends the old session when logging in again, and on logout', async () => {
    const { agent, api } = harness();
    await signIn(agent);
    const csrf = await signIn(agent);
    expect(api.called('logout')).toHaveLength(1);
    const response = await agent.post('/logout').type('form').send({ _csrf: csrf }).expect(303);
    expect(response.headers.location).toBe('/login');
    expect(String(response.headers['set-cookie'])).toContain('tb_session=;');
    expect(api.called('logout')).toHaveLength(2);
    await agent.get('/dashboard').expect(303);
  });

  it('clears a session the API no longer accepts', async () => {
    const { agent } = harness();
    await agent.get('/login').set('Cookie', 'tb_session=stale').expect(200);
    const response = await agent.get('/dashboard').set('Cookie', 'tb_session=stale');
    expect(response.status).toBe(303);
    expect(response.headers.location).toBe('/login?next=%2Fdashboard');
  });

  it('redirects signed-in users away from the login page', async () => {
    const { agent } = harness();
    await signIn(agent);
    const response = await agent.get('/login').expect(303);
    expect(response.headers.location).toBe('/dashboard');
    expect((await agent.get('/').expect(303)).headers.location).toBe('/dashboard');
  });
});

describe('registration and password reset', () => {
  it('registers and signs in', async () => {
    const { agent, api } = harness();
    await agent.get('/register').expect(200);
    const csrf = await csrfFrom(agent, '/register');
    const response = await agent
      .post('/register')
      .type('form')
      .send({
        _csrf: csrf,
        email: 'new@example.test',
        display_name: 'New',
        password: 'correct-horse-battery',
        password_confirm: 'correct-horse-battery',
      })
      .expect(303);
    expect(response.headers.location).toBe('/dashboard');
    expect(api.called('register')).toHaveLength(1);
  });

  it('shows mismatch and API validation errors on the form', async () => {
    const { agent, api } = harness();
    const csrf = await csrfFrom(agent, '/register');
    const mismatch = await agent
      .post('/register')
      .type('form')
      .send({ _csrf: csrf, email: 'x@example.test', password: 'a', password_confirm: 'b' })
      .expect(400);
    expect(mismatch.text).toContain('do not match');
    api.failNext(
      'register',
      new ApiError(422, 'validation_failed', 'The request is invalid.', [
        { field: 'password', message: 'too short' },
      ]),
    );
    const invalid = await agent
      .post('/register')
      .type('form')
      .send({ _csrf: csrf, email: 'x@example.test', password: 'a', password_confirm: 'a' })
      .expect(400);
    expect(invalid.text).toContain('password: too short');
  });

  it('requests and completes a password reset', async () => {
    const { agent, api } = harness();
    await agent.get('/forgot-password').expect(200);
    let csrf = await csrfFrom(agent, '/forgot-password');
    const forgot = await agent
      .post('/forgot-password')
      .type('form')
      .send({ _csrf: csrf, email: 'mo@example.test' })
      .expect(303);
    expect(forgot.headers.location).toBe('/login');
    const page = await agent.get('/reset-password?token=abc_DEF-123').expect(200);
    expect(page.text).toContain('value="abc_DEF-123"');
    csrf = await csrfFrom(agent, '/reset-password?token=t');
    await agent
      .post('/reset-password')
      .type('form')
      .send({ _csrf: csrf, token: 't', password: 'x', password_confirm: 'y' })
      .expect(400);
    api.failNext('resetPassword', new ApiError(422, 'validation_failed', 'Link expired.'));
    const expired = await agent
      .post('/reset-password')
      .type('form')
      .send({ _csrf: csrf, token: 't', password: 'x', password_confirm: 'x' })
      .expect(400);
    expect(expired.text).toContain('Link expired.');
    await agent
      .post('/reset-password')
      .type('form')
      .send({ _csrf: csrf, token: 't', password: 'x', password_confirm: 'x' })
      .expect(303);
    expect(api.called('resetPassword')).toHaveLength(2);
  });

  it('turns rate limiting into a message on the form', async () => {
    const { agent, api } = harness();
    const csrf = await csrfFrom(agent, '/forgot-password');
    api.failNext('forgotPassword', new ApiError(429, 'rate_limited', 'Too many attempts.'));
    const response = await agent
      .post('/forgot-password')
      .type('form')
      .send({ _csrf: csrf, email: 'x@example.test' })
      .expect(303);
    expect(response.headers.location).toBe('/forgot-password');
    const page = await agent.get('/forgot-password');
    expect(page.text).toContain('Too many attempts.');
  });
});
