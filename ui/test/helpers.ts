import path from 'node:path';
import { pino } from 'pino';
import request from 'supertest';
import type TestAgent from 'supertest/lib/agent.js';
import { createApp } from '../src/app.js';
import type { AppConfig } from '../src/config.js';
import { FakeApi } from './fakeApi.js';

export const config: AppConfig = {
  nodeEnv: 'test',
  port: 0,
  apiBaseUrl: 'http://api.internal:8000',
  serviceAuthSecret: 's'.repeat(32),
  cookieSecret: 'c'.repeat(32),
  cookieSecure: false,
  trustProxyHops: 0,
  maxUploadBytes: 1024,
  apiTimeoutMs: 1000,
  logLevel: 'error',
};

export interface Harness {
  api: FakeApi;
  agent: TestAgent;
}

export function harness(overrides: Partial<AppConfig> = {}): Harness {
  const api = new FakeApi();
  const app = createApp({
    config: { ...config, ...overrides },
    api,
    logger: pino({ level: 'silent' }),
    rootDir: path.resolve(import.meta.dirname, '..'),
  });
  return { api, agent: request.agent(app) };
}

/** Load a page and return the CSRF token embedded in its forms. */
export async function csrfFrom(agent: TestAgent, url = '/login'): Promise<string> {
  const response = await agent.get(url);
  const match = /name="_csrf" value="([^"]+)"/.exec(response.text);
  if (!match?.[1]) {
    throw new Error(`no csrf token on ${url} (status ${String(response.status)})`);
  }
  return match[1];
}

/** Log the agent in as the member (or admin) and return a fresh CSRF token. */
export async function signIn(
  agent: TestAgent,
  who: 'member' | 'admin' = 'member',
): Promise<string> {
  const csrf = await csrfFrom(agent, '/register');
  const email = who === 'admin' ? 'root@example.test' : 'mo@example.test';
  await agent
    .post('/login')
    .type('form')
    .send({ _csrf: csrf, email, password: 'correct-horse-battery', next: '/dashboard' })
    .expect(303);
  return csrfFrom(agent, '/profile');
}
