/**
 * Activity Logs Page — searchable, filterable log table.
 */
import { useEffect, useState } from 'react';
import { ScrollText, Filter, Search } from 'lucide-react';
import { logsAPI } from '@/lib/api';
import { timeAgo, EmptyState } from '@/components/shared';

const ACTION_COLORS = {
  DETECTED: '#818cf8', CLASSIFIED: '#22d3ee', AI_GENERATED: '#a78bfa',
  UPLOADED: '#818cf8', SUBMITTED: '#34d399', CANCELLED: '#94a3b8',
  MANUALLY_SUBMITTED: '#10b981', REMINDER_SENT: '#fbbf24',
  REVIEW_REQUESTED: '#f59e0b', RESUBMITTED: '#a78bfa',
  VERIFICATION_PASSED: '#34d399', VERIFICATION_FAILED: '#fb7185',
};

const ACTION_ICONS = {
  DETECTED: '🔍', CLASSIFIED: '🏷️', AI_GENERATED: '🤖', UPLOADED: '📤',
  SUBMITTED: '✅', CANCELLED: '❌', MANUALLY_SUBMITTED: '👤',
  REMINDER_SENT: '🔔', REVIEW_REQUESTED: '👀', RESUBMITTED: '🔄',
  VERIFICATION_PASSED: '✓', VERIFICATION_FAILED: '✗',
};

const FILTER_OPTIONS = [
  { value: '', label: 'All Actions' },
  { value: 'DETECTED', label: 'Detected' },
  { value: 'CLASSIFIED', label: 'Classified' },
  { value: 'AI_GENERATED', label: 'AI Generated' },
  { value: 'SUBMITTED', label: 'Submitted' },
  { value: 'CANCELLED', label: 'Cancelled' },
  { value: 'MANUALLY_SUBMITTED', label: 'Manual Submit' },
  { value: 'REMINDER_SENT', label: 'Reminder' },
];

export default function ActivityLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 30 };
      if (filter) params.action = filter;
      const { data } = await logsAPI.getAll(params);
      setLogs(data.logs);
      setTotalPages(data.pages);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchLogs(); }, [filter, page]);

  return (
    <div className="animate-fade-in">
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
        <ScrollText size={24} color="#818cf8" /> Activity Logs
      </h1>

      {/* Filter bar */}
      <div className="glass-card-static" style={{ padding: 16, marginBottom: 20, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <Filter size={16} color="var(--text-muted)" />
        <select className="input-field" value={filter} onChange={(e) => { setFilter(e.target.value); setPage(1); }}
          style={{ width: 200, cursor: 'pointer' }}>
          {FILTER_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Showing page {page} of {totalPages}
        </span>
      </div>

      {/* Logs */}
      <div className="glass-card-static" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading logs...</div>
        ) : logs.length === 0 ? (
          <EmptyState icon="📋" title="No activity logs" description="Logs will appear here as the AI processes your assignments." />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 50 }}></th>
                <th>Action</th>
                <th>Details</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ textAlign: 'center', fontSize: 18 }}>
                    {ACTION_ICONS[log.action] || '📋'}
                  </td>
                  <td>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: 6,
                      padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                      background: `${ACTION_COLORS[log.action] || '#818cf8'}15`,
                      color: ACTION_COLORS[log.action] || '#818cf8',
                    }}>
                      {log.action.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 400 }}>
                    {log.details ? (
                      <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', display: 'block' }}>
                        {typeof log.details === 'object' ? JSON.stringify(log.details).slice(0, 80) : log.details}
                      </span>
                    ) : '—'}
                  </td>
                  <td style={{ fontSize: 13, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {timeAgo(log.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 20 }}>
          <button className="btn-secondary" disabled={page <= 1}
            onClick={() => setPage(p => Math.max(1, p - 1))} style={{ fontSize: 13, padding: '6px 12px' }}>
            Previous
          </button>
          <span style={{ display: 'flex', alignItems: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
            {page} / {totalPages}
          </span>
          <button className="btn-secondary" disabled={page >= totalPages}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))} style={{ fontSize: 13, padding: '6px 12px' }}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}
