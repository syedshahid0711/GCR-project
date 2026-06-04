/**
 * Sidebar — main navigation sidebar with glassmorphism.
 */
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, FileText, Bell, Settings, ScrollText,
  LogOut, GraduationCap, ChevronLeft, Menu
} from 'lucide-react';
import { useState } from 'react';
import useAuthStore from '@/stores/authStore';
import useNotificationStore from '@/stores/notificationStore';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/assignments', label: 'Assignments', icon: FileText },
  { path: '/notifications', label: 'Notifications', icon: Bell },
  { path: '/activity-logs', label: 'Activity Logs', icon: ScrollText },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const { unreadCount } = useNotificationStore();
  const location = useLocation();

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="mobile-menu-btn"
        onClick={() => setMobileOpen(!mobileOpen)}
        style={{
          position: 'fixed', top: 16, left: 16, zIndex: 1001,
          background: 'rgba(99,102,241,0.2)', border: '1px solid rgba(99,102,241,0.3)',
          borderRadius: 8, padding: '8px', color: '#818cf8', cursor: 'pointer',
          display: 'none',
        }}
      >
        <Menu size={20} />
      </button>

      {/* Overlay */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
            zIndex: 999, display: 'none',
          }}
          className="mobile-overlay"
        />
      )}

      <aside
        style={{
          position: 'fixed', left: 0, top: 0, bottom: 0,
          width: collapsed ? 72 : 260,
          background: 'rgba(10, 10, 30, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRight: '1px solid rgba(255,255,255,0.06)',
          display: 'flex', flexDirection: 'column',
          zIndex: 1000,
          transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          overflow: 'hidden',
        }}
      >
        {/* Logo */}
        <div style={{
          padding: collapsed ? '20px 16px' : '20px 24px',
          display: 'flex', alignItems: 'center', gap: 12,
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          minHeight: 72,
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'var(--gradient-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <GraduationCap size={20} color="white" />
          </div>
          {!collapsed && (
            <div style={{ overflow: 'hidden', whiteSpace: 'nowrap' }}>
              <div style={{ fontWeight: 700, fontSize: 16 }}>EduAI</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Assistant</div>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            style={{
              marginLeft: 'auto', background: 'none', border: 'none',
              color: 'var(--text-muted)', cursor: 'pointer', padding: 4,
              display: collapsed ? 'none' : 'block',
            }}
          >
            <ChevronLeft size={16} />
          </button>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: 4 }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path ||
              (item.path === '/assignments' && location.pathname.startsWith('/assignments'));
            const showBadge = item.path === '/notifications' && unreadCount > 0;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: collapsed ? '12px 16px' : '10px 16px',
                  borderRadius: 10, textDecoration: 'none',
                  color: isActive ? '#fff' : 'var(--text-secondary)',
                  background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  borderLeft: isActive ? '3px solid #6366f1' : '3px solid transparent',
                  transition: 'all 0.2s ease',
                  position: 'relative',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  fontSize: 14, fontWeight: isActive ? 600 : 400,
                }}
              >
                <Icon size={18} style={{ flexShrink: 0 }} />
                {!collapsed && <span>{item.label}</span>}
                {showBadge && (
                  <span style={{
                    position: collapsed ? 'absolute' : 'relative',
                    top: collapsed ? 6 : 'auto',
                    right: collapsed ? 10 : 'auto',
                    marginLeft: collapsed ? 0 : 'auto',
                    background: '#f43f5e', color: 'white',
                    fontSize: 10, fontWeight: 700,
                    padding: '2px 6px', borderRadius: 10,
                    minWidth: 18, textAlign: 'center',
                  }}>
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User section */}
        <div style={{
          padding: collapsed ? '16px 8px' : '16px',
          borderTop: '1px solid rgba(255,255,255,0.06)',
        }}>
          {user && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              marginBottom: 8, justifyContent: collapsed ? 'center' : 'flex-start',
            }}>
              <img
                src={user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=6366f1&color=fff`}
                alt={user.name}
                style={{ width: 32, height: 32, borderRadius: '50%', flexShrink: 0 }}
              />
              {!collapsed && (
                <div style={{ overflow: 'hidden' }}>
                  <div style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                    {user.name}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                    {user.email}
                  </div>
                </div>
              )}
            </div>
          )}
          <button
            onClick={logout}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              width: '100%', padding: '8px 12px',
              background: 'rgba(244, 63, 94, 0.1)',
              border: '1px solid rgba(244, 63, 94, 0.2)',
              borderRadius: 8, color: '#fb7185',
              cursor: 'pointer', fontSize: 13,
              justifyContent: collapsed ? 'center' : 'flex-start',
              transition: 'all 0.2s ease',
            }}
          >
            <LogOut size={16} />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      <style>{`
        @media (max-width: 768px) {
          .mobile-menu-btn { display: block !important; }
          .mobile-overlay { display: block !important; }
          aside {
            transform: translateX(${mobileOpen ? '0' : '-100%'}) !important;
            width: 260px !important;
          }
        }
      `}</style>
    </>
  );
}
