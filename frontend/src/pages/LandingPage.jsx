/**
 * Landing Page — hero section with feature cards and CTA.
 */
import { useNavigate } from 'react-router-dom';
import { Brain, Shield, Clock, Zap, BookOpen, Bell, ArrowRight, GraduationCap, Sparkles } from 'lucide-react';

const features = [
  { icon: Brain, title: 'AI-Powered Classification', desc: 'Automatically categorizes assignments, announcements, and deadlines using Google Gemini AI.', color: '#818cf8' },
  { icon: Zap, title: 'Auto-Solve & Submit', desc: 'Generates PDF, DOCX, PPTX, code files and submits digital assignments before deadline.', color: '#22d3ee' },
  { icon: Shield, title: 'Smart Safety Rules', desc: 'Never touches handwritten assignments. Detects manual submissions. No duplicate work.', color: '#10b981' },
  { icon: Clock, title: 'Deadline Management', desc: 'Smart reminders at 2 days, 12 hours, 2 hours, and 30 minutes before every deadline.', color: '#f59e0b' },
  { icon: BookOpen, title: 'OCR Processing', desc: 'Reads PDFs, images, docs, and slides. Extracts text with Tesseract OCR when needed.', color: '#f43f5e' },
  { icon: Bell, title: 'Multi-Channel Alerts', desc: 'Browser, email, and Telegram notifications. Confidence alerts for review.', color: '#a78bfa' },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      {/* Animated background */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0,
        background: 'radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.06) 0%, transparent 50%), radial-gradient(ellipse at 50% 80%, rgba(6,182,212,0.05) 0%, transparent 50%)',
      }} />

      {/* Header */}
      <header style={{
        position: 'relative', zIndex: 10, padding: '20px 40px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        maxWidth: 1200, margin: '0 auto',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 12,
            background: 'var(--gradient-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <GraduationCap size={22} color="white" />
          </div>
          <span style={{ fontWeight: 800, fontSize: 20 }}>
            <span className="gradient-text">EduAI</span> Assistant
          </span>
        </div>
        <button className="btn-primary" onClick={() => navigate('/login')}>
          Get Started <ArrowRight size={16} />
        </button>
      </header>

      {/* Hero */}
      <section style={{
        position: 'relative', zIndex: 10, textAlign: 'center',
        padding: '80px 20px 60px', maxWidth: 800, margin: '0 auto',
      }}>
        <div className="animate-fade-in" style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
          borderRadius: 100, padding: '6px 16px', marginBottom: 24, fontSize: 13,
          color: '#818cf8', fontWeight: 500,
        }}>
          <Sparkles size={14} /> Powered by Google Gemini AI — 100% Free
        </div>

        <h1 className="animate-fade-in stagger-1" style={{
          fontSize: 'clamp(36px, 6vw, 64px)', fontWeight: 800,
          lineHeight: 1.1, marginBottom: 20, opacity: 0,
        }}>
          Your <span className="gradient-text">AI Classroom</span>{' '}
          Assistant That Never Sleeps
        </h1>

        <p className="animate-fade-in stagger-2" style={{
          fontSize: 18, color: 'var(--text-secondary)',
          maxWidth: 600, margin: '0 auto 40px', lineHeight: 1.7, opacity: 0,
        }}>
          Connect your Google Classroom. Let AI classify, solve, and submit your digital assignments automatically — while you focus on what matters.
        </p>

        <div className="animate-fade-in stagger-3" style={{
          display: 'flex', gap: 16, justifyContent: 'center',
          flexWrap: 'wrap', opacity: 0,
        }}>
          <button className="btn-primary" onClick={() => navigate('/login')}
            style={{ padding: '14px 32px', fontSize: 16 }}>
            <GraduationCap size={20} /> Connect Google Classroom
          </button>
          <button className="btn-secondary" onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
            style={{ padding: '14px 32px', fontSize: 16 }}>
            Learn More
          </button>
        </div>

        {/* Stats */}
        <div className="animate-fade-in stagger-4" style={{
          display: 'flex', justifyContent: 'center', gap: 40, marginTop: 60, opacity: 0,
          flexWrap: 'wrap',
        }}>
          {[
            { value: '100%', label: 'Free to Use' },
            { value: '7+', label: 'File Formats' },
            { value: '24/7', label: 'Auto Monitoring' },
            { value: '0', label: 'Cost Forever' },
          ].map((stat, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 28, fontWeight: 800 }} className="gradient-text">{stat.value}</div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" style={{
        position: 'relative', zIndex: 10,
        padding: '60px 20px 100px', maxWidth: 1100, margin: '0 auto',
      }}>
        <h2 style={{ textAlign: 'center', fontSize: 32, fontWeight: 700, marginBottom: 12 }}>
          Everything You Need, <span className="gradient-text">Automated</span>
        </h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: 48, fontSize: 16 }}>
          From detection to submission — fully automated pipeline.
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 20,
        }}>
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <div key={i} className="glass-card animate-fade-in" style={{
                padding: 28, opacity: 0, animationDelay: `${i * 0.1}s`,
              }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12,
                  background: `${f.color}15`, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', marginBottom: 16,
                }}>
                  <Icon size={22} color={f.color} />
                </div>
                <h3 style={{ fontSize: 17, fontWeight: 600, marginBottom: 8 }}>{f.title}</h3>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{f.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        position: 'relative', zIndex: 10,
        textAlign: 'center', padding: '30px 20px',
        borderTop: '1px solid rgba(255,255,255,0.05)',
        color: 'var(--text-muted)', fontSize: 13,
      }}>
        Built with ❤️ using React, Flask, and Google Gemini AI — 100% Free & Open Source
      </footer>
    </div>
  );
}
