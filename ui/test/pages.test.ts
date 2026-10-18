import { describe, expect, it } from 'vitest';
import { ApiError } from '../src/api/ApiError.js';
import { IDS } from './fakeApi.js';
import { harness, signIn } from './helpers.js';

describe('dashboard, team and project pages', () => {
  it('requires a session', async () => {
    const { agent } = harness();
    const response = await agent.get(`/projects/${IDS.project}`).expect(303);
    expect(response.headers.location).toBe(`/login?next=%2Fprojects%2F${IDS.project}`);
  });

  it('renders the dashboard and creates a team', async () => {
    const { agent, api } = harness();
    const csrf = await signIn(agent);
    const page = await agent.get('/dashboard').expect(200);
    expect(page.text).toContain('Core');
    expect(page.text).toContain('Write docs');
    const created = await agent.post('/teams').type('form').send({ _csrf: csrf, name: 'Ops' });
    expect(created.headers.location).toBe(`/teams/${IDS.team}`);
    expect(api.called('createTeam')[0]?.[1]).toBe('Ops');
  });

  it('manages team members and projects', async () => {
    const { agent, api } = harness();
    const csrf = await signIn(agent);
    const page = await agent.get(`/teams/${IDS.team}`).expect(200);
    expect(page.text).toContain('Add member by email');
    await agent
      .post(`/teams/${IDS.team}/members`)
      .type('form')
      .send({ _csrf: csrf, email: 'ada@example.test' })
      .expect(303);
    await agent
      .post(`/teams/${IDS.team}/members/${IDS.admin}/remove`)
      .type('form')
      .send({ _csrf: csrf })
      .expect(303);
    const project = await agent
      .post(`/teams/${IDS.team}/projects`)
      .type('form')
      .send({ _csrf: csrf, name: 'New', webhook_url: '' });
    expect(project.headers.location).toBe(`/projects/${IDS.project}`);
    expect(api.called('createProject')[0]?.[3]).toBeUndefined();
    expect(api.called('removeMember')[0]?.[2]).toBe(IDS.admin);
  });

  it('shows API conflicts as a flash message on the same page', async () => {
    const { agent, api } = harness();
    const csrf = await signIn(agent);
    api.failNext('addMember', new ApiError(409, 'conflict', 'Already a member.'));
    const response = await agent
      .post(`/teams/${IDS.team}/members`)
      .type('form')
      .send({ _csrf: csrf, email: 'mo@example.test' })
      .expect(303);
    expect(response.headers.location).toBe(`/teams/${IDS.team}`);
    const page = await agent.get(`/teams/${IDS.team}`);
    expect(page.text).toContain('Already a member.');
  });

  it('renders the board with columns, settings and activity', async () => {
    const { agent } = harness();
    await signIn(agent);
    const page = await agent.get(`/projects/${IDS.project}`).expect(200);
    expect(page.text).toContain('To do');
    expect(page.text).toContain('In progress');
    expect(page.text).toContain('moved &#34;Write docs&#34; from todo to done');
    expect(page.text).toContain('signing-key');
  });

  it('creates tasks, saves settings and archives', async () => {
    const { agent, api } = harness();
    const csrf = await signIn(agent);
    await agent
      .post(`/projects/${IDS.project}/tasks`)
      .type('form')
      .send({
        _csrf: csrf,
        title: 'New task',
        description: 'x',
        status: 'bogus',
        priority: 'high',
        assignee_id: '',
        due_date: '',
        labels: 'a, b, a',
      })
      .expect(303);
    expect(api.called('createTask')[0]?.[2]).toEqual({
      title: 'New task',
      description: 'x',
      priority: 'high',
      assignee_id: null,
      due_date: null,
      labels: ['a', 'b'],
    });
    await agent
      .post(`/projects/${IDS.project}/settings`)
      .type('form')
      .send({ _csrf: csrf, name: 'Renamed', webhook_url: 'https://h.example.test' })
      .expect(303);
    await agent
      .post(`/projects/${IDS.project}/settings`)
      .type('form')
      .send({ _csrf: csrf, name: 'Renamed', clear_webhook: 'on' })
      .expect(303);
    expect(api.called('updateProject').map((c) => c[2])).toEqual([
      { name: 'Renamed', webhook_url: 'https://h.example.test' },
      { name: 'Renamed', clear_webhook: true },
    ]);
    await agent
      .post(`/projects/${IDS.project}/archive`)
      .type('form')
      .send({ _csrf: csrf })
      .expect(303);
  });

  it('streams the CSV export as a download', async () => {
    const { agent } = harness();
    await signIn(agent);
    const response = await agent.get(`/projects/${IDS.project}/export.csv`).expect(200);
    expect(response.headers['content-disposition']).toBe('attachment; filename="project.csv"');
    expect(response.text).toBe('id,title\r\n');
  });

  it('answers 404 for unknown ids and pages', async () => {
    const { agent } = harness();
    await signIn(agent);
    await agent.get('/projects/not-a-uuid').expect(404);
    const missing = await agent.get('/nowhere').expect(404);
    expect(missing.text).toContain('does not exist');
  });
});

