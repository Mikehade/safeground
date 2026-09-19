import { useState } from 'react';
import { MapPin, Navigation } from 'lucide-react';
import { useScoutStore } from '../../store/useScoutStore';

interface Props { onShowMain?: () => void; }

export default function ScoutInputs({ onShowMain }: Props) {
  const { loading, analyzeRoutes, clear } = useScoutStore();
  const [originName, setOriginName] = useState('');
  const [destName, setDestName] = useState('');

  const handleAnalyze = () => {
    if (!originName.trim() || !destName.trim()) return;
    analyzeRoutes({ name: originName.trim() }, { name: destName.trim() });
  };

  return (
    <div className="flex flex-col gap-4 p-5">
      <div>
        <h2 className="font-display text-[15px] font-semibold text-[#2d2a24] mb-1">Check your route</h2>
        <p className="text-[11px] text-[#9b9590] leading-relaxed">
          We'll scan incident databases and live web sources for each possible route.
        </p>
      </div>

      <div className="flex flex-col gap-2.5">
        <div className="relative">
          <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#b5b0aa]" />
          <input type="text" placeholder="Where are you now?" value={originName}
            onChange={(e) => setOriginName(e.target.value)}
            className="w-full pl-8 pr-3 py-2.5 rounded-xl border border-[#e8e6e1] bg-[#faf9f7]
                       text-sm placeholder:text-[#c5c0ba] focus:outline-none focus:border-[#6b6560]
                       focus:bg-white transition-colors" />
        </div>
        <div className="relative">
          <Navigation size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#b5b0aa]" />
          <input type="text" placeholder="Where are you going?" value={destName}
            onChange={(e) => setDestName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            className="w-full pl-8 pr-3 py-2.5 rounded-xl border border-[#e8e6e1] bg-[#faf9f7]
                       text-sm placeholder:text-[#c5c0ba] focus:outline-none focus:border-[#6b6560]
                       focus:bg-white transition-colors" />
        </div>

        <button onClick={handleAnalyze}
          disabled={loading || !originName.trim() || !destName.trim()}
          className="w-full py-2.5 rounded-xl bg-[#2d2a24] text-white font-medium text-sm
                     hover:bg-[#3a3732] disabled:opacity-25 disabled:cursor-not-allowed
                     transition-colors active:scale-[0.98]">
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Analyzing…
            </span>
          ) : 'Check routes'}
        </button>
      </div>

      {!loading && (
        <button onClick={() => { clear(); setOriginName(''); setDestName(''); }}
          className="text-[11px] text-[#b5b0aa] hover:text-[#6b6560] self-start transition-colors">
          Clear
        </button>
      )}
    </div>
  );
}
