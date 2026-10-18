import { AsyncLocalStorage } from 'node:async_hooks';
import { pino, type Logger } from 'pino';

interface RequestScope {
  readonly requestId: string;
}

/** Carries the per-request id to every log line and to outgoing API calls. */
export const requestScope = new AsyncLocalStorage<RequestScope>();

export function currentRequestId(): string {
  return requestScope.getStore()?.requestId ?? '-';
}

/** JSON logger. Every line carries the service name and the current request id. */
export function createLogger(level: string): Logger {
  return pino({
    level,
    base: { service: 'ui' },
    messageKey: 'msg',
    timestamp: pino.stdTimeFunctions.isoTime,
    formatters: { level: (label) => ({ level: label.toUpperCase() }) },
    mixin: () => ({ request_id: currentRequestId() }),
  });
}
