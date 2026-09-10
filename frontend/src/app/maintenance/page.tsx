'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import {
  Wrench,
  Plus,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertTriangle,
  FileText
} from 'lucide-react';

export default function MaintenancePage() {
  const [records, setRecords] = useState<any[]>([]);
  const [machines, setMachines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);

  // Form state
  const [machineId, setMachineId] = useState('');
  const [workOrderNumber, setWorkOrderNumber] = useState(`WO-${Date.now().toString().slice(-4)}`);
  const [maintenanceType, setMaintenanceType] = useState('PREDICTIVE');
  const [priority, setPriority] = useState('HIGH');
  const [description, setDescription] = useState('Preventive bearing inspection triggered by vibration anomaly.');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [mRes, recRes] = await Promise.allSettled([
        api.getMachines(),
        api.getMaintenanceRecords(),
      ]);

      if (mRes.status === 'fulfilled') {
        const mList = mRes.value || [];
        setMachines(mList);
        if (mList.length > 0 && !machineId) setMachineId(mList[0].id);
      }
      if (recRes.status === 'fulfilled') setRecords(recRes.value || []);
    } catch (err) {
      console.error('Failed to load maintenance records:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateRecord(e: React.FormEvent) {
    e.preventDefault();
    if (!machineId || !workOrderNumber) return;
    setCreating(true);
    try {
      await api.createMaintenance({
        machine_id: machineId,
        work_order_number: workOrderNumber,
        maintenance_type: maintenanceType,
        priority: priority,
        description: description,
        status: 'OPEN',
      });
      setShowModal(false);
      setWorkOrderNumber(`WO-${Date.now().toString().slice(-4)}`);
      await loadData();
    } catch (err: any) {
      alert(`Work order creation failed: ${err.message}`);
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdateStatus(id: string, newStatus: string) {
    try {
      await api.updateMaintenance(id, { status: newStatus });
      await loadData();
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    }
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Maintenance & Work Orders (CMMS)</h1>
          <p className="page-description">
            Computerized Maintenance Management System for scheduling, technician assignment, spare parts, and predictive work order triggers.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => setShowModal(true)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Plus size={16} /> Create Work Order
          </button>
          <button
            onClick={loadData}
            className="btn btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </div>

      {/* Work Orders List */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Active & Completed Work Orders</div>
            <div className="card-subtitle">Auto-generated predictive tickets and preventive maintenance logs</div>
          </div>
          <span className="badge badge-running">{records.length} Work Orders</span>
        </div>
        <div className="card-body">
          {records.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
              No maintenance work orders logged yet.
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Work Order #</th>
                  <th>Machine</th>
                  <th>Type</th>
                  <th>Priority</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td style={{ fontWeight: 600, color: 'var(--primary)' }}>{r.work_order_number}</td>
                    <td>{r.machine?.name || r.machine_id?.slice(0, 8)}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{r.maintenance_type}</td>
                    <td>
                      <span className={`badge ${r.priority === 'CRITICAL' || r.priority === 'HIGH' ? 'badge-critical' : 'badge-warning'}`} style={{ fontSize: '0.75rem' }}>
                        {r.priority}
                      </span>
                    </td>
                    <td style={{ maxWidth: '300px', fontSize: '0.85rem' }}>{r.description}</td>
                    <td>
                      <span className={`badge ${r.status === 'COMPLETED' ? 'badge-running' : r.status === 'IN_PROGRESS' ? 'badge-warning' : 'badge-idle'}`} style={{ fontSize: '0.75rem' }}>
                        {r.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {r.status === 'OPEN' && (
                          <button
                            onClick={() => handleUpdateStatus(r.id, 'IN_PROGRESS')}
                            className="btn btn-primary btn-sm"
                            style={{ fontSize: '0.72rem', padding: '0.25rem 0.5rem' }}
                          >
                            Start Work
                          </button>
                        )}
                        {r.status === 'IN_PROGRESS' && (
                          <button
                            onClick={() => handleUpdateStatus(r.id, 'COMPLETED')}
                            className="btn btn-outline btn-sm"
                            style={{ fontSize: '0.72rem', padding: '0.25rem 0.5rem', color: 'var(--status-running)', borderColor: 'var(--status-running)' }}
                          >
                            Close Ticket
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Create Work Order Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <div className="modal-title">Create Maintenance Work Order</div>
              <button onClick={() => setShowModal(false)} className="btn btn-outline btn-sm">✕</button>
            </div>
            <form onSubmit={handleCreateRecord}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Work Order # *
                  </label>
                  <input
                    type="text"
                    required
                    value={workOrderNumber}
                    onChange={(e) => setWorkOrderNumber(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Target Machine *
                  </label>
                  <select
                    value={machineId}
                    onChange={(e) => setMachineId(e.target.value)}
                    className="input-field"
                  >
                    {machines.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.machine_code} — {m.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Maintenance Type
                  </label>
                  <select
                    value={maintenanceType}
                    onChange={(e) => setMaintenanceType(e.target.value)}
                    className="input-field"
                  >
                    <option value="PREDICTIVE">Predictive (Triggered by ML Models)</option>
                    <option value="PREVENTIVE">Preventive (Routine Scheduled)</option>
                    <option value="CORRECTIVE">Corrective (Equipment Breakdown)</option>
                    <option value="CALIBRATION">cGMP Calibration Check</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Priority
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="input-field"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High Priority</option>
                    <option value="CRITICAL">Critical Emergency</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                    Issue Description & SOP Instructions
                  </label>
                  <textarea
                    rows={3}
                    required
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="input-field"
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-outline">
                  Cancel
                </button>
                <button type="submit" disabled={creating} className="btn btn-primary">
                  {creating ? 'Creating...' : 'Dispatch Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
