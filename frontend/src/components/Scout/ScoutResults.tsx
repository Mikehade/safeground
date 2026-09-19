import { useState, useMemo, useEffect, useRef } from 'react';
import { useScoutStore } from '../../store/useScoutStore';
import type { ToolEvent } from '../../store/useScoutStore';

/* ── Tool icon lookup ── */
const TOOL_ICONS: Record<string, string> = {
  geocode_location: '📍',
  get_routes: '🗺️',
  query_incidents_in_area: '🔍',
  get_area_hotspots: '🔥',
  search_content: '🌐',
  scrape_url: '📄',
};

/* ── Single tool event card ── */
function ToolCard({ event, isLatest }: { event: ToolEvent; isLatest: boolean }) {
  return (
    <div
      className={`
        flex items-start gap-2.5 px-3.5 py-2.5 rounded-xl border transition-all duration-500
        ${isLatest
          ? 'bg-white border-ground-300 shadow-sm'
          : 'bg-ground-50/50 border-ground-200/60 opacity-70'}
      `}
    >
      <span className="text-base mt-0.5 shrink-0">
        {TOOL_ICONS[event.name] || '⚙️'}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-ground-700 truncate">
          {event.message}
        </p>
        {isLatest && (
          <div className="flex items-center gap-1.5 mt-1">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-amber-500" />
            </span>
            <span className="text-[10px] text-ground-400">Working…</span>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Thinking / progress phase ── */
function StreamingProgress() {
  const { statusMessage, toolEvents, streaming, advisory } = useScoutStore();
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest event
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [toolEvents.length]);

  const showToolPhase = toolEvents.length > 0 && !streaming && !advisory;
  const showTransition = streaming || advisory;

  return (
    <div className="flex flex-col items-center justify-center h-full gap-5 px-6">
      {/* Shield spinner — visible during tool phase */}
      {!showTransition && (
        <div className="relative">
          <div className="w-14 h-14 border-[3px] border-ground-200 border-t-ground-700 rounded-full animate-spin" />
          <span className="absolute inset-0 flex items-center justify-center text-lg">🛡️</span>
        </div>
      )}

      {/* Status message */}
      {statusMessage && !showTransition && (
        <p className="text-sm font-medium text-ground-700 text-center animate-fade-in">
          {statusMessage}
        </p>
      )}

      {/* Tool event cards */}
      {showToolPhase && (
        <div
          ref={containerRef}
          className="w-full max-w-sm flex flex-col gap-2 max-h-[50vh] overflow-y-auto pr-1"
        >
          {toolEvents.map((ev, i) => (
            <div
              key={`${ev.name}-${ev.timestamp}`}
              className="animate-slide-in"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <ToolCard event={ev} isLatest={i === toolEvents.length - 1} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Main results component ── */
export default function ScoutResults() {
  const { advisory, loading, streaming, done, error, toolCalls, toolEvents, submitFeedback } =
    useScoutStore();
  const [feedbackSent, setFeedbackSent] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const renderedHtml = useMemo(() => {
    if (!advisory) return '';
    return markdownToHtml(advisory);
  }, [advisory]);

  // Auto-scroll as tokens stream in
  useEffect(() => {
    if (streaming && contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [advisory, streaming]);

  /* ── Loading: show tool progress ── */
  if (loading && !advisory) {
    return <StreamingProgress />;
  }

  /* ── Error state ── */
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 px-8">
        <span className="text-3xl">⚠️</span>
        <p className="text-sm text-danger-700 text-center">{error}</p>
      </div>
    );
  }

  /* ── Empty state ── */
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

  /* ── Advisory content (streaming or final) ── */
  return (
    <div className="flex flex-col h-full">
      <div ref={contentRef} className="flex-1 overflow-y-auto main-scroll">
        <div className="max-w-3xl mx-auto px-6 py-6 lg:px-10 lg:py-8">
          {/* Tool summary strip — collapsed once advisory is showing */}
          {toolEvents.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-5 pb-4 border-b border-ground-200/60">
              {toolEvents.map((ev, i) => (
                <span
                  key={`${ev.name}-${i}`}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-md
                             bg-ground-100/80 text-[10px] text-ground-500 font-medium"
                >
                  {TOOL_ICONS[ev.name] || '⚙️'} {ev.name.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}

          {/* Advisory markdown */}
          <div
            className="advisory-content text-sm text-ground-900 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: renderedHtml }}
          />

          {/* Streaming cursor */}
          {streaming && (
            <span className="inline-block w-2 h-4 bg-ground-700 animate-blink ml-0.5 align-text-bottom rounded-sm" />
          )}

          {/* Source count */}
          {done && toolCalls > 0 && (
            <div className="mt-6 pt-4 border-t border-ground-200 flex items-center gap-2">
              <span className="text-xs text-ground-800/30">
                Based on {toolCalls} data source{toolCalls > 1 ? 's' : ''} checked
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Feedback bar — only after done */}
      {done && (
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
      )}
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

  // Links — [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, '');
  html = html.replace(/<p><(h[123]|hr|table|ul|ol|blockquote)/g, '<$1');
  html = html.replace(/<\/(h[123]|hr|table|ul|ol|blockquote)><\/p>/g, '</$1>');

  return html;
}

function inlineFormat(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
}
