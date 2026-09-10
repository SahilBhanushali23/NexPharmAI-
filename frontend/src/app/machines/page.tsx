'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import {
  Cpu,
  Search,
  Filter,
  Plus,
  Activity,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  ExternalLink,
  ChevronRight
} from 'lucide-react';

export default function MachinesPage() {
  const [machines, setMachines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [showAddModal, setShowAddModal] = useState(false);
  const [creating, setCreating] = useState(false);

  // New machine form state
  const [newCode, setNewCode] = useState('');
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('TABLET_PRESS');
  const [newManufacturer, setNewManufacturer] = useState('PharmaTech Industries');
  const [newModelNumber, setNewModelNumber] = useState('PT-2026-X');

  useEffect(() => {
    fetchMachines();
  }, [statusFilter]);

  async function fetchMachines() {
    setLoading(true);
    try {
      const params: any = {};
      if (statusFilter !== 'ALL') params.status = statusFilter;
      const data = await api.getMachines(params);
      setMachines(data || []);
    } catch (err) {
      console.error('Error fetching machines:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateMachine(e: React.FormEvent) {
    e.preventDefault();
    if (!newCode || !newName) return;
    setCreating(true);
    try {
      await api.createMachine({
        machine_id: newCode.trim().toUpperCase(),
        machine_code: newCode.trim().toUpperCase(),
        machine_name: newName.trim(),
        name: newName.trim(),
        machine_type: newType,
        production_line: 'LINE-1',
        location: 'Cleanroom A',
        manufacturer: newManufacturer,
        model_number: newModelNumber,
        status: 'RUNNING',
      });
      setShowAddModal(false);
      setNewCode('');
      setNewName('');
      await fetchMachines();
      alert(`Machine ${newCode.toUpperCase()} registered successfully!`);
    } catch (err: any) {
      alert(`Error creating machine: ${err.message || err.detail || 'Check server connection'}`);
    } finally {
      setCreating(false);
    }
  }

  const filteredMachines = machines.filter((m) => {
    const nameStr = (m.name || m.machine_name || '').toLowerCase();
    const codeStr = (m.machine_code || m.machine_id || '').toLowerCase();
    const typeStr = (m.machine_type || '').toLowerCase();
    const s = search.toLowerCase();
    return nameStr.includes(s) || codeStr.includes(s) || typeStr.includes(s);
  });

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Machine Fleet & IoT Telemetry</h1>
          <p className="page-description">
            Live machine monitoring, AI health score assessment (0-100), predictive failure forecasting, and automated anomaly isolation.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Plus size={16} /> Add Equipment
          </button>
          <button
            onClick={fetchMachines}
            className="btn btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <RefreshCw size={16} /> Refresh Fleet
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-body" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search equipment by name, code, or model..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field"
              style={{ paddingLeft: '32px' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <Filter size={16} style={{ color: 'var(--text-muted)' }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Status:</span>
            {['ALL', 'RUNNING', 'WARNING', 'CRITICAL', 'MAINTENANCE'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`btn btn-sm ${statusFilter === status ? 'btn-primary' : 'btn-outline'}`}
                style={{ fontSize: '0.75rem' }}
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Machine Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-secondary)' }}>
          <RefreshCw size={28} className="spin" style={{ marginBottom: '0.75rem', color: 'var(--primary)' }} />
          <div>Connecting to IoT Telemetry Stream...</div>
        </div>
      ) : filteredMachines.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
          <Cpu size={36} style={{ marginBottom: '0.75rem', opacity: 0.5 }} />
          <div>No equipment found matching criteria.</div>
        </div>
      ) : (
        <div className="grid-3">
          {filteredMachines.map((m) => {
            const score = m.health_score ?? 85;
            const statusClass =
              m.status === 'RUNNING'
                ? 'badge-running'
                : m.status === 'WARNING'
                ? 'badge-warning'
                : m.status === 'CRITICAL'
                ? 'badge-critical'
                : 'badge-idle';

            const scoreColor =
              score >= 75 ? 'var(--status-running)' : score >= 50 ? 'var(--status-warning)' : 'var(--status-critical)';

            return (
              <div key={m.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div className="card-header" style={{ paddingBottom: '0.5rem' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 600, letterSpacing: '0.05em' }}>
                      {m.machine_code || m.machine_id}
                    </div>
                    <div className="card-title" style={{ fontSize: '1.1rem', marginTop: '0.15rem' }}>
                      {m.name || m.machine_name}
                    </div>
                  </div>
                  <span className={`badge ${statusClass}`}>{m.status}</span>
                </div>

                <div className="card-body" style={{ paddingTop: '0.5rem', flex: 1 }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    Type: <strong style={{ color: 'var(--text-primary)' }}>{m.machine_type}</strong> • Mfr: {m.manufacturer || 'OEM'}
                  </div>

                  {/* Health Bar */}
                  <div style={{ marginBottom: '1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>AI Health Index</span>
                      <span style={{ fontSize: '1.1rem', fontWeight: 800, color: scoreColor }}>
                        {score.toFixed(0)}<span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/100</span>
                      </span>
                    </div>
                    <div className="progress-bar" style={{ height: '8px' }}>
                      <div
                        className="progress-fill"
                        style={{ width: `${Math.min(100, Math.max(0, score))}%`, background: scoreColor }}
                      ></div>
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', padding: '0.65rem 0.85rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Total Runtime: </span>
                      <strong style={{ color: 'var(--text-primary)' }}>{m.total_operating_hours || 1420}h</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Line: </span>
                      <strong style={{ color: 'var(--text-primary)' }}>{m.production_line_id ? 'Line Assigned' : 'Unassigned'}</strong>
                    </div>
                  </div>
                </div>

                <div style={{ padding: '0.85rem 1.25rem', borderTop: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.1)' }}>
                  <Link
                    href={`/machines/${m.id}`}
                    className="btn btn-outline"
                    style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', textDecoration: 'none' }}
                  >
                    <span>Inspect Diagnostics & AI Models</span>
                    <ChevronRight size={15} />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Equipment Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <div className="modal-title">Register New Production Machine</div>
              <button onClick={() => setShowAddModal(false)} className="btn btn-outline btn-sm">✕</button>
            </div>
            <form onSubmit={handleCreateMachine}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Machine Code *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. M-107-TP"
                    value={newCode}
                    onChange={(e) => setNewCode(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Machine Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. High-Speed Rotary Tablet Press C"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Machine Type
                  </label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="input-field"
                  >
                    <option value="TABLET_PRESS">Tablet Press</option>
                    <option value="COATING_PAN">Coating Pan</option>
                    <option value="BLISTER_PACKER">Blister Packer</option>
                    <option value="FLUID_BED_DRYER">Fluid Bed Dryer</option>
                    <option value="BIOREACTOR">Bioreactor / Fermenter</option>
                    <option value="CAPSULE_FILLER">Capsule Filler</option>
                    <option value="AUTOCLAVE">Autoclave Sterilizer</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Manufacturer
                  </label>
                  <input
                    type="text"
                    value={newManufacturer}
                    onChange={(e) => setNewManufacturer(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Model Number
                  </label>
                  <input
                    type="text"
                    value={newModelNumber}
                    onChange={(e) => setNewModelNumber(e.target.value)}
                    className="input-field"
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-outline">
                  Cancel
                </button>
                <button type="submit" disabled={creating} className="btn btn-primary">
                  {creating ? 'Saving...' : 'Register Machine'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
