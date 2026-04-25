import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import {
  listTenants,
  approveTenant,
  rejectTenant,
  suspendTenant,
  reapproveTenant,
  deleteTenantBranch,
} from '../../api/tenants';

const SuperAdminTenants = () => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await listTenants();
      const list = data?.results ?? data;
      setRows(Array.isArray(list) ? list : []);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load branches');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const act = async (id, fn, okMsg) => {
    try {
      await fn(id);
      toast.success(okMsg);
      await load();
    } catch (e) {
      toast.error(e.response?.data?.error || e.response?.data?.detail || 'Action failed');
    }
  };

  const confirmDelete = async (id) => {
    if (!window.confirm('Permanently delete this branch and all its users?')) return;
    try {
      await deleteTenantBranch(id);
      toast.success('Branch deleted');
      await load();
    } catch (e) {
      toast.error(e.response?.data?.error || e.response?.data?.detail || 'Delete failed');
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-dark-text-primary mb-2">Branches</h1>
      <p className="text-dark-text-muted text-sm mb-6">Approve or reject branch registrations.</p>
      {loading ? (
        <p className="text-dark-text-muted">Loading…</p>
      ) : (
        <div className="overflow-x-auto glass-strong rounded-xl border border-dark-border">
          <table className="min-w-full text-sm text-left">
            <thead>
              <tr className="border-b border-dark-border text-dark-text-muted">
                <th className="p-3">Name</th>
                <th className="p-3">Email</th>
                <th className="p-3">CNIC</th>
                <th className="p-3">Status</th>
                <th className="p-3">Registered</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => (
                <tr key={t.id} className="border-b border-dark-border/60">
                  <td className="p-3 text-dark-text-primary">{t.name}</td>
                  <td className="p-3 text-dark-text-secondary">{t.email}</td>
                  <td className="p-3 text-dark-text-secondary font-mono text-xs">{t.cnic}</td>
                  <td className="p-3">
                    <span
                      className={
                        t.status === 'APPROVED'
                          ? 'text-emerald-400'
                          : t.status === 'REJECTED'
                            ? 'text-red-400'
                            : t.status === 'SUSPENDED'
                              ? 'text-orange-400'
                              : 'text-amber-400'
                      }
                    >
                      {t.status}
                    </span>
                  </td>
                  <td className="p-3 text-dark-text-muted text-xs">
                    {t.created_at ? new Date(t.created_at).toLocaleString() : '—'}
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex flex-wrap justify-end gap-2">
                    {t.status === 'PENDING' && (
                      <>
                        <button
                          type="button"
                          className="px-3 py-1 rounded-lg bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30"
                          onClick={() => act(t.id, approveTenant, 'Branch approved')}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          className="px-3 py-1 rounded-lg bg-red-600/20 text-red-400 hover:bg-red-600/30"
                          onClick={() => act(t.id, rejectTenant, 'Branch rejected')}
                        >
                          Reject
                        </button>
                      </>
                    )}
                    {t.status === 'APPROVED' && (
                      <button
                        type="button"
                        className="px-3 py-1 rounded-lg bg-orange-600/20 text-orange-300 hover:bg-orange-600/30"
                        onClick={() => act(t.id, suspendTenant, 'Branch suspended')}
                      >
                        Suspend
                      </button>
                    )}
                    {t.status === 'SUSPENDED' && (
                      <button
                        type="button"
                        className="px-3 py-1 rounded-lg bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30"
                        onClick={() => act(t.id, reapproveTenant, 'Branch re-approved')}
                      >
                        Re-approve
                      </button>
                    )}
                    {(t.status === 'APPROVED' || t.status === 'SUSPENDED' || t.status === 'REJECTED') && (
                      <button
                        type="button"
                        className="px-3 py-1 rounded-lg bg-red-900/30 text-red-300 hover:bg-red-900/50"
                        onClick={() => confirmDelete(t.id)}
                      >
                        Delete
                      </button>
                    )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!rows.length && (
            <p className="p-6 text-dark-text-muted text-center">No branches yet.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default SuperAdminTenants;
