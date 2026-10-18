import { z } from 'zod';

/** Environment-driven settings, validated once at startup. Secrets have no defaults. */
const schema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('production'),
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  API_BASE_URL: z.url({ protocol: /^https?$/ }),
  SERVICE_AUTH_SECRET: z.string().min(32),
  COOKIE_SECRET: z.string().min(32),
  COOKIE_SECURE: z
    .enum(['true', 'false'])
    .default('true')
    .transform((value) => value === 'true'),
  TRUST_PROXY_HOPS: z.coerce.number().int().min(0).max(5).default(0),
  MAX_UPLOAD_BYTES: z.coerce
    .number()
    .int()
    .min(1024)
    .max(100 * 1024 * 1024)
    .default(10 * 1024 * 1024),
  API_TIMEOUT_MS: z.coerce.number().int().min(100).max(60_000).default(10_000),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

export interface AppConfig {
  readonly nodeEnv: 'development' | 'test' | 'production';
  readonly port: number;
  readonly apiBaseUrl: string;
  readonly serviceAuthSecret: string;
  readonly cookieSecret: string;
  readonly cookieSecure: boolean;
  readonly trustProxyHops: number;
  readonly maxUploadBytes: number;
  readonly apiTimeoutMs: number;
  readonly logLevel: 'debug' | 'info' | 'warn' | 'error';
}

export class ConfigError extends Error {}

/** Parse and validate configuration; throws a ConfigError naming every invalid variable. */
export function loadConfig(env: NodeJS.ProcessEnv = process.env): AppConfig {
  const parsed = schema.safeParse(env);
  if (!parsed.success) {
    const fields = parsed.error.issues.map((issue) => issue.path.join('.')).join(', ');
    throw new ConfigError(`Invalid configuration: ${fields}`);
  }
  const value = parsed.data;
  if (value.NODE_ENV === 'production' && !value.COOKIE_SECURE) {
    throw new ConfigError('COOKIE_SECURE must be true in production');
  }
  return {
    nodeEnv: value.NODE_ENV,
    port: value.PORT,
    apiBaseUrl: value.API_BASE_URL.replace(/\/+$/, ''),
    serviceAuthSecret: value.SERVICE_AUTH_SECRET,
    cookieSecret: value.COOKIE_SECRET,
    cookieSecure: value.COOKIE_SECURE,
    trustProxyHops: value.TRUST_PROXY_HOPS,
    maxUploadBytes: value.MAX_UPLOAD_BYTES,
    apiTimeoutMs: value.API_TIMEOUT_MS,
    logLevel: value.LOG_LEVEL,
  };
}
