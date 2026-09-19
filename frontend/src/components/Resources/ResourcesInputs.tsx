import { MapPin } from 'lucide-react';
import { resourceApi } from '../../services/api';
import { useResourceStore } from '../../store/useResourceStore';

export default function ResourcesInputs() {
  const { setResources, setLoading, loading } = useResourceStore();

  const handleFind = () => {
    navigator.geolocation?.getCurrentPosition(
      async (pos) => {
        setLoading(true);
        try { const { data } = await resourceApi.findNearby(pos.coords.latitude, pos.coords.longitude); setResources(data); }
        catch { setResources([]); }
        setLoading(false);
      },
      () => alert('Location access is needed.'),
    );
  };

  return (
    <div className="flex flex-col gap-4 p-5">
      <div>
        <h2 className="font-display text-[15px] font-semibold text-[#2d2a24] mb-1">Find safety resources</h2>
        <p className="text-[11px] text-[#9b9590]">Locate shelters, hotlines, legal aid, and support near you.</p>
      </div>
      <button onClick={handleFind} disabled={loading}
        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#2d2a24] text-white font-medium text-sm
                   hover:bg-[#3a3732] disabled:opacity-25 transition-colors active:scale-[0.98]">
        <MapPin size={14} /> {loading ? 'Searching…' : 'Use my location'}
      </button>
      <p className="text-[10px] text-[#c5c0ba]">Your location is used only for this search and is never stored.</p>
    </div>
  );
}
