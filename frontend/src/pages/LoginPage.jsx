/**
 * Login Page — Google OAuth login with futuristic design.
 */
import { GraduationCap, Shield, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const navigate = useNavigate();

  const handleGoogleLogin = () => {
    window.location.href = '/api/auth/google';
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-primary)',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Animated orbs */}
      <div style={{
        position: 'absolute', width: 400, height: 400, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)',
        top: '-10%', right: '-10%', animation: 'float 8s ease-in-out infinite',
      }} />
      <div style={{
        position: 'absolute', width: 300, height: 300, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.1) 0%, transparent 70%)',
        bottom: '-5%', left: '-5%', animation: 'float 6s ease-in-out infinite reverse',
      }} />

      {/* Back button */}
      <button onClick={() => navigate('/')} style={{
        position: 'absolute', top: 24, left: 24,
        background: 'none', border: 'none', color: 'var(--text-muted)',
        cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, fontSize: 14,
      }}>
        <ArrowLeft size={16} /> Back to Home
      </button>

      {/* Login card */}
      <div className="glass-card-static animate-fade-in" style={{
        width: '100%', maxWidth: 420, padding: 40,
        textAlign: 'center', position: 'relative', zIndex: 10,
      }}>
        {/* Logo */}
        <div style={{
          width: 64, height: 64, borderRadius: 16,
          background: 'var(--gradient-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 20px',
          boxShadow: '0 0 30px rgba(99,102,241,0.3)',
        }}>
          <GraduationCap size={32} color="white" />
        </div>

        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
          Welcome to <span className="gradient-text">EduAI</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 32 }}>
          Sign in with your Google Classroom account to get started
        </p>

        {/* Google Login Button */}
        <button
          onClick={handleGoogleLogin}
          style={{
            width: '100%', padding: '14px 24px',
            background: 'white', color: '#1f1f1f',
            border: 'none', borderRadius: 12,
            fontSize: 15, fontWeight: 600,
            cursor: 'pointer', display: 'flex',
            alignItems: 'center', justifyContent: 'center', gap: 12,
            transition: 'all 0.3s ease',
            boxShadow: '0 2px 12px rgba(0,0,0,0.2)',
          }}
          onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)'; }}
          onMouseOut={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,0,0,0.2)'; }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Sign in with Google
        </button>

        {/* Security note */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          marginTop: 24, padding: '12px 16px',
          background: 'rgba(16,185,129,0.08)',
          border: '1px solid rgba(16,185,129,0.15)',
          borderRadius: 10, fontSize: 12, color: '#34d399',
        }}>
          <Shield size={14} />
          <span>We never store your Google password. Only secure OAuth tokens.</span>
        </div>

        {/* Features preview */}
        <div style={{ marginTop: 32, textAlign: 'left' }}>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
            What you get:
          </p>
          {[
            'Auto-detect & classify assignments',
            'AI-generated solutions (PDF, DOCX, PPT, Code)',
            'Smart deadline reminders',
            'Automatic submission before deadline',
          ].map((text, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '6px 0', fontSize: 13, color: 'var(--text-secondary)',
            }}>
              <div style={{ width: 5, height: 5, borderRadius: '50%', background: '#6366f1', flexShrink: 0 }} />
              {text}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