describe('task page', () => {
  it('renders sanitized Markdown for descriptions and comments', async () => {
    const { agent } = harness();
    await signIn(agent);
    const page = await agent.get(`/tasks/${IDS.task}`).expect(200);
    expect(page.text).toContain('<strong>bold</strong>');
    expect(page.text).not.toContain('<script>alert(1)');
    expect(page.text).not.toContain('href="javascript');
    expect(page.text).not.toMatch(/<img[^>]*onerror/);
    expect(page.text).toContain('notes.txt');
    expect(page.text).toContain('2.0 KB');
  });

  it('updates, comments, edits comments and deletes', async () => {
    const { agent, api } = harness();
    const csrf = await signIn(agent);
    await agent
      .post(`/tasks/${IDS.task}`)
      .type('form')
      .send({
        _csrf: csrf,
        title: 'T',
        status: 'done',
        assignee_id: IDS.user,
        due_date: '2026-12-01',
      })
      .expect(303);
    await agent
      .post(`/tasks/${IDS.task}/comments`)
      .type('form')
      .send({ _csrf: csrf, body: 'hi' })
      .expect(303);
    const edited = await agent
      .post(`/comments/${IDS.comment}`)
      .type('form')
      .send({ _csrf: csrf, body: 'edit', task_id: IDS.task })
      .expect(303);
    expect(edited.headers.location).toBe(`/tasks/${IDS.task}`);
    const deleted = await agent
      .post(`/comments/${IDS.comment}/delete`)
      .type('form')
      .send({ _csrf: csrf, task_id: 'not-a-uuid' })
      .expect(303);
    expect(deleted.headers.location).toBe('/dashboard');
    const removed = await agent
      .post(`/tasks/${IDS.task}/delete`)
      .type('form')
      .send({ _csrf: csrf });
    expect(removed.headers.location).toBe(`/projects/${IDS.project}`);
    expect(api.called('updateTask')[0]?.[2]).toMatchObject({
      status: 'done',
      due_date: '2026-12-01',
    });
  });

  it('uploads with CSRF checked after parsing, and enforces the size limit', async () => {
    const { agent, api } = harness();
    const csrf = await signIn(agent);
    await agent
      .post(`/tasks/${IDS.task}/attachments`)
      .attach('file', Buffer.from('hello'), 'hello.txt')
      .field('_csrf', 'wrong')
      .expect(403);
    const ok = await agent
      .post(`/tasks/${IDS.task}/attachments`)
      .field('_csrf', csrf)
      .attach('file', Buffer.from('hello'), 'hello.txt')
      .expect(303);
    expect(ok.headers.location).toBe(`/tasks/${IDS.task}`);
    expect(api.called('uploadAttachment')).toHaveLength(1);
    await agent
      .post(`/tasks/${IDS.task}/attachments`)
      .field('_csrf', csrf)
      .attach('file', Buffer.alloc(4096), 'big.bin')
      .expect(303);
    const page = await agent.get(`/tasks/${IDS.task}`);
    expect(page.text).toContain('limited to 0 MB');
    await agent.post(`/tasks/${IDS.task}/attachments`).field('_csrf', csrf).expect(303);
    expect(api.called('uploadAttachment')).toHaveLength(1);
  });

  it('downloads attachments as non-renderable files', async () => {
    const { agent } = harness();
    await signIn(agent);
    const response = await agent.get(`/attachments/${IDS.attachment}/download`).expect(200);
    expect(response.headers['content-disposition']).toBe('attachment; filename="notes.txt"');
    expect(response.headers['content-type']).toBe('application/octet-stream');
    expect(response.headers['x-content-type-options']).toBe('nosniff');
    expect(response.headers['content-security-policy']).toContain('sandbox');
  });
});

