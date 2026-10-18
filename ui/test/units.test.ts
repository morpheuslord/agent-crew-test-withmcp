import { describe, expect, it } from 'vitest';
import { ApiError, assertUuid } from '../src/api/ApiError.js';
import { HttpApiClient } from '../src/api/HttpApiClient.js';
import { deriveKey } from '../src/app.js';
import { ConfigError, loadConfig } from '../src/config.js';
import { createLogger, currentRequestId, requestScope } from '../src/logging.js';
import { MarkdownRenderer } from '../src/security/MarkdownRenderer.js';
import { safeRedirect } from '../src/security/redirects.js';
import { ViewModels } from '../src/viewmodels/ViewModels.js';
import { IDS } from './fakeApi.js';

describe('MarkdownRenderer', () => {
  const render = (md: string): string => new MarkdownRenderer().render(md);

  it.each([
    ['<script>alert(1)</script>', '<script'],
    ['<img src=x onerror=alert(1)>', 'onerror'],
    ['[click](javascript:alert(1))', 'javascript:'],
    ['[click](JaVaScRiPt:alert(1))', 'avascript'],
    ['<a href="data:text/html,x">x</a>', 'data:'],
    ['<iframe src="https://evil.test"></iframe>', '<iframe'],
    ['<p style="background:url(x)">x</p>', 'style='],
    ['<svg onload=alert(1)>', '<svg'],
    ['[x](//evil.test)', '//evil.test'],
  ])('removes %s', (input, forbidden) => {
    expect(render(input).toLowerCase()).not.toContain(forbidden.toLowerCase());
  });

  it('keeps formatting and safe links, hardened', () => {
    const html = render('# Title\n\n**b** *i* `c`\n\n- one\n\n[ok](https://example.test)');
    expect(html).toContain('<h1>Title</h1>');
    expect(html).toContain('<strong>b</strong>');
    expect(html).toContain('<li>one</li>');
    expect(html).toContain('href="https://example.test"');
    expect(html).toContain('rel="nofollow noopener noreferrer"');
  });
});

describe('safeRedirect', () => {
  it.each([
    ['/tasks/1', '/tasks/1'],
    ['/search?q=a', '/search?q=a'],
    ['https://evil.test', '/dashboard'],
    ['//evil.test', '/dashboard'],
    ['/\\evil.test', '/dashboard'],
    ['/a\\b', '/dashboard'],
    ['/ok\r\nSet-Cookie: x', '/dashboard'],
    ['', '/dashboard'],
    [undefined, '/dashboard'],
    ['/' + 'a'.repeat(600), '/dashboard'],
  ])('%s -> %s', (input, expected) => {
    expect(safeRedirect(input)).toBe(expected);
  });
});

describe('loadConfig', () => {
  const base = {
    API_BASE_URL: 'http://api:8000/',
    SERVICE_AUTH_SECRET: 's'.repeat(32),
    COOKIE_SECRET: 'c'.repeat(32),
  };

  it('parses defaults and strips trailing slashes', () => {
    const config = loadConfig(base);
    expect(config.apiBaseUrl).toBe('http://api:8000');
    expect(config.cookieSecure).toBe(true);
    expect(config.port).toBe(3000);
    expect(config.maxUploadBytes).toBe(10 * 1024 * 1024);
  });

  it('rejects missing or weak secrets and insecure production cookies', () => {
    expect(() => loadConfig({ ...base, COOKIE_SECRET: 'short' })).toThrow(ConfigError);
    expect(() => loadConfig({ ...base, API_BASE_URL: 'ftp://x' })).toThrow(/API_BASE_URL/);
    expect(() => loadConfig({ ...base, COOKIE_SECURE: 'false' })).toThrow(/COOKIE_SECURE/);
    expect(
      loadConfig({ ...base, COOKIE_SECURE: 'false', NODE_ENV: 'development' }).cookieSecure,
    ).toBe(false);
  });
});

