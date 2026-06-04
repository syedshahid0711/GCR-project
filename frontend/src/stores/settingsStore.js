/**
 * Settings Store — manages user settings.
 */
import { create } from 'zustand';
import { settingsAPI } from '@/lib/api';

const useSettingsStore = create((set) => ({
  settings: {
    auto_submit: true,
    confidence_threshold: 50,
    reminder_frequency: 'standard',
    approval_mode: false,
    notifications: { browser: true, email: false, telegram: false },
    course_filters: {},
  },
  isLoading: false,

  fetchSettings: async () => {
    set({ isLoading: true });
    try {
      const { data } = await settingsAPI.get();
      set({ settings: data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  updateSettings: async (updates) => {
    try {
      const { data } = await settingsAPI.update(updates);
      set({ settings: data.settings });
    } catch { /* ignore */ }
  },
}));

export default useSettingsStore;
