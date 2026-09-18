/**
 * Quick-exit — navigates to Google, no history trace.
 * Critical for GBV and at-risk users.
 */
export default function QuickExit() {
  return (
    <button
      onClick={() => window.location.replace('https://www.google.com')}
      className="fixed top-3 right-3 z-[9999] bg-white/80 backdrop-blur hover:bg-danger-500 hover:text-white
                 rounded-full w-8 h-8 flex items-center justify-center text-xs font-bold
                 shadow-sm border border-ground-200 transition-all duration-150"
      aria-label="Exit quickly"
      title="Leave this site immediately"
    >
      ✕
    </button>
  );
}
