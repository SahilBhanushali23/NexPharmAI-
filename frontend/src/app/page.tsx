'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { SystemHealth } from '@/types';

export default function HomePage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function checkHealth() {
      try {
        setLoading(true);
        const data = await api.getHealth();
        setHealth(data);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Unable to connect to backend service.');
      } finally {
        setLoading(false);
      }
    }

    checkHealth();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ marginBottom: '0.5rem' }}>Pharmaceutical Smart Manufacturing Platform</h1>
        <p style={{ fontSize: '1.05rem', maxWidth: '850px' }}>
          NexPharmAI unifies machine IoT telemetry, predictive failure classification, unsupervised anomaly detection,
          OR-Tools constraint-based production scheduling, automatic dynamic rescheduling, and raw material inventory gating.
        </p>
      </div>

      <div className="grid-metrics">
        <div className="metric-card">
          <div className="metric-title">Architecture Setup</div>
          <div className="metric-value" style={{ color: 'var(--primary)' }}>Phase 1</div>
          <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>Monorepo Scaffolding & Config</p>
        </div>

        <div className="metric-card">
          <div className="metric-title">Backend API Core</div>
          <div className="metric-value" style={{ color: health?.status === 'online' ? 'var(--status-running)' : 'var(--status-warning)' }}>
            {loading ? 'Checking...' : health?.status === 'online' ? 'Online' : 'Offline / Standby'}
          </div>
          <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>
            {health ? `FastAPI ${health.version} (${health.environment})` : 'Target: localhost:8000'}
          </p>
        </div>

        <div className="metric-card">
          <div className="metric-title">Authentic Training Dataset</div>
          <div className="metric-value" style={{ color: 'var(--status-running)' }}>10,000</div>
          <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>AI4I 2020 Predictive Maint. Records</p>
        </div>

        <div className="metric-card">
          <div className="metric-title">Next-Gen Scheduler</div>
          <div className="metric-value" style={{ color: 'var(--secondary)' }}>OR-Tools</div>
          <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>CP-SAT Constraint Optimizer</p>
        </div>
      </div>

      {/* Quick Launchpad to Modules */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <div>
            <div className="card-title">Plant Operations Module Launchpad</div>
            <div className="card-subtitle">Quick access to full-stack manufacturing services</div>
          </div>
          <Link href="/dashboard" className="btn btn-primary btn-sm" style={{ textDecoration: 'none' }}>
            Open Dashboard →
          </Link>
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem' }}>
            {[
              { title: 'Executive Dashboard', href: '/dashboard', desc: 'Plant OEE & Telemetry Overview' },
              { title: 'Machine Fleet & IoT', href: '/machines', desc: 'Health Scores & Failure Predictions' },
              { title: 'AI Production Scheduler', href: '/scheduler', desc: 'Google OR-Tools CP-SAT & Rescheduling' },
              { title: 'Orders & Batches', href: '/production', desc: 'cGMP BMR & Production Orders' },
              { title: 'Raw Material Inventory', href: '/inventory', desc: 'Stock Ledger & Shortage Gating' },
              { title: 'Maintenance & CMMS', href: '/maintenance', desc: 'Predictive & Preventive Work Orders' },
              { title: 'Alert Center', href: '/alerts', desc: 'Telemetry & Critical Notifications' },
              { title: 'Batch Quality Prediction', href: '/quality', desc: 'CQA Dissolution & Release Model' },
              { title: 'Demand Forecasting', href: '/forecasting', desc: '7d/30d/90d S&OP Projections' },
              { title: 'OEE Factory Analytics', href: '/analytics', desc: 'Six Big Losses & Efficiency Breakdown' },
              { title: 'AI Decision Assistant', href: '/assistant', desc: 'RAG Conversational Factory Co-Pilot' },
              { title: 'Access Control (Login)', href: '/login', desc: '21 CFR Part 11 RBAC Portals' },
            ].map((m) => (
              <Link
                key={m.href}
                href={m.href}
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  textDecoration: 'none',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.25rem',
                  transition: 'border-color 0.2s',
                }}
              >
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>{m.title}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.desc}</div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: 'var(--primary)' }}>●</span> Core System Workflow Progression
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
          {[
            'Demand Forecasting',
            'Production Planning',
            'Inventory Verification',
            'Machine Availability',
            'Machine Health',
            'Predictive Maintenance',
            'Anomaly Detection',
            'Production Scheduling',
            'Batch Execution',
            'Quality Prediction',
            'OEE Analytics',
            'Automatic Rescheduling',
          ].map((step, idx, arr) => (
            <div key={step} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className="badge" style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', padding: '0.4rem 0.8rem' }}>
                <strong style={{ color: 'var(--primary)', marginRight: '0.3rem' }}>{idx + 1}.</strong> {step}
              </span>
              {idx < arr.length - 1 && <span style={{ color: 'var(--text-muted)' }}>→</span>}
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Backend Connection Health Probe</h3>
        {loading ? (
          <p>Connecting to backend API at <code>http://localhost:8000/api/v1/health</code>...</p>
        ) : error ? (
          <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-md)' }}>
            <div style={{ fontWeight: 600, color: 'var(--status-critical)', marginBottom: '0.25rem' }}>Backend Connection Notice</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {error} — Start the FastAPI backend server using: <code>uvicorn app.main:app --port 8000</code> inside the <code>backend/</code> folder.
            </div>
          </div>
        ) : (
          <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-md)' }}>
            <div style={{ fontWeight: 600, color: 'var(--status-running)', marginBottom: '0.25rem' }}>Backend Successfully Connected!</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
              Status: {health?.status} | Service: {health?.service} | Version: {health?.version} | Time: {health?.timestamp}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
