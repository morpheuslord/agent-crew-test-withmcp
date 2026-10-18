export interface FieldError {
  field: string;
  message: string;
}

/** A non-2xx answer from the API, or a failure to reach it (status 502). */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly fields: FieldError[] = [],
  ) {
    super(message);
    this.name = 'ApiError';
  }

  /** One user-facing sentence, including field details for validation errors. */
  describe(): string {
    if (this.fields.length === 0) {
      return this.message;
    }
    const details = this.fields.map((f) => (f.field ? `${f.field}: ${f.message}` : f.message));
    return `${this.message} ${details.join('; ')}`;
  }
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isUuid(value: unknown): value is string {
  return typeof value === 'string' && UUID.test(value);
}

/** Path ids are always UUIDs; anything else never reaches the API URL. */
export function assertUuid(value: string): string {
  if (!isUuid(value)) {
    throw new ApiError(404, 'not_found', 'Not found.');
  }
  return value;
}
