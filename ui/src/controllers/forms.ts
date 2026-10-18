import type { Request } from 'express';
import { isUuid } from '../api/ApiError.js';
import {
  SORT_FIELDS,
  TASK_PRIORITIES,
  TASK_STATUSES,
  type SortField,
  type TaskInput,
  type TaskPriority,
  type TaskQuery,
  type TaskStatus,
} from '../api/types.js';
import { field, queryParam } from '../http/context.js';

const DATE = /^\d{4}-\d{2}-\d{2}$/;

function oneOf<T extends string>(allowed: readonly T[], value: string): T | undefined {
  return (allowed as readonly string[]).includes(value) ? (value as T) : undefined;
}

/** Comma-separated labels, trimmed and de-duplicated; the API enforces lengths. */
export function parseLabels(raw: string): string[] {
  return [
    ...new Set(
      raw
        .split(',')
        .map((label) => label.trim())
        .filter(Boolean),
    ),
  ];
}

/**
 * Reads the task form. Only known fields are copied; empty assignee or due date clears it.
 * Values the API would reject are passed on so the user sees the API's validation message.
 */
export function readTaskForm(req: Request): TaskInput {
  const assignee = field(req, 'assignee_id');
  const due = field(req, 'due_date');
  const input: TaskInput = {
    title: field(req, 'title'),
    description: field(req, 'description'),
    labels: parseLabels(field(req, 'labels')),
    assignee_id: assignee === '' ? null : assignee,
    due_date: due === '' ? null : due,
  };
  const status = oneOf<TaskStatus>(TASK_STATUSES, field(req, 'status'));
  const priority = oneOf<TaskPriority>(TASK_PRIORITIES, field(req, 'priority'));
  if (status) {
    input.status = status;
  }
  if (priority) {
    input.priority = priority;
  }
  return input;
}

/** Search parameters from the query string; invalid values are dropped rather than forwarded. */
export function readTaskQuery(req: Request): TaskQuery {
  const query: TaskQuery = {};
  const text = queryParam(req, 'q').trim();
  if (text) {
    query.q = text.slice(0, 200);
  }
  const status = oneOf<TaskStatus>(TASK_STATUSES, queryParam(req, 'status'));
  if (status) {
    query.status = status;
  }
  const assignee = queryParam(req, 'assignee_id');
  if (isUuid(assignee)) {
    query.assignee_id = assignee;
  }
  const label = queryParam(req, 'label').trim();
  if (label) {
    query.label = label.slice(0, 50);
  }
  const dueBefore = queryParam(req, 'due_before');
  if (DATE.test(dueBefore)) {
    query.due_before = dueBefore;
  }
  const sort = oneOf<SortField>(SORT_FIELDS, queryParam(req, 'sort'));
  if (sort) {
    query.sort = sort;
  }
  const order = queryParam(req, 'order');
  if (order === 'asc' || order === 'desc') {
    query.order = order;
  }
  const page = Number.parseInt(queryParam(req, 'page'), 10);
  query.page = Number.isInteger(page) && page >= 1 && page <= 10_000 ? page : 1;
  query.page_size = 25;
  return query;
}
