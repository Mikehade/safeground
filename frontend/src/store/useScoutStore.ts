import { create } from 'zustand';
import { scoutApi, feedbackApi } from '../services/api';
import type { LocationInput } from '../types';

interface ScoutState {
  advisory: string;
  loading: boolean;
  error: string | null;
  toolCalls: number;
  analyzeRoutes: (origin: LocationInput, dest: LocationInput) => Promise<void>;
  submitFeedback: (helpful: boolean) => Promise<void>;
  clear: () => void;
}

export const useScoutStore = create<ScoutState>((set) => ({
  advisory: '',
  loading: false,
  error: null,
  toolCalls: 0,

  analyzeRoutes: async (origin, dest) => {
    set({ loading: true, error: null, advisory: '' });
    try {
      const { data } = await scoutApi.analyze({
        origin,
        destination: dest,
        current_hour: new Date().getHours(),
      });
      set({ advisory: data.advisory, toolCalls: data.tool_calls, loading: false });
    } catch (e: any) {
      set({
        error: e?.response?.data?.detail || 'Failed to analyze routes. Try again.',
        loading: false,
      });
    }
  },

  submitFeedback: async (helpful) => {
    try {
      await feedbackApi.submit({ helpful, context: 'scout' });
    } catch {
      /* silent */
    }
  },

  clear: () => set({ advisory: '', error: null, toolCalls: 0 }),
}));
