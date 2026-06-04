/**
 * Notifications Page — grouped notifications with mark-read.
 */
import { useEffect } from 'react';
import {
  Bell, CheckCheck, AlertTriangle, CheckCircle2, XCircle,
  Clock, RotateCcw, User
} from 'lucide-react';
import useNotificationStore from '@/stores/notificationStore';
import { timeAgo, EmptyState } from '@/components/shared';

const typeConfig = {
  REMINDER: { icon: Clock, color: '#22d3ee', bg: 'rgba(6,182,212,0.1)' },
  CONFIDENCE_ALERT: { icon: AlertTriangle, color: '#fbbf24', bg: 'rgba(245,158,11,0.1)' },
  SUBMISSION_SUCCESS: { icon: CheckCircle2, color: '#34d399', bg: 'rgba(16,185,129,0.1)' },
  SUBMISSION_FAILED: { icon: XCircle, color: '#fb7185', bg: 'rgba(244,63,94,0.1)' },
  RESUBMISSION_NEEDED: { icon: RotateCcw, color: '#a78bfa', bg: 'rgba(167,139,250,0.1)' },
  MANUAL_DETECTED: { icon: User, color: '#818cf8', bg: 'rgba(99,102,241,0.1)' },
  ASSIGNMENT_RETURNED: { icon: RotateCcw, color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
};

export default function NotificationsPage() {
  const { notifications, unreadCount, fetchNotifications, markRead, markAllRead } = useNotificationStore();

  useEffect(() => { fetchNotifications({ per_page: 50 }); }, []);

  // Group by date
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  const groups = notifications.reduce((acc, n) => {
    const date = new Date(n.created_at).toDateString();
    const label = date === today ? 'Today' : date === yesterday ? 'Yesterday' : date;
    if (!acc[label]) acc[label] = [];
    acc[label].push(n);
    return acc;
  }, {});

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Bell size={24} color="#818cf8" /> Notifications
          </h1>
          {unreadCount > 0 && (
            <p style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 4 }}>
              {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
            </p>
          )}
        </div>
        {unreadCount > 0 && (
          <button className="btn-secondary" onClick={markAllRead} style={{ fontSize: 13 }}>
            <CheckCheck size={14} /> Mark all read
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="glass-card-static">
          <EmptyState icon="🔔" title="No notifications" description="You're all caught up! Notifications will appear here." />
        </div>
      ) : (
        Object.entries(groups).map(([label, items]) => (
          <div key={label} style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {label}
            </h3>
            <div className="glass-card-static" style={{ overflow: 'hidden' }}>
              {items.map((n, i) => {
                const config = typeConfig[n.type] || typeConfig.REMINDER;
                const Icon = config.icon;
                return (
                  <div key={n.id} onClick={() => !n.is_read && markRead(n.id)} style={{
                    padding: '16px 20px', display: 'flex', gap: 14, alignItems: 'flex-start',
                    borderBottom: i < items.length - 1 ? '1px solid rgba(255,255,255,0.03)' : 'none',
                    background: n.is_read ? 'transparent' : 'rgba(99,102,241,0.03)',
                    cursor: n.is_read ? 'default' : 'pointer',
                    transition: 'background 0.2s',
                  }}>
                    <div style={{
                      width: 38, height: 38, borderRadius: 10,
                      background: config.bg, display: 'flex',
                      alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                    }}>
                      <Icon size={18} color={config.color} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 14, fontWeight: n.is_read ? 400 : 600 }}>{n.title}</span>
                        {!n.is_read && (
                          <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#6366f1', flexShrink: 0 }} />
                        )}
                      </div>
                      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.5 }}>
                        {n.message}
                      </p>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4, display: 'block' }}>
                        {timeAgo(n.created_at)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
