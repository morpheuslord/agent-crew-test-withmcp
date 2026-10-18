import path from 'node:path';
import cookieParser from 'cookie-parser';
import express, { type Express } from 'express';
import helmet from 'helmet';
import type { Logger } from 'pino';
import type { TaskboardApi } from './api/TaskboardApi.js';
import type { AppConfig } from './config.js';
import { AuthController } from './controllers/AuthController.js';
import {
  AdminController,
  HealthController,
  ProfileController,
  SearchController,
} from './controllers/AccountControllers.js';
import type { Controller, ControllerDeps } from './controllers/Controller.js';
import { DashboardController } from './controllers/DashboardController.js';
import { ProjectController } from './controllers/ProjectController.js';
import { TaskController } from './controllers/TaskController.js';
import { TeamController } from './controllers/TeamController.js';
import { ErrorHandler } from './http/ErrorHandler.js';
import { FlashMessages, RequestContext, SessionLoader } from './http/middleware.js';
import { CookiePolicy } from './security/cookies.js';
import { CsrfProtection } from './security/CsrfProtection.js';
import { MarkdownRenderer } from './security/MarkdownRenderer.js';
import { ViewModels } from './viewmodels/ViewModels.js';

export interface AppDependencies {
  config: AppConfig;
  api: TaskboardApi;
  logger: Logger;
  /** Directory holding `views/` and `public/`; defaults to the working directory. */
  rootDir?: string;
}

/** Composition root of the UI server: wires middleware, controllers and error handling. */
export function createApp({
  config,
  api,
  logger,
  rootDir = process.cwd(),
}: AppDependencies): Express {
  const app = express();
  const cookies = new CookiePolicy(config.cookieSecure);
  const csrf = new CsrfProtection(config.cookieSecret, cookies);
  const flash = new FlashMessages(cookies);

  app.disable('x-powered-by');
  app.set('trust proxy', config.trustProxyHops);
  app.set('views', path.join(rootDir, 'views'));
  app.set('view engine', 'ejs');

  app.use(
    helmet({
      contentSecurityPolicy: {
        useDefaults: false,
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'none'"],
          styleSrc: ["'self'"],
          imgSrc: ["'self'"],
          fontSrc: ["'self'"],
          connectSrc: ["'self'"],
          objectSrc: ["'none'"],
          baseUri: ["'none'"],
          formAction: ["'self'"],
          frameAncestors: ["'none'"],
          ...(config.cookieSecure ? { upgradeInsecureRequests: [] } : {}),
        },
      },
      strictTransportSecurity: config.cookieSecure
        ? { maxAge: 31_536_000, includeSubDomains: true }
        : false,
      referrerPolicy: { policy: 'no-referrer' },
      crossOriginEmbedderPolicy: false,
    }),
  );
  app.use(new RequestContext(logger).handler());
  app.use(
    '/static',
    express.static(path.join(rootDir, 'public'), { dotfiles: 'deny', index: false, maxAge: '1h' }),
  );
  app.use((_req, res, next) => {
    // Pages may contain private data: never let shared caches or the back button keep them.
    res.setHeader('Cache-Control', 'no-store');
    next();
  });
  app.use(cookieParser(config.cookieSecret));
  app.use(express.urlencoded({ extended: false, limit: '64kb', parameterLimit: 50 }));
  app.use(csrf.issue());
  app.use(csrf.verify());
  app.use(new SessionLoader(api, cookies).handler());
  app.use(flash.handler());

  const views = new ViewModels(new MarkdownRenderer());
  const deps: ControllerDeps = {
    api,
    flash,
    cookies,
    views,
    logger,
    maxUploadBytes: config.maxUploadBytes,
  };
  const controllers: Controller[] = [
    new HealthController(deps),
    new AuthController(deps),
    new DashboardController(deps),
    new TeamController(deps),
    new ProjectController(deps),
    new TaskController(deps, csrf),
    new SearchController(deps),
    new ProfileController(deps),
    new AdminController(deps),
  ];
  const router = express.Router();
  for (const controller of controllers) {
    controller.register(router);
  }
  app.use(router);

  const errors = new ErrorHandler(logger, cookies);
  app.use(errors.notFound());
  app.use(errors.handler());
  return app;
}
