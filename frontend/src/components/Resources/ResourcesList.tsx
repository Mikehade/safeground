import { useResourceStore } from '../../store/useResourceStore';

const typeConfig: Record<string, { icon: string; label: string; color: string }> = {
  shelter: { icon: '🏠', label: 'Shelter', color: 'bg-safe-50 text-safe-700' },
  legal_aid: { icon: '⚖️', label: 'Legal Aid', color: 'bg-blue-50 text-blue-700' },
  hotline: { icon: '📞', label: 'Hotline', color: 'bg-purple-50 text-purple-700' },
  hospital: { icon: '🏥', label: 'Hospital', color: 'bg-red-50 text-red-700' },
  cso: { icon: '🤝', label: 'CSO', color: 'bg-amber-50 text-amber-700' },
  police_oversight: { icon: '👁️', label: 'Oversight', color: 'bg-slate-50 text-slate-700' },
};

export default function ResourcesList() {
  const { resources, loading } = useResourceStore();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-10 h-10 border-[3px] border-ground-200 border-t-ground-800 rounded-full animate-spin" />
      </div>
    );
  }

  if (resources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        <span className="text-5xl mb-4">🆘</span>
        <h2 className="font-display text-xl font-semibold text-ground-800/60">Safety resources</h2>
        <p className="text-sm text-ground-800/35 mt-2 max-w-md">
          Tap "Use my location" in the sidebar to find verified shelters,
          hotlines, legal aid, and support near you.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-6">
      <h2 className="font-display text-lg font-semibold mb-4">
        {resources.length} resource{resources.length > 1 ? 's' : ''} found nearby
      </h2>

      <div className="flex flex-col gap-3">
        {resources.map((r) => {
          const config = typeConfig[r.type] || { icon: '📍', label: r.type, color: 'bg-ground-100 text-ground-800' };
          return (
            <div
              key={r.id}
              className="p-4 rounded-xl bg-white border border-ground-200 hover:border-ground-800/20 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-medium text-sm text-ground-900">{r.name}</h3>
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full shrink-0 ml-3 ${config.color}`}>
                  {config.icon} {config.label}
                </span>
              </div>
              {r.address && <p className="text-xs text-ground-800/50 mb-1">{r.address}</p>}
              {r.operating_hours && <p className="text-xs text-ground-800/40 mb-2">{r.operating_hours}</p>}
              {r.phone && (
                <a
                  href={`tel:${r.phone}`}
                  className="inline-flex items-center gap-1 text-sm font-medium text-safe-700 hover:underline"
                >
                  📞 {r.phone}
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
