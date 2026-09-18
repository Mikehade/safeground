import { useReportStore } from '../../store/useReportStore';
import { useState } from 'react';

export default function ReportSuccess() {
  const { receiptToken } = useReportStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (receiptToken) {
      navigator.clipboard.writeText(receiptToken);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!receiptToken) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        <span className="text-5xl mb-4">📢</span>
        <h2 className="font-display text-xl font-semibold text-ground-800/60">
          Anonymous reporting
        </h2>
        <p className="text-sm text-ground-800/35 mt-2 max-w-md">
          Report incidents safely using the form in the sidebar.
          No account needed. No data stored about you.
          You'll receive a receipt token to track your report.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-full px-8">
      <div className="max-w-md w-full text-center">
        <div className="w-20 h-20 rounded-full bg-safe-50 flex items-center justify-center text-4xl mx-auto mb-6">
          ✓
        </div>
        <h2 className="font-display text-2xl font-bold mb-2">Report submitted</h2>
        <p className="text-sm text-ground-800/50 mb-6">
          Save this receipt token. It's the only way to check your report's status.
          We don't store any information that links back to you.
        </p>

        <div className="flex items-center gap-3 p-4 rounded-xl bg-ground-100 border border-ground-200 mb-4">
          <code className="flex-1 text-center font-mono text-2xl font-bold tracking-widest text-ground-900">
            {receiptToken}
          </code>
          <button
            onClick={handleCopy}
            className="px-4 py-2 rounded-lg bg-ground-900 text-white text-sm font-medium
                       hover:bg-ground-800 transition-colors shrink-0"
          >
            {copied ? '✓ Copied' : 'Copy'}
          </button>
        </div>

        <p className="text-xs text-ground-800/30">
          Screenshot this token or write it down. It cannot be recovered.
        </p>
      </div>
    </div>
  );
}
