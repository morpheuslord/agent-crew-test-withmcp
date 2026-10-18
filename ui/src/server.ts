import { HttpApiClient } from './api/HttpApiClient.js';
import { createApp } from './app.js';
import { loadConfig } from './config.js';
import { createLogger } from './logging.js';

/** Process entry point: load config, build the API client and serve. */
function main(): void {
  const config = loadConfig();
  const logger = createLogger(config.logLevel);
  const api = new HttpApiClient(config.apiBaseUrl, config.serviceAuthSecret, config.apiTimeoutMs);
  const app = createApp({ config, api, logger });
  const server = app.listen(config.port, () => {
    logger.info({ port: config.port }, 'ui server listening');
  });
  const shutdown = (): void => {
    logger.info('shutting down');
    server.close(() => process.exit(0));
  };
  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
}

main();
