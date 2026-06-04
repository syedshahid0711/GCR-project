/**
 * Assignments List Page — filterable table of all assignments.
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Filter, Search } from 'lucide-react';
import useAssignmentStore from '@/stores/assignmentStore';
import { StatusBadge, CategoryBadge, ConfidenceMeter, timeUntil, EmptyState } from '@/components/shared';
import { useState } from 'react';

const STATE_OPTIONS = [
  { value: '', label: 'All States' },
  { value: 'NEW', label: 'New' },
  { value: 'CLASSIFIED', label: 'Classified' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'WAITING_FOR_REVIEW', label: 'Needs Review' },
  { value: 'SUBMITTED_BY_AI', label: 'Submitted (AI)' },
  { value: 'SUBMITTED_MANUALLY', label: 'Submitted (Manual)' },
  { value: 'HANDWRITTEN_PENDING', label: 'Handwritten' },
  { value: 'OVERDUE', label: 'Overdue' },
  { value: 'CANCELLED', label: 'Cancelled' },
];

const CATEGORY_OPTIONS = [
  { value: '', label: 'All Categories' },
  { value: 'DIGITAL_ASSIGNMENT', label: 'Digital' },
  { value: 'HANDWRITTEN_ASSIGNMENT', label: 'Handwritten' },
  { value: 'GENERAL_ANNOUNCEMENT', label: 'Announcement' },
  { value: 'EXAM_NOTICE', label: 'Exam' },
];

export default function AssignmentsPage() {
  const { assignments, fetchAssignments, isLoading, pagination, setFilters, filters } = useAssignmentStore();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  useEffect(() => { fetchAssignments(); }, []);

  const filtered = search
    ? assignments.filter(a => a.title.toLowerCase().includes(search.toLowerCase()))
    : assignments;

  return (
    <div className="animate-fade-in">
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 20 }}>📚 Assignments</h1>

      {/* Filters */}
      <div className="glass-card-static" style={{ padding: 16, marginBottom: 20, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1 1 200px' }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input className="input-field" placeholder="Search assignments..." value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 36 }} />
        </div>
        <select className="input-field" style={{ flex: '0 0 160px', cursor: 'pointer' }}
          value={filters.state} onChange={(e) => setFilters({ state: e.target.value })}>
          {STATE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select className="input-field" style={{ flex: '0 0 160px', cursor: 'pointer' }}
          value={filters.category} onChange={(e) => setFilters({ category: e.target.value })}>
          {CATEGORY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="glass-card-static" style={{ overflow: 'hidden' }}>
        {isLoading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading...</div>
        ) : filtered.length === 0 ? (
          <EmptyState icon="📭" title="No assignments found" description="Sync your Google Classroom or adjust your filters." />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Category</th>
                <th>State</th>
                <th>Confidence</th>
                <th>Deadline</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a.id} style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/assignments/${a.id}`)}>
                  <td>
                    <div style={{ fontWeight: 500, maxWidth: 300, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {a.title}
                    </div>
                  </td>
                  <td><CategoryBadge category={a.category} /></td>
                  <td><StatusBadge state={a.state} /></td>
                  <td>{a.ai_confidence > 0 ? <ConfidenceMeter value={a.ai_confidence} size={36} /> : <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>—</span>}</td>
                  <td>
                    <span style={{
                      fontSize: 13,
                      color: a.is_overdue ? '#fb7185' : 'var(--text-secondary)',
                      fontWeight: a.is_overdue ? 600 : 400,
                    }}>
                      {timeUntil(a.due_date)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 20 }}>
          {Array.from({ length: pagination.pages }, (_, i) => (
            <button key={i} className={i + 1 === pagination.page ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '6px 12px', fontSize: 13, minWidth: 36 }}
              onClick={() => fetchAssignments({ page: i + 1 })}>
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
