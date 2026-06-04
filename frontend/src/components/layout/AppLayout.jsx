/**
 * AppLayout — main layout wrapper with sidebar + content area.
 */
import { Outlet, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import Sidebar from './Sidebar';
import useAuthStore from '@/stores/authStore';
import useNotificationStore from '@/stores/notificationStore';

export default function AppLayout() {
  const { isAuthenticated, isLoading, fetchUser } = useAuthStore();
  const { fetchNotifications } = useNotificationStore();

  useEffect(() => {
    fetchUser();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifications();
      const interval = setInterval(() => fetchNotifications(), 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  if (isLoading) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        minHeight: '100vh', background: 'var(--bg-primary)',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: 'var(--gradient-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 16px', animation: 'pulse-glow 2s ease-in-out infinite',
          }}>
            <span style={{ fontSize: 24 }}>🎓</span>
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Loading EduAI Assistant...</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