describe('deriveKey', () => {
  it('gives each purpose its own key', () => {
    const secret = 'c'.repeat(32);
    expect(deriveKey(secret, 'csrf')).not.toBe(deriveKey(secret, 'cookie-signing'));
    expect(deriveKey(secret, 'csrf')).not.toContain(secret);
    expect(deriveKey(secret, 'csrf')).toBe(deriveKey(secret, 'csrf'));
  });
});

describe('logging', () => {
  it('exposes the request id inside a request scope only', () => {
    expect(currentRequestId()).toBe('-');
    requestScope.run({ requestId: 'req-1' }, () => {
      expect(currentRequestId()).toBe('req-1');
    });
    expect(createLogger('info').level).toBe('info');
  });
});

describe('HttpApiClient', () => {
  interface Seen {
    url: string;
    init: RequestInit;
  }

  function client(responses: Response[]): { api: HttpApiClient; seen: Seen[] } {
    const seen: Seen[] = [];
    const fetchFn = (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
      seen.push({ url: input instanceof Request ? input.url : input.toString(), init: init ?? {} });
      const next = responses.shift();
      return next ? Promise.resolve(next) : Promise.reject(new Error('network down'));
    };
    return { api: new HttpApiClient('http://api:8000', 'secret', 1000, fetchFn), seen };
  }

  const json = (body: unknown, status = 200): Response =>
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

  it('sends service auth, bearer token, client IP and request id', async () => {
    const { api, seen } = client([json({ id: IDS.user })]);
    await requestScope.run({ requestId: 'req-42' }, () =>
      api.me({ token: 'tok', clientIp: '10.1.2.3' }),
    );
    const headers = seen[0]?.init.headers as Record<string, string>;
    expect(seen[0]?.url).toBe('http://api:8000/api/v1/auth/me');
    expect(headers['X-Service-Token']).toBe('secret');
    expect(headers.Authorization).toBe('Bearer tok');
    expect(headers['X-Client-IP']).toBe('10.1.2.3');
    expect(headers['X-Request-ID']).toBe('req-42');
    expect(seen[0]?.init.redirect).toBe('error');
  });

  it('maps API errors and network failures', async () => {
    const { api } = client([
      json(
        {
          error: {
            code: 'validation_failed',
            message: 'Bad.',
            fields: [{ field: 'name', message: 'x' }],
          },
        },
        422,
      ),
      new Response('not json', { status: 500 }),
    ]);
    const caller = { clientIp: '1.1.1.1' };
    const first = await api.createTeam(caller, '').catch((e: unknown) => e);
    expect(first).toBeInstanceOf(ApiError);
    expect((first as ApiError).describe()).toBe('Bad. name: x');
    const second = await api.listTeams(caller).catch((e: unknown) => e);
    expect((second as ApiError).status).toBe(500);
    const third = await api.listTeams(caller).catch((e: unknown) => e);
    expect((third as ApiError).status).toBe(502);
  });

  it('never puts a non-UUID into an API path', () => {
    const { api, seen } = client([]);
    expect(() => api.getTask({ clientIp: '1' }, '../admin/users')).toThrow(ApiError);
    expect(seen).toHaveLength(0);
    expect(() => assertUuid('x')).toThrow(ApiError);
  });

  it('builds query strings, bodies and uploads', async () => {
    const empty = (): Response => new Response(null, { status: 204 });
    const ok = (): Response => json({});
    const { api, seen } = client([
      ok(),
      ok(),
      ok(),
      ok(),
      empty(),
      ok(),
      ok(),
      ok(),
      empty(),
      ok(),
      ok(),
      ok(),
      ok(),
      ok(),
      empty(),
      ok(),
      ok(),
      ok(),
      ok(),
      ok(),
      ok(),
      empty(),
      empty(),
      ok(),
      ok(),
      ok(),
      ok(),
      ok(),
      ok(),
    ]);
    const c = { token: 't', clientIp: '1' };
    await api.searchTasks(c, { q: 'a b', status: 'done', page: 2, label: '' });
    await api.register(c, 'e', 'n', 'p');
    await api.login(c, 'e', 'p');
    await api.changePassword(c, 'a', 'b');
    await api.forgotPassword(c, 'e');
    await api.createTeam(c, 'n');
    await api.getTeam(c, IDS.team);
    await api.addMember(c, IDS.team, 'e');
    await api.removeMember(c, IDS.team, IDS.user);
    await api.createProject(c, IDS.team, 'n', 'https://h');
    await api.createProject(c, IDS.team, 'n');
    await api.listProjects(c);
    await api.getProject(c, IDS.project);
    await api.updateProject(c, IDS.project, { name: 'x' });
    await api.resetPassword(c, 'tok', 'p');
    await api.archiveProject(c, IDS.project);
    await api.listProjectTasks(c, IDS.project, { sort: 'title' });
    await api.createTask(c, IDS.project, { title: 't' });
    await api.projectActivity(c, IDS.project, 1);
    await api.getTask(c, IDS.task);
    await api.updateTask(c, IDS.task, { title: 'x' });
    await api.deleteTask(c, IDS.task);
    await api.deleteComment(c, IDS.comment);
    await api.listComments(c, IDS.task);
    await api.addComment(c, IDS.task, 'b');
    await api.editComment(c, IDS.comment, 'b');
    await api.listAttachments(c, IDS.task);
    await api.uploadAttachment(c, IDS.task, {
      filename: 'a.txt',
      contentType: 'text/plain',
      data: Buffer.from('x'),
    });
    await api.listUsers(c, 1);
    expect(seen[0]?.url).toBe('http://api:8000/api/v1/search/tasks?q=a+b&status=done&page=2');
    expect(seen[1]?.init.body).toBe(
      JSON.stringify({ email: 'e', display_name: 'n', password: 'p' }),
    );
    expect(seen[9]?.init.body).toBe(JSON.stringify({ name: 'n', webhook_url: 'https://h' }));
    expect(seen[27]?.init.body).toBeInstanceOf(FormData);
    expect(seen.map((s) => s.init.method)).toContain('DELETE');
  });

  it('streams binary responses and checks readiness', async () => {
    const { api } = client([
      new Response('abc', {
        headers: { 'content-type': 'text/csv', 'content-disposition': 'attachment' },
      }),
      new Response('x', { headers: { 'content-length': '1' } }),
      json({}),
      json({}),
      json({}),
      json({}),
    ]);
    const c = { clientIp: '1' };
    const csv = await api.exportCsv(c, IDS.project);
    expect(csv.headers['content-type']).toBe('text/csv');
    const file = await api.downloadAttachment(c, IDS.attachment);
    expect(file.headers['content-length']).toBe('1');
    await api.updateUser(c, IDS.user, { role: 'admin' });
    await api.globalActivity(c, 1);
    await api.logout(c);
    expect(await api.ready()).toBe(true);
    expect(await api.ready()).toBe(false);
  });
});

