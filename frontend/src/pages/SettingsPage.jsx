/**
 * Settings Page — user preferences for automation behavior.
 */
import { useEffect, useState } from 'react';
import { Settings, Zap, Shield, Bell, SlidersHorizontal, Globe, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import useSettingsStore from '@/stores/settingsStore';
import { assignmentsAPI } from '@/lib/api';

function Toggle({ checked, onChange, label, description }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '14px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
    }}>
      <div>
        <div style={{ fontSize: 14, fontWeight: 500 }}>{label}</div>
        {description && <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{description}</div>}
      </div>
      <label className="toggle">
        <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
        <span className="toggle-slider" />
      </label>
    </div>
  );
}

export default function SettingsPage() {
  const { settings, fetchSettings, updateSettings } = useSettingsStore();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [setupLoading, setSetupLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [setupMode, setSetupMode] = useState('automatic');
  const [cookieJson, setCookieJson] = useState('');
  const [importLoading, setImportLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);

  const checkSessionStatus = async () => {
    try {
      const response = await assignmentsAPI.getBrowserSessionStatus();
      setIsLoggedIn(response.data.logged_in);
    } catch (err) {
      console.error("Failed to fetch browser session status:", err);
    } finally {
      setSessionLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
    checkSessionStatus();
  }, []);

  const handleSetupLogin = async () => {
    setSetupLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const response = await assignmentsAPI.setupBrowserLogin();
      if (response.data.success || response.data.launched) {
        // Browser launched in background — now poll for session to appear
        setSuccessMsg("Browser window opened! Log in to Google Classroom, then close the window. We'll detect it automatically.");
        pollForSession();
      } else {
        setSetupLoading(false);
        setErrorMsg(response.data.error || "Could not launch login browser.");
      }
    } catch (err) {
      setSetupLoading(false);
      setErrorMsg(err.response?.data?.error || "Failed to trigger login browser.");
    }
  };

  const pollForSession = () => {
    let attempts = 0;
    const maxAttempts = 120; // poll for up to ~6 minutes (120 × 3s)
    const interval = setInterval(async () => {
      attempts++;
      try {
        const res = await assignmentsAPI.getBrowserSessionStatus();
        if (res.data.logged_in) {
          clearInterval(interval);
          setIsLoggedIn(true);
          setSetupLoading(false);
          setSuccessMsg("✅ Browser session successfully saved! Submissions are now authorized.");
        }
      } catch (e) {
        // ignore polling errors
      }
      if (attempts >= maxAttempts) {
        clearInterval(interval);
        setSetupLoading(false);
        setErrorMsg("Polling timed out. If you already logged in, refresh this page to check.");
      }
    }, 3000);
  };

  const handleImportCookies = async () => {
    setImportLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      let parsed;
      try {
        parsed = JSON.parse(cookieJson.trim());
      } catch (e) {
        throw new Error("Invalid JSON format. Please make sure you copied the entire cookie JSON.");
      }

      if (!Array.isArray(parsed)) {
        throw new Error("Pasted content must be a JSON array of cookies.");
      }

      const response = await assignmentsAPI.importCookies(parsed);
      if (response.data.success) {
        setSuccessMsg("Cookies successfully imported and authenticated!");
        setIsLoggedIn(true);
        setCookieJson('');
      } else {
        setErrorMsg(response.data.error || "Failed to import cookies.");
      }
    } catch (err) {
      setErrorMsg(err.message || err.response?.data?.error || "An error occurred during cookie import.");
    } finally {
      setImportLoading(false);
      checkSessionStatus();
    }
  };

  const update = (key, value) => {
    updateSettings({ [key]: value });
  };

  const updateNested = (parent, key, value) => {
    updateSettings({ [parent]: { ...settings[parent], [key]: value } });
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: 700 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Settings size={24} color="#818cf8" /> Settings
      </h1>

      {/* Automation Settings */}
      <div className="glass-card-static" style={{ padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Zap size={18} color="#22d3ee" /> Automation
        </h3>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>Control how the AI handles your assignments.</p>

        <Toggle
          checked={settings.auto_submit}
          onChange={(v) => update('auto_submit', v)}
          label="Auto-Submit"
          description="Automatically submit AI-generated assignments when confidence is above threshold."
        />

        <Toggle
          checked={settings.approval_mode}
          onChange={(v) => update('approval_mode', v)}
          label="Approval Mode"
          description="Require your manual approval before any submission — even high confidence ones."
        />

        {/* Confidence Threshold */}
        <div style={{ padding: '16px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>Confidence Threshold</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Assignments below this score will require your review.
              </div>
            </div>
            <span style={{
              fontSize: 18, fontWeight: 700, color: '#818cf8',
              background: 'rgba(99,102,241,0.1)', padding: '4px 12px', borderRadius: 8,
            }}>
              {settings.confidence_threshold}%
            </span>
          </div>
          <input
            type="range" min="0" max="100" step="5"
            value={settings.confidence_threshold}
            onChange={(e) => update('confidence_threshold', parseInt(e.target.value))}
            style={{
              width: '100%', accentColor: '#6366f1', height: 6,
              background: 'rgba(255,255,255,0.1)', borderRadius: 3, cursor: 'pointer',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            <span>0% (submit everything)</span>
            <span>100% (always review)</span>
          </div>
        </div>

        {/* Reminder Frequency */}
        <div style={{ padding: '16px 0' }}>
          <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>Reminder Frequency</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
            How often to remind you about upcoming deadlines.
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {['minimal', 'standard', 'aggressive'].map((freq) => (
              <button key={freq}
                className={settings.reminder_frequency === freq ? 'btn-primary' : 'btn-secondary'}
                onClick={() => update('reminder_frequency', freq)}
                style={{ flex: 1, textTransform: 'capitalize', fontSize: 13, padding: '8px 16px' }}>
                {freq}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Browser Automation Settings */}
      <div className="glass-card-static" style={{ padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Globe size={18} color="#60a5fa" /> Browser Automation
        </h3>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
          Google Classroom session setup. A valid session is required to automatically upload and submit assignments.
        </p>

        {sessionLoading ? (
          <div style={{ padding: '16px 0', textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
            Checking browser session status...
          </div>
        ) : (
          <>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '16px', borderRadius: 12, background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.05)', marginBottom: 16,
            }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 500 }}>Classroom Session</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  {isLoggedIn ? 'Active — headless submission authorized' : 'Inactive — submission requires initial manual setup'}
                </div>
              </div>
              <span style={{
                fontSize: 12, fontWeight: 600, borderRadius: 20, padding: '4px 10px',
                background: isLoggedIn ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                color: isLoggedIn ? '#34d399' : '#fbbf24',
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: isLoggedIn ? '#10b981' : '#f59e0b',
                }} />
                {isLoggedIn ? 'Active' : 'Setup Required'}
              </span>
            </div>

            {/* Mode Selector Tab */}
            <div style={{ display: 'flex', background: 'rgba(255,255,255,0.02)', padding: 4, borderRadius: 8, border: '1px solid rgba(255,255,255,0.04)', marginBottom: 16 }}>
              <button 
                onClick={() => { setSetupMode('automatic'); setErrorMsg(null); setSuccessMsg(null); }}
                style={{
                  flex: 1, padding: '8px 12px', borderRadius: 6, border: 'none', fontSize: 12, fontWeight: 500, cursor: 'pointer',
                  background: setupMode === 'automatic' ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: setupMode === 'automatic' ? '#818cf8' : 'var(--text-secondary)',
                  transition: 'all 0.2s ease',
                }}
              >
                Browser Setup (Headed)
              </button>
              <button 
                onClick={() => { setSetupMode('import'); setErrorMsg(null); setSuccessMsg(null); }}
                style={{
                  flex: 1, padding: '8px 12px', borderRadius: 6, border: 'none', fontSize: 12, fontWeight: 500, cursor: 'pointer',
                  background: setupMode === 'import' ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: setupMode === 'import' ? '#818cf8' : 'var(--text-secondary)',
                  transition: 'all 0.2s ease',
                }}
              >
                Instant Cookie Import (100% Reliable)
              </button>
            </div>

            {setupMode === 'automatic' ? (
              <>
                {errorMsg && (
                  <div style={{
                    background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)',
                    borderRadius: 8, padding: 12, fontSize: 13, color: '#f43f5e',
                    marginBottom: 16, display: 'flex', alignItems: 'flex-start', gap: 8
                  }}>
                    <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                    <div>{errorMsg}</div>
                  </div>
                )}

                {successMsg && (
                  <div style={{
                    background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)',
                    borderRadius: 8, padding: 12, fontSize: 13, color: '#34d399',
                    marginBottom: 16, display: 'flex', alignItems: 'flex-start', gap: 8
                  }}>
                    <CheckCircle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                    <div>{successMsg}</div>
                  </div>
                )}

                <button
                  className={setupLoading ? 'btn-secondary' : 'btn-primary'}
                  disabled={setupLoading}
                  onClick={handleSetupLogin}
                  style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8, padding: '12px' }}
                >
                  {setupLoading ? (
                    <>
                      <RefreshCw size={16} className="animate-spin-slow" style={{ animation: 'spin-slow 2s linear infinite' }} />
                      Browser launched — waiting for login... (Check your taskbar)
                    </>
                  ) : (
                    isLoggedIn ? 'Reconnect Google Classroom' : 'Setup Browser Login'
                  )}
                </button>

                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, textAlign: 'center' }}>
                  💡 Clicking this button launches a browser window. Simply log in to your Google Account there.
                </div>
              </>
            ) : (
              <>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 12 }}>
                  Google security sometimes blocks automated sign-ins. Use this option to securely import cookies from your normal browser:
                  <ol style={{ paddingLeft: 16, marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <li>1. Install the free <b>Cookie-Editor</b> extension in Chrome/Edge.</li>
                    <li>2. Open a new tab, go to <b>https://classroom.google.com</b>, and log in.</li>
                    <li>3. Click the Cookie-Editor extension icon, then click <b>Export</b> then <b>JSON</b>.</li>
                    <li>4. Paste the copied text inside the box below and click import.</li>
                  </ol>
                </div>

                <textarea
                  className="input-field"
                  placeholder='Paste cookie JSON here... (e.g. [{"domain": ".google.com", ...}])'
                  value={cookieJson}
                  onChange={(e) => setCookieJson(e.target.value)}
                  style={{ height: 100, fontFamily: 'monospace', fontSize: 11, resize: 'vertical', marginBottom: 12 }}
                />

                {errorMsg && (
                  <div style={{
                    background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)',
                    borderRadius: 8, padding: 12, fontSize: 13, color: '#f43f5e',
                    marginBottom: 12, display: 'flex', alignItems: 'flex-start', gap: 8
                  }}>
                    <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                    <div>{errorMsg}</div>
                  </div>
                )}

                {successMsg && (
                  <div style={{
                    background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)',
                    borderRadius: 8, padding: 12, fontSize: 13, color: '#34d399',
                    marginBottom: 12, display: 'flex', alignItems: 'flex-start', gap: 8
                  }}>
                    <CheckCircle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                    <div>{successMsg}</div>
                  </div>
                )}

                <button
                  className={importLoading ? 'btn-secondary' : 'btn-primary'}
                  disabled={importLoading || !cookieJson.trim()}
                  onClick={handleImportCookies}
                  style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8, padding: '12px' }}
                >
                  {importLoading ? 'Importing cookies...' : 'Import Session Cookies'}
                </button>
              </>
            )}
          </>
        )}
      </div>

      {/* Notification Settings */}
      <div className="glass-card-static" style={{ padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Bell size={18} color="#fbbf24" /> Notifications
        </h3>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>Choose where to receive alerts.</p>

        <Toggle
          checked={settings.notifications?.browser ?? true}
          onChange={(v) => updateNested('notifications', 'browser', v)}
          label="Browser Notifications"
          description="Show notifications in the dashboard."
        />
        <Toggle
          checked={settings.notifications?.email ?? false}
          onChange={(v) => updateNested('notifications', 'email', v)}
          label="Email Notifications"
          description="Send alerts to your Gmail address."
        />
        <Toggle
          checked={settings.notifications?.telegram ?? false}
          onChange={(v) => updateNested('notifications', 'telegram', v)}
          label="Telegram Notifications"
          description="Send alerts via Telegram bot (requires setup)."
        />
      </div>

      {/* Security Info */}
      <div className="glass-card-static" style={{ padding: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={18} color="#10b981" /> Security
        </h3>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>Your account security information.</p>

        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 2 }}>
          ✅ Google OAuth 2.0 — no passwords stored<br />
          ✅ Tokens encrypted at rest with Fernet<br />
          ✅ JWT session cookies (httpOnly)<br />
          ✅ No duplicate submissions<br />
          ✅ Max 3 retry attempts (no infinite loops)
        </div>
      </div>
    </div>
  );
}
