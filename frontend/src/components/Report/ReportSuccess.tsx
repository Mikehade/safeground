import { useState } from 'react';
import { CheckCircle, Copy, Check, Megaphone } from 'lucide-react';
import { useReportStore } from '../../store/useReportStore';

export default function ReportSuccess() {
  const { receiptToken } = useReportStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (receiptToken) { navigator.clipboard.writeText(receiptToken); setCopied(true); setTimeout(() => setCopied(false), 2000); }
  };

  if (!receiptToken) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        <Megaphone size={44} strokeWidth={1} className="text-[#d1cec8] mb-4" />
        <h2 className="font-display text-base font-semibold text-[#6b6560]">Anonymous reporting</h2>
        <p className="text-[12px] text-[#b5b0aa] mt-2 max-w-sm">
          Report incidents safely using the form in the panel. No account needed.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-full px-8">
      <div className="max-w-md w-full text-center">
        <CheckCircle size={48} strokeWidth={1.5} className="text-green-500 mx-auto mb-5" />
        <h2 className="font-display text-xl font-bold text-[#2d2a24] mb-2">Report submitted</h2>
        <p className="text-[13px] text-[#6b6560] mb-6">
          Save this receipt token. It is the only way to check your report status.
          We store nothing that links back to you.
        </p>
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-[#f5f4f1] border border-[#e8e6e1] mb-4">
          <code className="flex-1 text-center font-mono text-2xl font-bold tracking-widest text-[#2d2a24]">
            {receiptToken}
          </code>
          <button onClick={handleCopy}
            className="flex items-center gap-1 px-4 py-2 rounded-xl bg-[#2d2a24] text-white text-sm font-medium
                       hover:bg-[#3a3732] transition-colors shrink-0">
            {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy</>}
          </button>
        </div>
        <p className="text-[11px] text-[#b5b0aa]">Screenshot or write it down. It cannot be recovered.</p>
      </div>
    </div>
  );
}
