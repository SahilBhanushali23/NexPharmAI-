'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import {
  BarChart3,
  Gauge,
  Activity,
  Layers,
  CheckCircle,
  Clock,
  TrendingUp,
  RefreshCw
} from 'lucide-react';

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [machines, setMachines] = useState<any[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState('');
  const [machineOee, setMachineOee] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  useEffect(() => {
    if (selectedMachineId) {
      loadMachineOee(selectedMachineId);
    }
  }, [selectedMachineId]);

  async function loadAnalytics() {
    setLoading(true);
    try {
      const [sumRes, machRes] = await Promise.allSettled([
        api.getDashboardSummary(),
        api.getMachines(),
      ]);

      if (sumRes.status === 'fulfilled') setSummary(sumRes.value);
      if (machRes.status === 'fulfilled') {
        const mList = machRes.value || [];
        setMachines(mList);
        if (mList.length > 0 && !selectedMachineId) {
          setSelectedMachineId(mList[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  }

  async function loadMachineOee(id: string) {
    try {
      const data = await api.getMachineOEE(id);
      setMachineOee(data);
    } catch (err) {
      console.error('Failed to load machine OEE:', err);
    }
  }

  const oee = summary?.oee_metrics || {
    availability: 0.92,
    performance: 0.94,
    quality_rate: 0.98,
    overall_oee: 0.85,
  };

  const selectedOee = machineOee || {
    availability: 0.94,
    performance: 0.92,
    quality_rate: 0.99,
    oee: 0.856,
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">OEE & Factory Analytics</h1>
          <p className="page-description">
            Overall Equipment Effectiveness (OEE), Six Big Losses breakdown, machine availability, throughput efficiency, and cGMP quality yields.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={loadAnalytics}
            className="btn btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <RefreshCw size={16} /> Refresh Analytics
          </button>
        </div>
      </div>

      {/* Global Plant OEE Breakdown */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <div>
            <div className="card-title">Plant-Wide Overall Equipment Effectiveness</div>
            <div className="card-subtitle">Aggregated across all production lines and active manufacturing shifts</div>
          </div>
          <span className="badge badge-running">Target: &gt;85%</span>
        </div>
        <div className="card-body">
          <div className="grid-4" style={{ marginBottom: '1rem' }}>
            <div className="metric-card">
              <div className="metric-label">Plant Total OEE</div>
              <div className="metric-value" style={{ color: 'var(--primary)', fontSize: '2.2rem' }}>
                {(oee.overall_oee * 100).toFixed(1)}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Availability Factor</div>
              <div className="metric-value" style={{ color: 'var(--status-running)', fontSize: '2.2rem' }}>
                {(oee.availability * 100).toFixed(1)}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Performance Factor</div>
              <div className="metric-value" style={{ color: 'var(--secondary)', fontSize: '2.2rem' }}>
                {(oee.performance * 100).toFixed(1)}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Quality Rate Factor</div>
              <div className="metric-value" style={{ color: 'var(--status-running)', fontSize: '2.2rem' }}>
                {(oee.quality_rate * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Machine-Specific OEE Deep Dive */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Machine-Level OEE Deep Dive</div>
              <div className="card-subtitle">Select equipment to view detailed factor breakdown</div>
            </div>
            <Gauge size={18} style={{ color: 'var(--primary)' }} />
          </div>
          <div className="card-body">
            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                Choose Machine
              </label>
              <select
                value={selectedMachineId}
                onChange={(e) => setSelectedMachineId(e.target.value)}
                className="input-field"
              >
                {machines.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.machine_code} — {m.name}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Availability Rate</span>
                  <span style={{ fontWeight: 600 }}>{(selectedOee.availability * 100).toFixed(1)}%</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${Math.min(100, selectedOee.availability * 100)}%`, background: 'var(--primary)' }}></div>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Performance Speed</span>
                  <span style={{ fontWeight: 600 }}>{(selectedOee.performance * 100).toFixed(1)}%</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${Math.min(100, selectedOee.performance * 100)}%`, background: 'var(--secondary)' }}></div>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Quality First-Pass Yield</span>
                  <span style={{ fontWeight: 600 }}>{(selectedOee.quality_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${Math.min(100, selectedOee.quality_rate * 100)}%`, background: 'var(--status-running)' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Six Big Losses Analysis */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Six Big Losses Categorization</div>
              <div className="card-subtitle">TPM (Total Productive Maintenance) root cause tracking</div>
            </div>
            <span className="badge badge-running">Loss Audit</span>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--status-critical)' }}>1. Equipment Failures / Breakdowns</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Mitigated by: AI4I 2020 LightGBM predictive alerts before catastrophic downtime.</div>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--status-warning)' }}>2. Setup & Adjustments / Changeovers</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Mitigated by: Google OR-Tools CP-SAT batch sequence optimization.</div>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--primary)' }}>3. Idling & Minor Stops</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Mitigated by: Real-time telemetry ingestion and anomaly isolation.</div>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--secondary)' }}>4. Reduced Speed & Micro-Stoppages</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Mitigated by: Continuous RPM and Torque threshold monitoring.</div>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--status-running)' }}>5. Production Rejects & Scrap</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Mitigated by: In-flight CQA quality prediction model.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
