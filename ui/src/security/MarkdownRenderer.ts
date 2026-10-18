import { Marked } from 'marked';
import sanitizeHtml from 'sanitize-html';

/**
 * Renders user-written Markdown to HTML that is safe to embed: Markdown first, then a strict
 * allow-list sanitizer, so raw HTML inside the Markdown cannot add scripts, handlers or styles.
 */
export class MarkdownRenderer {
  private readonly marked = new Marked({ gfm: true, breaks: true, async: false });

  private readonly options: sanitizeHtml.IOptions = {
    allowedTags: [
      'p',
      'br',
      'strong',
      'em',
      'del',
      'code',
      'pre',
      'blockquote',
      'ul',
      'ol',
      'li',
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'hr',
      'a',
      'table',
      'thead',
      'tbody',
      'tr',
      'th',
      'td',
    ],
    // `rel` is set by the transform below, never taken from user input.
    allowedAttributes: { a: ['href', 'title', 'rel'] },
    allowedSchemes: ['http', 'https', 'mailto'],
    allowProtocolRelative: false,
    disallowedTagsMode: 'discard',
    transformTags: {
      a: sanitizeHtml.simpleTransform('a', { rel: 'nofollow noopener noreferrer' }),
    },
  };

  render(markdown: string): string {
    const html = this.marked.parse(markdown, { async: false });
    return sanitizeHtml(html, this.options);
  }
}
