import { useState } from 'react';
import { useReportStore } from '../../store/useReportStore';

export default function StatusPanel() {
  const { statusResult, checking, error, checkStatus } = useReportStore();
  const [token, setToken] = useState('');

  const handleCheck = () => {
    if (token.trim()) checkStatus(token.trim());
  };

  const statusColor: Record<string, string> = {
    pending: 'bg-warn-50 text-warn-700',
    verified: 'bg-safe-50 text-safe-700',
    routed: 'bg-safe-50 text-safe-700',
    resolved: 'bg-ground-100 text-ground-800',
  };

  return (
    <div className="flex flex-col gap-4 p-5">
      <div>
        <h2 className="font-display text-base font-semibold mb-1">Check report status</h2>
        <p className="text-xs text-ground-800/50">
          Enter the receipt token you received when you submitted a report.
        </p>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          placeholder="SG-xxxxxxxx"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
          className="flex-1 px-3 py-2.5 rounded-lg border border-ground-200 bg-ground-50 text-sm
                     font-mono placeholder:text-ground-800/25 focus:outline-none
                     focus:border-ground-800 focus:bg-white transition-colors"
        />
        <button
          onClick={handleCheck}
          disabled={checking || !token.trim()}
          className="px-4 py-2.5 rounded-lg bg-ground-900 text-white text-sm font-medium
                     hover:bg-ground-800 disabled:opacity-30 transition-colors shrink-0"
        >
          {checking ? '…' : 'Check'}
        </button>
      </div>

      {error && <div className="p-2.5 rounded-lg bg-danger-50 text-danger-700 text-xs">{error}</div>}

      {statusResult && !statusResult.found && (
        <div className="p-3 rounded-lg bg-ground-100 text-xs text-center text-ground-800/50">
          No report found for this token.
        </div>
      )}

      {statusResult?.found && (
        <div className="p-4 rounded-xl bg-white border border-ground-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-ground-800/60">Status</span>
            <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${statusColor[statusResult.status || ''] || 'bg-ground-100'}`}>
              {statusResult.status}
            </span>
          </div>
          {statusResult.incident_type && (
            <p className="text-xs text-ground-800/50">
              Type: {statusResult.incident_type.replace(/_/g, ' ')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