describe('search, profile, admin and health', () => {
  it('searches with sanitized parameters and pagination', async () => {
    const { agent, api } = harness();
    await signIn(agent);
    const page = await agent
      .get('/search')
      .query({
        q: 'docs',
        status: 'bogus',
        sort: 'title',
        order: 'asc',
        page: '2',
        label: 'x',
        due_before: 'not-a-date',
        assignee_id: IDS.user,
      })
      .expect(200);
    expect(api.called('searchTasks')[0]?.[1]).toEqual({
      q: 'docs',
      label: 'x',
      assignee_id: IDS.user,
      sort: 'title',
      order: 'asc',
      page: 2,
      page_size: 25,
    });
    expect(page.text).toContain('Page 2 of 3');
  });

  it('changes the password and stores the new session', async () => {
    const { agent, api } = harness();
    const csrf = await signIn(agent);
    await agent.get('/profile').expect(200);
    await agent
      .post('/profile/password')
      .type('form')
      .send({ _csrf: csrf, current_password: 'a', new_password: 'b', new_password_confirm: 'c' })
      .expect(303);
    expect(api.called('changePassword')).toHaveLength(0);
    const response = await agent
      .post('/profile/password')
      .type('form')
      .send({ _csrf: csrf, current_password: 'a', new_password: 'b', new_password_confirm: 'b' })
      .expect(303);
    expect(String(response.headers['set-cookie'])).toContain('tb_session=member-token');
  });

  it('keeps members out of admin pages', async () => {
    const { agent } = harness();
    await signIn(agent);
    await agent.get('/admin/users').expect(403);
    await agent.get('/admin/activity').expect(403);
  });

  it('lets admins manage users and read the global feed', async () => {
    const { agent, api } = harness();
    const csrf = await signIn(agent, 'admin');
    const users = await agent.get('/admin/users').expect(200);
    expect(users.text).toContain('Make admin');
    for (const action of ['make_admin', 'make_member', 'deactivate', 'activate', 'bogus']) {
      await agent
        .post(`/admin/users/${IDS.user}`)
        .type('form')
        .send({ _csrf: csrf, action })
        .expect(303);
    }
    expect(api.called('updateUser').map((c) => c[2])).toEqual([
      { role: 'admin' },
      { role: 'member' },
      { is_active: false },
      { is_active: true },
    ]);
    const activity = await agent.get('/admin/activity?page=1').expect(200);
    expect(activity.text).toContain('Mo');
  });

  it('reports health and readiness', async () => {
    const { agent, api } = harness();
    await agent.get('/healthz').expect(200, { status: 'ok' });
    await agent.get('/readyz').expect(200);
    api.readyState = false;
    await agent.get('/readyz').expect(503);
  });

  it('shows a generic page when the API is down', async () => {
    const { agent, api } = harness();
    await signIn(agent);
    api.failNext('listTeams', new ApiError(502, 'api_unavailable', 'down'));
    const response = await agent.get('/dashboard').expect(502);
    expect(response.text).toContain('The service is unavailable.');
    api.failNext('getTask', new ApiError(401, 'authentication_required', 'expired'));
    const expired = await agent.get(`/tasks/${IDS.task}`).expect(303);
    expect(expired.headers.location).toBe('/login');
  });
});
