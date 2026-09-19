import { Phone, LifeBuoy } from 'lucide-react';
import { useResourceStore } from '../../store/useResourceStore';

const cfg: Record<string, { label: string; color: string }> = {
  shelter: { label: 'Shelter', color: 'bg-green-50 text-green-700' },
  legal_aid: { label: 'Legal Aid', color: 'bg-blue-50 text-blue-700' },
  hotline: { label: 'Hotline', color: 'bg-purple-50 text-purple-700' },
  hospital: { label: 'Hospital', color: 'bg-red-50 text-red-600' },
  cso: { label: 'CSO', color: 'bg-amber-50 text-amber-700' },
  police_oversight: { label: 'Oversight', color: 'bg-slate-50 text-slate-600' },
};

export default function ResourcesList() {
  const { resources, loading } = useResourceStore();

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 border-[3px] border-[#e8e6e1] border-t-[#2d2a24] rounded-full animate-spin" />
    </div>
  );

  if (!resources.length) return (
    <div className="flex flex-col items-center justify-center h-full text-center px-8">
      <LifeBuoy size={44} strokeWidth={1} className="text-[#d1cec8] mb-4" />
      <h2 className="font-display text-base font-semibold text-[#6b6560]">Safety resources</h2>
      <p className="text-[12px] text-[#b5b0aa] mt-2 max-w-sm">Tap "Use my location" to find verified shelters, hotlines, and support near you.</p>
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto px-5 py-5">
      <h2 className="font-display text-[15px] font-semibold text-[#2d2a24] mb-4">
        {resources.length} resource{resources.length > 1 ? 's' : ''} found
      </h2>
      <div className="flex flex-col gap-2.5">
        {resources.map((r) => {
          const c = cfg[r.type] || { label: r.type, color: 'bg-[#f5f4f1] text-[#6b6560]' };
          return (
            <div key={r.id} className="p-4 rounded-xl bg-white border border-[#e8e6e1] hover:shadow-sm transition-shadow">
              <div className="flex items-start justify-between mb-1.5">
                <h3 className="font-medium text-[13px] text-[#2d2a24]">{r.name}</h3>
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full shrink-0 ml-3 ${c.color}`}>{c.label}</span>
              </div>
              {r.address && <p className="text-[11px] text-[#9b9590] mb-1">{r.address}</p>}
              {r.operating_hours && <p className="text-[10px] text-[#c5c0ba] mb-2">{r.operating_hours}</p>}
              {r.phone && (
                <a href={`tel:${r.phone}`} className="inline-flex items-center gap-1 text-[13px] font-medium text-green-700 hover:underline">
                  <Phone size={12} /> {r.phone}
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
