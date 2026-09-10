'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import {
  ShieldCheck,
  Lock,
  Mail,
  UserCheck,
  Sparkles,
  ArrowRight
} from 'lucide-react';

const PRESET_ACCOUNTS = [
  { role: 'Plant Admin', email: 'admin@nexpharm.ai', pass: 'admin123', desc: 'Full System Control' },
  { role: 'Production Mgr', email: 'prod@nexpharm.ai', pass: 'prod123', desc: 'Scheduling & Batches' },
  { role: 'Maintenance Mgr', email: 'maint@nexpharm.ai', pass: 'maint123', desc: 'IoT Fleet & Work Orders' },
  { role: 'Quality Mgr', email: 'qual@nexpharm.ai', pass: 'qual123', desc: 'CQA & cGMP Compliance' },
  { role: 'Operator', email: 'op@nexpharm.ai', pass: 'op123', desc: 'Shop Floor Ingestion' },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('admin@nexpharm.ai');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.login({ email, password });
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  }

  function handleSelectPreset(p: typeof PRESET_ACCOUNTS[0]) {
    setEmail(p.email);
    setPassword(p.pass);
  }

  return (
    <div style={{ maxWidth: '520px', margin: '3rem auto' }}>
      <div className="card" style={{ padding: '2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--primary-glow)',
              color: 'var(--primary)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              fontWeight: 800,
              fontSize: '1.25rem',
            }}
          >
            NP
          </div>
          <h2>NexPharmAI Access Portal</h2>
          <p style={{ fontSize: '0.85rem' }}>
            21 CFR Part 11 compliant role-based authentication and digital audit trail.
          </p>
        </div>

        {error && (
          <div
            style={{
              background: 'var(--status-critical-bg)',
              border: '1px solid var(--status-critical)',
              color: 'var(--status-critical)',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '1.25rem',
              fontSize: '0.85rem',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
              Corporate Email
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                style={{ paddingLeft: '36px' }}
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
              Security Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                style={{ paddingLeft: '36px' }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ marginTop: '0.5rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
          >
            <ShieldCheck size={16} />
            {loading ? 'Authenticating...' : 'Sign In to Operations OS'}
          </button>
        </form>

        {/* Demo Fast-Login Presets */}
        <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem', fontWeight: 600 }}>
            DEMO FAST-SELECT ROLES (Pre-seeded):
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {PRESET_ACCOUNTS.map((p) => (
              <button
                key={p.role}
                onClick={() => handleSelectPreset(p)}
                type="button"
                className="btn btn-outline"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.8rem',
                  background: 'var(--bg-tertiary)',
                }}
              >
                <span>
                  <strong style={{ color: 'var(--primary)' }}>{p.role}</strong> — {p.email}
                </span>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{p.desc}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
