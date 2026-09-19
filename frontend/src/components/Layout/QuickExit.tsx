import { X } from 'lucide-react';

export default function QuickExit() {
  return (
    <button
      onClick={() => window.location.replace('https://www.google.com')}
      className="fixed top-3 right-3 z-[9999] bg-white/90 backdrop-blur-sm hover:bg-red-500 hover:text-white
                 rounded-full w-7 h-7 flex items-center justify-center
                 shadow-sm border border-[#e8e6e1] transition-all duration-150"
      aria-label="Exit quickly" title="Leave this site immediately"
    >
      <X size={14} strokeWidth={2.5} />
    </button>
  );
}
