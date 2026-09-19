import { useState } from 'react';
import { Search } from 'lucide-react';
import { useReportStore } from '../../store/useReportStore';

export default function StatusPanel() {
  const { statusResult, checking, error, checkStatus } = useReportStore();
  const [token, setToken] = useState('');

  const colors: Record<string, string> = {
    pending: 'bg-amber-50 text-amber-700', verified: 'bg-green-50 text-green-700',
    routed: 'bg-blue-50 text-blue-700', resolved: 'bg-[#f5f4f1] text-[#6b6560]',
  };

  return (
    <div className="flex flex-col gap-4 p-5">
      <div>
        <h2 className="font-display text-[15px] font-semibold text-[#2d2a24] mb-1">Check report status</h2>
        <p className="text-[11px] text-[#9b9590]">Enter the receipt token from your submission.</p>
      </div>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#b5b0aa]" />
          <input type="text" placeholder="SG-xxxxxxxx" value={token}
            onChange={(e) => setToken(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && token.trim() && checkStatus(token.trim())}
            className="w-full pl-8 pr-3 py-2.5 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] text-sm font-mono
                       placeholder:text-[#c5c0ba] focus:outline-none focus:border-[#6b6560] focus:bg-white transition-colors" />
        </div>
        <button onClick={() => token.trim() && checkStatus(token.trim())} disabled={checking || !token.trim()}
          className="px-4 py-2.5 rounded-xl bg-[#2d2a24] text-white text-sm font-medium
                     hover:bg-[#3a3732] disabled:opacity-25 transition-colors shrink-0">
          {checking ? '…' : 'Check'}
        </button>
      </div>
      {error && <div className="p-2.5 rounded-lg bg-red-50 text-red-600 text-[11px]">{error}</div>}
      {statusResult && !statusResult.found && (
        <div className="p-3 rounded-xl bg-[#f5f4f1] text-[11px] text-center text-[#9b9590]">No report found for this token.</div>
      )}
      {statusResult?.found && (
        <div className="p-4 rounded-xl bg-white border border-[#e8e6e1]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-medium text-[#6b6560]">Status</span>
            <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium ${colors[statusResult.status || ''] || 'bg-[#f5f4f1]'}`}>
              {statusResult.status}
            </span>
          </div>
          {statusResult.incident_type && (
            <p className="text-[11px] text-[#9b9590]">Type: {statusResult.incident_type.replace(/_/g, ' ')}</p>
          )}
        </div>
      )}
    </div>
  );
}
