/**
 * Auth Store — manages user authentication state.
 */
import { create } from 'zustand';
import { authAPI } from '@/lib/api';

const useAuthStore = create((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  fetchUser: async () => {
    try {
      const { data } = await authAPI.getMe();
      set({ user: data, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  logout: async () => {
    try {
      await authAPI.logout();
    } catch { /* ignore */ }
    set({ user: null, isAuthenticated: false });
    window.location.href = '/';
  },

  setUser: (user) => set({ user, isAuthenticated: !!user, isLoading: false }),
}));

export default useAuthStore;
