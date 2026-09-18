import { useState } from 'react';
import { useScoutStore } from '../../store/useScoutStore';

export default function ScoutInputs() {
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
        <h2 className="font-display text-base font-semibold mb-1">Check your route</h2>
        <p className="text-xs text-ground-800/50">
          Enter your origin and destination. We'll scan incident databases
          and live sources for each possible route.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <div>
          <label className="block text-xs font-medium text-ground-800/60 mb-1">From</label>
          <input
            type="text"
            placeholder="e.g. Ikorodu Garage, Lagos"
            value={originName}
            onChange={(e) => setOriginName(e.target.value)}
            className="w-full px-3 py-2.5 rounded-lg border border-ground-200 bg-ground-50
                       text-sm placeholder:text-ground-800/25 focus:outline-none
                       focus:border-ground-800 focus:bg-white transition-colors"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-ground-800/60 mb-1">To</label>
          <input
            type="text"
            placeholder="e.g. Redemption Camp"
            value={destName}
            onChange={(e) => setDestName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            className="w-full px-3 py-2.5 rounded-lg border border-ground-200 bg-ground-50
                       text-sm placeholder:text-ground-800/25 focus:outline-none
                       focus:border-ground-800 focus:bg-white transition-colors"
          />
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading || !originName.trim() || !destName.trim()}
          className="w-full py-2.5 rounded-lg bg-ground-900 text-white font-medium text-sm
                     hover:bg-ground-800 disabled:opacity-30 disabled:cursor-not-allowed
                     transition-colors active:scale-[0.98]"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Analyzing…
            </span>
          ) : (
            'Check routes'
          )}
        </button>
      </div>

      {loading && (
        <div className="flex flex-col gap-2 py-2 text-xs text-ground-800/40">
          <p>Scanning incident database…</p>
          <p>Searching live web sources…</p>
          <p>This may take 30–60 seconds.</p>
        </div>
      )}

      <button
        onClick={() => { clear(); setOriginName(''); setDestName(''); }}
        className="text-xs text-ground-800/40 hover:text-ground-900 self-start transition-colors"
      >
        Clear
      </button>
    </div>
  );
}
