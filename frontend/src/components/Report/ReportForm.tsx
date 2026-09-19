import { useState } from 'react';
import { MapPin, AlertTriangle } from 'lucide-react';
import { useReportStore } from '../../store/useReportStore';

const TYPES = [
  { value: 'police_brutality', label: 'Police brutality' },
  { value: 'corruption', label: 'Corruption' },
  { value: 'gbv', label: 'Gender-based violence' },
  { value: 'gang_activity', label: 'Gang activity' },
  { value: 'unrest', label: 'Unrest / protest' },
  { value: 'robbery', label: 'Robbery' },
  { value: 'electoral', label: 'Electoral irregularity' },
  { value: 'other', label: 'Other' },
];

export default function ReportForm() {
  const { receiptToken, submitting, error, submitReport, clear } = useReportStore();
  const [type, setType] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);

  const handleGeo = () => {
    navigator.geolocation?.getCurrentPosition(
      (p) => { setCoords({ lat: p.coords.latitude, lng: p.coords.longitude }); setLocation('Current location'); },
      () => setLocation('Could not get location'),
    );
  };

  const handleSubmit = () => {
    if (!type || !coords) return;
    submitReport({ incident_type: type, latitude: coords.lat, longitude: coords.lng,
      description: description || undefined, city: location || undefined });
  };

  if (receiptToken) {
    return (
      <div className="flex flex-col items-center gap-3 p-5 text-center">
        <span className="w-10 h-10 rounded-full bg-green-50 flex items-center justify-center text-green-600 text-lg">✓</span>
        <p className="text-sm font-medium text-green-700">Report submitted</p>
        <p className="text-[11px] text-[#9b9590]">View your receipt token in the main panel.</p>
        <button onClick={() => { clear(); setType(''); setDescription(''); setLocation(''); setCoords(null); }}
          className="text-[11px] text-[#b5b0aa] hover:text-[#6b6560] underline mt-1">Submit another</button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 p-5">
      <div>
        <h2 className="font-display text-[15px] font-semibold text-[#2d2a24] mb-1">Report an incident</h2>
        <p className="text-[11px] text-[#9b9590]">Anonymous. No account needed. No data stored about you.</p>
      </div>

      <div className="flex flex-col gap-2.5">
        <div>
          <label className="block text-[11px] font-medium text-[#6b6560] mb-1">What happened?</label>
          <select value={type} onChange={(e) => setType(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] text-sm
                       focus:outline-none focus:border-[#6b6560] focus:bg-white transition-colors">
            <option value="">Select type</option>
            {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-medium text-[#6b6560] mb-1">Where?</label>
          <div className="flex gap-2">
            <input type="text" placeholder="Area / landmark" value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="flex-1 px-3 py-2.5 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] text-sm
                         placeholder:text-[#c5c0ba] focus:outline-none focus:border-[#6b6560] focus:bg-white transition-colors" />
            <button onClick={handleGeo}
              className="px-3 py-2.5 rounded-xl border border-[#e8e6e1] hover:bg-[#f5f4f1] transition-colors" title="Use my location">
              <MapPin size={14} className="text-[#6b6560]" />
            </button>
          </div>
        </div>

        {!coords && (
          <div className="flex gap-2">
            <input type="number" step="any" placeholder="Latitude"
              onChange={(e) => setCoords((c) => ({ lat: parseFloat(e.target.value) || 0, lng: c?.lng || 0 }))}
              className="flex-1 px-3 py-2 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] text-sm placeholder:text-[#c5c0ba] focus:outline-none focus:border-[#6b6560] transition-colors" />
            <input type="number" step="any" placeholder="Longitude"
              onChange={(e) => setCoords((c) => ({ lat: c?.lat || 0, lng: parseFloat(e.target.value) || 0 }))}
              className="flex-1 px-3 py-2 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] text-sm placeholder:text-[#c5c0ba] focus:outline-none focus:border-[#6b6560] transition-colors" />
          </div>
        )}

        {/* Privacy warning */}
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-50 border border-amber-100">
          <AlertTriangle size={13} className="text-amber-500 mt-0.5 shrink-0" />
          <p className="text-[10px] text-amber-700 leading-relaxed">
            <strong>Do not include your name, phone number, address, or any information that could identify you.</strong> Describe only what happened, where, and when.
          </p>
        </div>

        <div>
          <label className="block text-[11px] font-medium text-[#6b6560] mb-1">Details (optional)</label>
          <textarea placeholder="What happened? When? Keep it factual." value={description}
            onChange={(e) => setDescription(e.target.value)} rows={3}
            className="w-full px-3 py-2.5 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] text-sm
                       placeholder:text-[#c5c0ba] focus:outline-none focus:border-[#6b6560] focus:bg-white transition-colors resize-none" />
        </div>

        {error && <div className="p-2.5 rounded-lg bg-red-50 text-red-600 text-[11px]">{error}</div>}

        <button onClick={handleSubmit} disabled={submitting || !type || !coords}
          className="w-full py-2.5 rounded-xl bg-[#2d2a24] text-white font-medium text-sm
                     hover:bg-[#3a3732] disabled:opacity-25 disabled:cursor-not-allowed transition-colors active:scale-[0.98]">
          {submitting ? 'Submitting…' : 'Submit report'}
        </button>
      </div>
    </div>
  );
}
