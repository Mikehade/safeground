import { create } from 'zustand';
import { streamScout, feedbackApi } from '../services/api';
import type { StreamEvent } from '../services/api';
import type { LocationInput } from '../types';

export interface ToolEvent {
  name: string;
  message: string;
  timestamp: number;
}

interface ScoutState {
  /** Accumulated advisory markdown (streamed token-by-token) */
  advisory: string;
  /** True while the agent is running */
  loading: boolean;
  /** True once the final "done" event arrives */
  done: boolean;
  /** True while tokens are actively streaming */
  streaming: boolean;
  /** Error message if something failed */
  error: string | null;
  /** Total tool calls the agent made */
  toolCalls: number;
  /** Live status message from the backend */
  statusMessage: string;
  /** Ordered list of tool events as they arrive */
  toolEvents: ToolEvent[];

  analyzeRoutes: (origin: LocationInput, dest: LocationInput) => Promise<void>;
  submitFeedback: (helpful: boolean) => Promise<void>;
  clear: () => void;
}

export const useScoutStore = create<ScoutState>((set, get) => ({
  advisory: '',
  loading: false,
  done: false,
  streaming: false,
  error: null,
  toolCalls: 0,
  statusMessage: '',
  toolEvents: [],

  analyzeRoutes: async (origin, dest) => {
    set({
      loading: true,
      done: false,
      streaming: false,
      error: null,
      advisory: '',
      toolCalls: 0,
      statusMessage: '',
      toolEvents: [],
    });

    try {
      await streamScout(
        {
          origin,
          destination: dest,
          current_hour: new Date().getHours(),
        },
        (event: StreamEvent) => {
          switch (event.type) {
            case 'status':
              set({ statusMessage: event.message });
              break;

            case 'tool':
              set((s) => ({
                toolEvents: [
                  ...s.toolEvents,
                  { name: event.name, message: event.message, timestamp: Date.now() },
                ],
              }));
              break;

            case 'token':
              set((s) => ({
                streaming: true,
                advisory: s.advisory + event.text,
              }));
              break;

            case 'advisory':
              // Fallback: full advisory in one shot (non-streaming path)
              set({ advisory: event.text, streaming: false });
              break;

            case 'done':
              set({ toolCalls: event.tool_calls, loading: false, done: true, streaming: false });
              break;

            case 'error':
              set({ error: event.message, loading: false, done: true, streaming: false });
              break;
          }
        },
      );
    } catch (e: any) {
      set({
        error: e?.message || 'Failed to analyze routes. Try again.',
        loading: false,
        done: true,
        streaming: false,
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

  clear: () =>
    set({
      advisory: '',
      error: null,
      toolCalls: 0,
      done: false,
      streaming: false,
      statusMessage: '',
      toolEvents: [],
    }),
}));
