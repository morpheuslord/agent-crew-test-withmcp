/**
 * Returns `target` only if it is a same-site path such as `/tasks/123`; otherwise the fallback.
 * Rejects absolute URLs, protocol-relative `//host`, backslash tricks and control characters.
 */
export function safeRedirect(target: unknown, fallback = '/dashboard'): string {
  if (typeof target !== 'string' || target.length === 0 || target.length > 512) {
    return fallback;
  }
  if (!target.startsWith('/') || target.startsWith('//') || target.startsWith('/\\')) {
    return fallback;
  }
  // Any control character (including CR/LF) could split headers or confuse URL parsers.
  if (Array.from(target).some((ch) => ch.charCodeAt(0) < 0x20 || ch.charCodeAt(0) === 0x7f)) {
    return fallback;
  }
  if (target.includes('\\')) {
    return fallback;
  }
  return target;
}
