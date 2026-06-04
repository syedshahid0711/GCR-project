/**
 * Shared utility components and helpers.
 */

/** Status badge component */
export function StatusBadge({ state }) {
  const config = {
    NEW: { label: 'New', className: 'badge-new' },
    CLASSIFIED: { label: 'Classified', className: 'badge-new' },
    IN_PROGRESS: { label: 'In Progress', className: 'badge-progress' },
    WAITING_FOR_REVIEW: { label: 'Needs Review', className: 'badge-review' },
    SUBMITTED_BY_AI: { label: 'Submitted (AI)', className: 'badge-submitted' },
    SUBMITTED_MANUALLY: { label: 'Submitted', className: 'badge-manual' },
    CANCELLED: { label: 'Cancelled', className: 'badge-cancelled' },
    OVERDUE: { label: 'Overdue', className: 'badge-overdue' },
    HANDWRITTEN_PENDING: { label: 'Handwritten', className: 'badge-handwritten' },
  };
  const c = config[state] || { label: state, className: 'badge-new' };
  return <span className={`badge ${c.className}`}>{c.label}</span>;
}

/** Category badge */
export function CategoryBadge({ category }) {
  const config = {
    DIGITAL_ASSIGNMENT: { label: '💻 Digital', className: 'badge-digital' },
    HANDWRITTEN_ASSIGNMENT: { label: '✍️ Handwritten', className: 'badge-handwritten' },
    GENERAL_ANNOUNCEMENT: { label: '📢 Announcement', className: 'badge-announcement' },
    DEADLINE_UPDATE: { label: '📅 Deadline', className: 'badge-review' },
    CLASS_RESCHEDULE: { label: '🔄 Reschedule', className: 'badge-announcement' },
    EXAM_NOTICE: { label: '📝 Exam', className: 'badge-overdue' },
    UNKNOWN: { label: '❓ Unknown', className: 'badge-cancelled' },
  };
  const c = config[category] || { label: category, className: 'badge-cancelled' };
  return <span className={`badge ${c.className}`}>{c.label}</span>;
}

/** Confidence meter (circular) */
export function ConfidenceMeter({ value, size = 56 }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  const color = value >= 70 ? '#10b981' : value >= 50 ? '#f59e0b' : '#f43f5e';

  return (
    <div className="confidence-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
      </svg>
      <span className="value" style={{ color, fontSize: size * 0.24 }}>{Math.round(value)}%</span>
    </div>
  );
}

/** Time ago helper */
export function timeAgo(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return date.toLocaleDateString();
}

/** Time until helper */
export function timeUntil(dateStr) {
  if (!dateStr) return 'No deadline';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((date - now) / 1000);
  if (diff < 0) return 'Overdue';
  if (diff < 3600) return `${Math.floor(diff / 60)}m left`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h left`;
  return `${Math.floor(diff / 86400)}d left`;
}

/** Empty state component */
export function EmptyState({ icon, title, description }) {
  return (
    <div style={{
      textAlign: 'center', padding: '60px 20px',
      color: 'var(--text-muted)',
    }}>
      <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.5 }}>{icon || '📭'}</div>
      <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>{title}</h3>
      <p style={{ fontSize: 14, maxWidth: 400, margin: '0 auto' }}>{description}</p>
    </div>
  );
}

/** Loading skeleton */
export function Skeleton({ width = '100%', height = 20, borderRadius = 8 }) {
  return (
    <div style={{
      width, height, borderRadius,
      background: 'linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.06) 50%, rgba(255,255,255,0.03) 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite',
    }} />
  );
}
