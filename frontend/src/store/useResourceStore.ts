import { create } from 'zustand';
import type { SafetyResource } from '../types';

interface ResourceState {
  resources: SafetyResource[];
  loading: boolean;
  setResources: (r: SafetyResource[]) => void;
  setLoading: (l: boolean) => void;
}

export const useResourceStore = create<ResourceState>((set) => ({
  resources: [],
  loading: false,
  setResources: (resources) => set({ resources }),
  setLoading: (loading) => set({ loading }),
}));
