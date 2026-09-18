import { useState } from 'react';
import { useReportStore } from '../../store/useReportStore';

const INCIDENT_TYPES = [
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

  const handleUseMyLocation = () => {
    navigator.geolocation?.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocation('Current location');
      },
      () => setLocation('Could not get location'),
    );
  };

  const handleSubmit = () => {
    if (!type || !coords) return;
    submitReport({
      incident_type: type,
      latitude: coords.lat,
      longitude: coords.lng,
      description: description || undefined,
      city: location || undefined,
    });
  };

  if (receiptToken) {
    return (
      <div className="flex flex-col items-center gap-3 p-5 text-center">
        <span className="text-3xl">✓</span>
        <p className="text-sm font-medium text-safe-700">Report submitted</p>
        <p className="text-xs text-ground-800/50">
          View your receipt token in the main panel. →
        </p>
        <button
          onClick={() => { clear(); setType(''); setDescription(''); setLocation(''); setCoords(null); }}
          className="text-xs text-ground-800/40 hover:text-ground-900 underline mt-1"
        >
          Submit another
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 p-5">
      <div>
        <h2 className="font-display text-base font-semibold mb-1">Report an incident</h2>
        <p className="text-xs text-ground-800/50">
          Anonymous. No account. No data stored about you.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <div>
          <label className="block text-xs font-medium text-ground-800/60 mb-1">What happened?</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="w-full px-3 py-2.5 rounded-lg border border-ground-200 bg-ground-50 text-sm
                       focus:outline-none focus:border-ground-800 focus:bg-white transition-colors"
          >
            <option value="">Select type</option>
            {INCIDENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-ground-800/60 mb-1">Where?</label>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Area / landmark"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="flex-1 px-3 py-2.5 rounded-lg border border-ground-200 bg-ground-50 text-sm
                         placeholder:text-ground-800/25 focus:outline-none focus:border-ground-800
                         focus:bg-white transition-colors"
            />
            <button
              onClick={handleUseMyLocation}
              className="px-3 py-2.5 rounded-lg border border-ground-200 text-sm
                         hover:bg-ground-100 transition-colors"
              title="Use my location"
            >
              📍
            </button>
          </div>
        </div>

        {!coords && (
          <div className="flex gap-2">
            <input
              type="number" step="any" placeholder="Latitude"
              onChange={(e) => setCoords((c) => ({ lat: parseFloat(e.target.value) || 0, lng: c?.lng || 0 }))}
              className="flex-1 px-3 py-2 rounded-lg border border-ground-200 bg-ground-50 text-sm
                         placeholder:text-ground-800/25 focus:outline-none focus:border-ground-800 transition-colors"
            />
            <input
              type="number" step="any" placeholder="Longitude"
              onChange={(e) => setCoords((c) => ({ lat: c?.lat || 0, lng: parseFloat(e.target.value) || 0 }))}
              className="flex-1 px-3 py-2 rounded-lg border border-ground-200 bg-ground-50 text-sm
                         placeholder:text-ground-800/25 focus:outline-none focus:border-ground-800 transition-colors"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-ground-800/60 mb-1">Details (optional)</label>
          <textarea
            placeholder="What happened? When?"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full px-3 py-2.5 rounded-lg border border-ground-200 bg-ground-50 text-sm
                       placeholder:text-ground-800/25 focus:outline-none focus:border-ground-800
                       focus:bg-white transition-colors resize-none"
          />
        </div>

        {error && <div className="p-2.5 rounded-lg bg-danger-50 text-danger-700 text-xs">{error}</div>}

        <button
          onClick={handleSubmit}
          disabled={submitting || !type || !coords}
          className="w-full py-2.5 rounded-lg bg-ground-900 text-white font-medium text-sm
                     hover:bg-ground-800 disabled:opacity-30 disabled:cursor-not-allowed
                     transition-colors active:scale-[0.98]"
        >
          {submitting ? 'Submitting…' : 'Submit report'}
        </button>
      </div>
    </div>
  );
}
