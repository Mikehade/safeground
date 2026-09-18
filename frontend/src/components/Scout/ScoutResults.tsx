import { useState, useMemo } from 'react';
import { useScoutStore } from '../../store/useScoutStore';

export default function ScoutResults() {
  const { advisory, loading, error, toolCalls, submitFeedback } = useScoutStore();
  const [feedbackSent, setFeedbackSent] = useState(false);

  const renderedHtml = useMemo(() => {
    if (!advisory) return '';
    return markdownToHtml(advisory);
  }, [advisory]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <div className="relative">
          <div className="w-16 h-16 border-[3px] border-ground-200 border-t-ground-800 rounded-full animate-spin" />
          <span className="absolute inset-0 flex items-center justify-center text-xl">🛡️</span>
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-ground-800/70">Analyzing routes</p>
          <p className="text-xs text-ground-800/40 mt-1">
            Querying incident database, scanning live sources…
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 px-8">
        <span className="text-3xl">⚠️</span>
        <p className="text-sm text-danger-700 text-center">{error}</p>
      </div>
    );
  }

  if (!advisory) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        <span className="text-5xl mb-4">🗺️</span>
        <h2 className="font-display text-xl font-semibold text-ground-800/60">
          Route safety advisory
        </h2>
        <p className="text-sm text-ground-800/35 mt-2 max-w-md">
          Enter your origin and destination in the sidebar.
          SafeGround will analyze each route for safety risks
          using incident reports and live web intelligence.
        </p>
      </div>
    );
  }

  const handleFeedback = (helpful: boolean) => {
    submitFeedback(helpful);
    setFeedbackSent(true);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Advisory content — the star */}
      <div className="flex-1 overflow-y-auto main-scroll">
        <div className="max-w-3xl mx-auto px-6 py-6 lg:px-10 lg:py-8">
          <div
            className="advisory-content text-sm text-ground-900 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: renderedHtml }}
          />

          {toolCalls > 0 && (
            <div className="mt-6 pt-4 border-t border-ground-200 flex items-center gap-2">
              <span className="text-xs text-ground-800/30">
                Based on {toolCalls} data source{toolCalls > 1 ? 's' : ''} checked
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Feedback bar — pinned at bottom */}
      <div className="border-t border-ground-200 bg-white px-6 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          {!feedbackSent ? (
            <>
              <span className="text-xs text-ground-800/50">Was this advisory helpful?</span>
              <div className="flex gap-2">
                <button
                  onClick={() => handleFeedback(true)}
                  className="px-4 py-1.5 rounded-md text-xs font-medium
                             bg-safe-50 text-safe-700 hover:bg-safe-500 hover:text-white transition-colors"
                >
                  👍 Yes
                </button>
                <button
                  onClick={() => handleFeedback(false)}
                  className="px-4 py-1.5 rounded-md text-xs font-medium
                             bg-danger-50 text-danger-700 hover:bg-danger-500 hover:text-white transition-colors"
                >
                  👎 No
                </button>
              </div>
            </>
          ) : (
            <span className="text-xs text-ground-800/40 w-full text-center">
              Thanks for the feedback — it helps SafeGround improve.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}


/**
 * Minimal markdown-to-HTML renderer.
 * Handles: headings, bold, italic, lists, tables, blockquotes, hr, links.
 * No external dependency needed.
 */
function markdownToHtml(md: string): string {
  let html = md;

  // Escape HTML entities first
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // Restore markdown chars that got escaped
  html = html.replace(/&gt;\s/gm, '> '); // blockquote
  html = html.replace(/&lt;/g, '<').replace(/&gt;/g, '>');

  // Re-escape actual HTML but keep our generated tags (we'll build from scratch)
  // Actually, let's just work with the raw markdown properly:
  html = md;

  // Tables
  html = html.replace(
    /\|(.+)\|\n\|[-| :]+\|\n((?:\|.+\|\n?)+)/g,
    (_match, headerRow: string, bodyRows: string) => {
      const headers = headerRow.split('|').map((h: string) => h.trim()).filter(Boolean);
      const headerHtml = headers.map((h: string) => `<th>${inlineFormat(h)}</th>`).join('');
      const rows = bodyRows.trim().split('\n').map((row: string) => {
        const cells = row.split('|').map((c: string) => c.trim()).filter(Boolean);
        return `<tr>${cells.map((c: string) => `<td>${inlineFormat(c)}</td>`).join('')}</tr>`;
      }).join('');
      return `<table><thead><tr>${headerHtml}</tr></thead><tbody>${rows}</tbody></table>`;
    }
  );

  // Blockquotes
  html = html.replace(/^>\s?(.+)$/gm, '<blockquote>$1</blockquote>');
  html = html.replace(/<\/blockquote>\n<blockquote>/g, '<br/>');

  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Horizontal rules
  html = html.replace(/^---+$/gm, '<hr/>');

  // Unordered lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`);

  // Ordered lists
  html = html.replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>');

  // Paragraphs — wrap loose lines
  html = html.replace(/^(?!<[a-z])((?!<\/)[^\n]+)$/gm, '<p>$1</p>');

  // Inline formatting
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, '');
  html = html.replace(/<p><(h[123]|hr|table|ul|ol|blockquote)/g, '<$1');
  html = html.replace(/<\/(h[123]|hr|table|ul|ol|blockquote)><\/p>/g, '</$1>');

  return html;
}

function inlineFormat(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}
