import { create } from 'zustand';
import { incidentApi } from '../services/api';
import type { IncidentReport } from '../types';

interface ReportState {
  receiptToken: string | null;
  submitting: boolean;
  error: string | null;
  // status check
  statusResult: { found: boolean; status?: string; incident_type?: string } | null;
  checking: boolean;

  submitReport: (data: IncidentReport) => Promise<void>;
  checkStatus: (token: string) => Promise<void>;
  clear: () => void;
}

export const useReportStore = create<ReportState>((set) => ({
  receiptToken: null,
  submitting: false,
  error: null,
  statusResult: null,
  checking: false,

  submitReport: async (data) => {
    set({ submitting: true, error: null, receiptToken: null });
    try {
      const { data: res } = await incidentApi.report(data);
      set({ receiptToken: res.receipt_token, submitting: false });
    } catch (e: any) {
      set({
        error: e?.response?.data?.detail || 'Failed to submit report.',
        submitting: false,
      });
    }
  },

  checkStatus: async (token) => {
    set({ checking: true, statusResult: null, error: null });
    try {
      const { data: res } = await incidentApi.checkStatus(token);
      set({ statusResult: res, checking: false });
    } catch {
      set({ error: 'Could not check status.', checking: false });
    }
  },

  clear: () => set({ receiptToken: null, error: null, statusResult: null }),
}));
