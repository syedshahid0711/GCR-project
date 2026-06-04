/**
 * Dashboard Page — main dashboard with stats, timeline, and alerts.
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText, PenTool, Clock, AlertTriangle, CheckCircle2, Upload,
  RefreshCw, TrendingUp, Activity, Sparkles
} from 'lucide-react';
import useAssignmentStore from '@/stores/assignmentStore';
import useAuthStore from '@/stores/authStore';
import { classroomAPI, logsAPI, seedAPI } from '@/lib/api';
import { StatusBadge, ConfidenceMeter, timeAgo, timeUntil, EmptyState } from '@/components/shared';
import { useState } from 'react';

export default function DashboardPage() {
  const { stats, fetchStats, assignments, fetchAssignments } = useAssignmentStore();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [timeline, setTimeline] = useState([]);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchAssignments({ per_page: 10, sort: 'due_date' });
    logsAPI.getTimeline().then(r => setTimeline(r.data)).catch(() => {});
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await classroomAPI.sync();
      await fetchStats();
      await fetchAssignments({ per_page: 10, sort: 'due_date' });
    } catch { /* ignore */ }
    setSyncing(false);
  };

  const handleSeedDemo = async () => {
    try {
      await seedAPI.seed();
      await fetchStats();
      await fetchAssignments({ per_page: 10, sort: 'due_date' });
      const r = await logsAPI.getTimeline();
      setTimeline(r.data);
    } catch { /* ignore */ }
  };

  const statCards = [
    { label: 'Pending', value: stats?.pending || 0, icon: FileText, color: '#818cf8', bg: 'rgba(99,102,241,0.1)' },
    { label: 'Handwritten', value: stats?.handwritten_pending || 0, icon: PenTool, color: '#fbbf24', bg: 'rgba(245,158,11,0.1)' },
    { label: 'Upcoming', value: stats?.upcoming_deadlines || 0, icon: Clock, color: '#22d3ee', bg: 'rgba(6,182,212,0.1)' },
    { label: 'Review Needed', value: stats?.low_confidence_alerts || 0, icon: AlertTriangle, color: '#fb7185', bg: 'rgba(244,63,94,0.1)' },
    { label: 'AI Submitted', value: stats?.submitted_by_ai || 0, icon: CheckCircle2, color: '#34d399', bg: 'rgba(16,185,129,0.1)' },
    { label: 'Manual', value: stats?.submitted_manually || 0, icon: Upload, color: '#a78bfa', bg: 'rgba(167,139,250,0.1)' },
  ];

  const actionIcons = {
    DETECTED: '🔍', CLASSIFIED: '🏷️', AI_GENERATED: '🤖', UPLOADED: '📤',
    SUBMITTED: '✅', CANCELLED: '❌', MANUALLY_SUBMITTED: '👤',
    REMINDER_SENT: '🔔', REVIEW_REQUESTED: '👀', RESUBMITTED: '🔄',
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, marginBottom: 4 }}>
            Welcome back, <span className="gradient-text">{user?.name?.split(' ')[0] || 'Student'}</span> 👋
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
            Here's your classroom overview
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn-secondary" onClick={handleSeedDemo} style={{ fontSize: 13 }}>
            <Sparkles size={14} /> Load Demo
          </button>
          <button className="btn-primary" onClick={handleSync} disabled={syncing} style={{ fontSize: 13 }}>
            <RefreshCw size={14} className={syncing ? 'spinning' : ''} />
            {syncing ? 'Syncing...' : 'Sync Classroom'}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div key={i} className="glass-card animate-fade-in" style={{
              padding: 20, opacity: 0, animationDelay: `${i * 0.08}s`,
              display: 'flex', alignItems: 'center', gap: 16,
            }}>
              <div style={{
                width: 48, height: 48, borderRadius: 12,
                background: card.bg, display: 'flex',
                alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                <Icon size={22} color={card.color} />
              </div>
              <div>
                <div style={{ fontSize: 28, fontWeight: 800, color: card.color, lineHeight: 1 }}>{card.value}</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>{card.label}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Assignments List */}
        <div className="glass-card-static" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{
            padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.05)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Activity size={18} color="#818cf8" /> Upcoming Assignments
            </h3>
            <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }}
              onClick={() => navigate('/assignments')}>View All</button>
          </div>

          {assignments.length === 0 ? (
            <EmptyState icon="📚" title="No assignments yet" description="Click 'Sync Classroom' or 'Load Demo' to get started." />
          ) : (
            <div style={{ maxHeight: 400, overflowY: 'auto' }}>
              {assignments.slice(0, 8).map((a) => (
                <div key={a.id}
                  onClick={() => navigate(`/assignments/${a.id}`)}
                  style={{
                    padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12,
                    transition: 'background 0.2s',
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {a.title}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4, display: 'flex', gap: 12, alignItems: 'center' }}>
                      <span>{timeUntil(a.due_date)}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                    {a.ai_confidence > 0 && <ConfidenceMeter value={a.ai_confidence} size={36} />}
                    <StatusBadge state={a.state} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Activity Timeline */}
        <div className="glass-card-static" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{
            padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.05)',
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
              <TrendingUp size={18} color="#22d3ee" /> AI Activity
            </h3>
          </div>

          {timeline.length === 0 ? (
            <EmptyState icon="🤖" title="No activity yet" description="AI activity will appear here once assignments are processed." />
          ) : (
            <div style={{ maxHeight: 400, overflowY: 'auto', padding: '8px 0' }}>
              {timeline.map((log, i) => (
                <div key={log.id || i} style={{
                  padding: '10px 20px', display: 'flex', gap: 12,
                  alignItems: 'flex-start', fontSize: 13,
                }}>
                  <span style={{ fontSize: 18, flexShrink: 0, marginTop: 2 }}>
                    {actionIcons[log.action] || '📋'}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 500 }}>{log.action.replace(/_/g, ' ')}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 2 }}>
                      {timeAgo(log.created_at)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .spinning { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}