describe('ViewModels', () => {
  const views = new ViewModels(new MarkdownRenderer());

  it('formats sizes and describes every activity type', () => {
    expect(views.humanSize(10)).toBe('10 B');
    expect(views.humanSize(5 * 1024 * 1024)).toBe('5.0 MB');
    const base = {
      id: '1',
      team_id: '1',
      project_id: null,
      task_id: null,
      actor_id: '1',
      actor_name: 'A',
      created_at: '2026-10-18T09:00:00Z',
    };
    const types = [
      'task_created',
      'task_updated',
      'comment_added',
      'attachment_added',
      'member_added',
      'member_removed',
      'other',
    ];
    const lines = views.activity(
      types.map((t) => ({ ...base, event_type: t, details: { title: 7 } })),
    );
    expect(lines.map((l) => l.text)).toEqual([
      'created task ""',
      'updated task ""',
      'commented on ""',
      'attached  to ""',
      'added  to the team',
      'removed  from the team',
      'other',
    ]);
    expect(lines[0]?.when).toBe('2026-10-18 09:00');
    const grouped = views.projectsByTeam([
      { id: 'p1', team_id: 't1' },
      { id: 'p2', team_id: 't1' },
    ] as never);
    expect(grouped.get('t1')).toHaveLength(2);
  });
});
