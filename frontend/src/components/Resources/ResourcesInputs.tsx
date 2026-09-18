import { useState } from 'react';
import { resourceApi } from '../../services/api';
import { useResourceStore } from '../../store/useResourceStore';

export default function ResourcesInputs() {
  const { setResources, setLoading, loading } = useResourceStore();
  const [locationName, setLocationName] = useState('');

  const handleFindNearby = () => {
    navigator.geolocation?.getCurrentPosition(
      async (pos) => {
        setLoading(true);
        try {
          const { data } = await resourceApi.findNearby(pos.coords.latitude, pos.coords.longitude);
          setResources(data);
        } catch {
          setResources([]);
        }
        setLoading(false);
      },
      () => alert('Location access is needed to find nearby resources.'),
    );
  };

  return (
    <div className="flex flex-col gap-4 p-5">
      <div>
        <h2 className="font-display text-base font-semibold mb-1">Find safety resources</h2>
        <p className="text-xs text-ground-800/50">
          Locate shelters, hotlines, legal aid, and support organizations near you.
        </p>
      </div>

      <button
        onClick={handleFindNearby}
        disabled={loading}
        className="w-full py-2.5 rounded-lg bg-ground-900 text-white font-medium text-sm
                   hover:bg-ground-800 disabled:opacity-30 transition-colors active:scale-[0.98]"
      >
        {loading ? 'Searching…' : '📍 Use my location'}
      </button>

      <div className="text-[10px] text-ground-800/30 leading-relaxed">
        Your location is used only for this search and is never stored.
      </div>
    </div>
  );
}
