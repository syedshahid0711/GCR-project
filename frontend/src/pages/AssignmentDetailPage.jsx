/**
 * Assignment Detail Page — full assignment view with AI actions.
 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Brain, FileOutput, Upload, XCircle, RotateCcw,
  Clock, BookOpen, Sparkles, CheckCircle2, AlertTriangle,
  FileDown, Eye
} from 'lucide-react';
import useAssignmentStore from '@/stores/assignmentStore';
import { assignmentsAPI } from '@/lib/api';
import { StatusBadge, CategoryBadge, ConfidenceMeter, timeUntil, timeAgo } from '@/components/shared';

export default function AssignmentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentAssignment: a, fetchAssignment, isLoading, classifyAssignment, generateAssignment, submitAssignment, cancelAssignment } = useAssignmentStore();
  const [actionLoading, setActionLoading] = useState('');

  useEffect(() => { fetchAssignment(id); }, [id]);

  const handleAction = async (action, fn) => {
    setActionLoading(action);
    try { await fn(id); await fetchAssignment(id); } catch { /* ignore */ }
    setActionLoading('');
  };

  if (isLoading || !a) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
        <div style={{ color: 'var(--text-muted)' }}>Loading assignment...</div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      {/* Back button */}
      <button onClick={() => navigate(-1)} style={{
        background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, marginBottom: 20, padding: 0,
      }}>
        <ArrowLeft size={16} /> Back
      </button>

      {/* Header */}
      <div className="glass-card-static" style={{ padding: 28, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ flex: 1, minWidth: 280 }}>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
              <StatusBadge state={a.state} />
              <CategoryBadge category={a.category} />
            </div>
            <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>{a.title}</h1>
            {a.course && (
              <p style={{ color: 'var(--text-muted)', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                <BookOpen size={14} /> {a.course.name} {a.course.section && `(${a.course.section})`}
              </p>
            )}
          </div>

          {/* Confidence + Deadline */}
          <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
            {a.ai_confidence > 0 && (
              <div style={{ textAlign: 'center' }}>
                <ConfidenceMeter value={a.ai_confidence} size={72} />
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>AI Confidence</div>
              </div>
            )}
            {a.due_date && (
              <div style={{ textAlign: 'center' }}>
                <div style={{
                  width: 72, height: 72, borderRadius: 16,
                  background: a.is_overdue ? 'rgba(244,63,94,0.1)' : 'rgba(6,182,212,0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
                }}>
                  <Clock size={20} color={a.is_overdue ? '#fb7185' : '#22d3ee'} />
                  <span style={{ fontSize: 11, color: a.is_overdue ? '#fb7185' : '#22d3ee', marginTop: 4, fontWeight: 600 }}>
                    {timeUntil(a.due_date)}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Deadline</div>
              </div>
            )}
          </div>
        </div>

        {/* Due date & points */}
        <div style={{ display: 'flex', gap: 20, marginTop: 16, flexWrap: 'wrap' }}>
          {a.due_date && (
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              📅 Due: {new Date(a.due_date).toLocaleString()}
            </div>
          )}
          {a.max_points && (
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              ⭐ Max Points: {a.max_points}
            </div>
          )}
          {a.ai_output_type && (
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              📄 Output: {a.ai_output_type.toUpperCase()}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="glass-card-static" style={{ padding: 20, marginBottom: 20 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sparkles size={16} color="#818cf8" /> Actions
        </h3>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {a.state === 'NEW' && (
            <button className="btn-primary" disabled={!!actionLoading}
              onClick={() => handleAction('classify', classifyAssignment)} style={{ fontSize: 13 }}>
              <Brain size={14} /> {actionLoading === 'classify' ? 'Classifying...' : 'Classify with AI'}
            </button>
          )}
          {['CLASSIFIED', 'WAITING_FOR_REVIEW', 'OVERDUE'].includes(a.state) && a.category === 'DIGITAL_ASSIGNMENT' && (
            <button className="btn-primary" disabled={!!actionLoading}
              onClick={() => handleAction('generate', generateAssignment)} style={{ fontSize: 13 }}>
              <Brain size={14} /> {actionLoading === 'generate' ? 'Generating...' : 'Generate Solution'}
            </button>
          )}
          {['IN_PROGRESS', 'WAITING_FOR_REVIEW', 'OVERDUE'].includes(a.state) && a.ai_output_path && (
            <button className="btn-primary" disabled={!!actionLoading}
              onClick={() => handleAction('submit', submitAssignment)}
              style={{ fontSize: 13, background: 'linear-gradient(135deg, #10b981, #059669)' }}>
              <Upload size={14} /> {actionLoading === 'submit' ? 'Submitting...' : 'Submit Now'}
            </button>
          )}
          {!['SUBMITTED_BY_AI', 'SUBMITTED_MANUALLY', 'CANCELLED'].includes(a.state) && (
            <button className="btn-danger" disabled={!!actionLoading}
              onClick={() => handleAction('cancel', cancelAssignment)} style={{ fontSize: 13 }}>
              <XCircle size={14} /> Cancel
            </button>
          )}
          {['SUBMITTED_BY_AI'].includes(a.state) && (
            <button className="btn-secondary" disabled={!!actionLoading}
              onClick={() => handleAction('resubmit', () => useAssignmentStore.getState().fetchAssignment(id))} style={{ fontSize: 13 }}>
              <RotateCcw size={14} /> Resubmit
            </button>
          )}
        </div>
      </div>

      {/* Generated File Preview — shown when confidence >= 80% and file exists */}
      {a.ai_confidence >= 80 && a.ai_output_path && (
        <div className="glass-card-static" style={{ padding: 24, marginBottom: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <FileOutput size={16} color="#10b981" /> Generated File — Ready for Submission
          </h3>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 20, padding: 16,
            background: 'rgba(16, 185, 129, 0.06)', borderRadius: 12,
            border: '1px solid rgba(16, 185, 129, 0.15)',
          }}>
            {/* File icon */}
            <div style={{
              width: 56, height: 56, borderRadius: 12,
              background: 'linear-gradient(135deg, rgba(16,185,129,0.15), rgba(6,182,212,0.15))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 24, flexShrink: 0,
            }}>
              {a.ai_output_type === 'pdf' ? '📄' : a.ai_output_type === 'docx' ? '📝' : a.ai_output_type === 'pptx' ? '📊' : a.ai_output_type === 'code' ? '💻' : '📃'}
            </div>

            {/* File info */}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
                AI-Generated {(a.ai_output_type || 'file').toUpperCase()} File
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                <span>Format: <strong style={{ color: 'var(--text-secondary)' }}>{(a.ai_output_type || 'unknown').toUpperCase()}</strong></span>
                <span>Confidence: <strong style={{ color: '#10b981' }}>{Math.round(a.ai_confidence)}%</strong></span>
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
              <a
                href={assignmentsAPI.getDownloadUrl(a.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary"
                style={{
                  fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 6,
                  textDecoration: 'none', padding: '8px 16px',
                }}
              >
                <Eye size={14} /> Open File
              </a>
              <a
                href={assignmentsAPI.getDownloadUrl(a.id)}
                download
                className="btn-secondary"
                style={{
                  fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 6,
                  textDecoration: 'none', padding: '8px 16px',
                }}
              >
                <FileDown size={14} /> Download
              </a>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Description */}
        <div className="glass-card-static" style={{ padding: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>📝 Description</h3>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
            {a.description || 'No description provided.'}
          </p>
          {a.attachments?.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h4 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>📎 Attachments</h4>
              {a.attachments.map((att, i) => (
                <a key={i} href={att.url} target="_blank" rel="noopener noreferrer" style={{
                  display: 'block', padding: '8px 12px', marginBottom: 4,
                  background: 'rgba(255,255,255,0.03)', borderRadius: 8,
                  color: '#818cf8', fontSize: 13, textDecoration: 'none',
                }}>
                  {att.name}
                </a>
              ))}
            </div>
          )}
        </div>

        {/* Activity Timeline */}
        <div className="glass-card-static" style={{ padding: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>📋 Activity Log</h3>
          {a.activity_logs?.length > 0 ? (
            <div>
              {a.activity_logs.map((log, i) => (
                <div key={i} style={{
                  display: 'flex', gap: 12, padding: '8px 0',
                  borderBottom: i < a.activity_logs.length - 1 ? '1px solid rgba(255,255,255,0.03)' : 'none',
                }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%', marginTop: 6, flexShrink: 0,
                    background: log.action === 'SUBMITTED' ? '#10b981' : log.action === 'CANCELLED' ? '#f43f5e' : '#6366f1',
                  }} />
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{log.action.replace(/_/g, ' ')}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{timeAgo(log.created_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No activity recorded yet.</p>
          )}
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          div[style*="grid-template-columns: 1fr 1fr"] {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
