/**
 * Assignment Store — manages assignments, stats, and filtering.
 */
import { create } from 'zustand';
import { assignmentsAPI } from '@/lib/api';

const useAssignmentStore = create((set, get) => ({
  assignments: [],
  currentAssignment: null,
  stats: null,
  isLoading: false,
  filters: { state: '', category: '', course_id: '', sort: 'due_date' },
  pagination: { page: 1, pages: 1, total: 0 },

  fetchAssignments: async (params = {}) => {
    set({ isLoading: true });
    try {
      const mergedParams = { ...get().filters, ...params };
      const { data } = await assignmentsAPI.getAll(mergedParams);
      set({
        assignments: data.assignments,
        pagination: { page: data.page, pages: data.pages, total: data.total },
        isLoading: false,
      });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchAssignment: async (id) => {
    set({ isLoading: true });
    try {
      const { data } = await assignmentsAPI.getById(id);
      set({ currentAssignment: data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchStats: async () => {
    try {
      const { data } = await assignmentsAPI.getStats();
      set({ stats: data });
    } catch { /* ignore */ }
  },

  setFilters: (filters) => {
    set({ filters: { ...get().filters, ...filters } });
    get().fetchAssignments();
  },

  classifyAssignment: async (id) => {
    const { data } = await assignmentsAPI.classify(id);
    get().fetchAssignments();
    return data;
  },

  generateAssignment: async (id, format) => {
    const { data } = await assignmentsAPI.generate(id, format);
    get().fetchAssignments();
    return data;
  },

  submitAssignment: async (id) => {
    const { data } = await assignmentsAPI.submit(id);
    get().fetchAssignments();
    return data;
  },

  cancelAssignment: async (id) => {
    const { data } = await assignmentsAPI.cancel(id);
    get().fetchAssignments();
    return data;
  },
}));

export default useAssignmentStore;
