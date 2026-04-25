import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import {
  listPasswordResetRequests,
  approvePasswordResetRequest,
  rejectPasswordResetRequest,
  deletePasswordResetRequest,
} from '../../api/tenants';

const SuperAdminPasswordResetRequests = () => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await listPasswordResetRequests();
      const list = data?.results ?? data;
      setRows(Array.isArray(list) ? list : []);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load requests');
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

  const removeRequest = async (id) => {
    if (!window.confirm('Remove this request from the list?')) return;
    try {
      await deletePasswordResetRequest(id);
      toast.success('Request deleted');
      await load();
    } catch (e) {
      toast.error(e.response?.data?.error || e.response?.data?.detail || 'Delete failed');
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-dark-text-primary mb-2">Password reset requests</h1>
      <p className="text-dark-text-muted text-sm mb-6">
        Approve to email a reset link, or reject with a notice to the user.
      </p>
      {loading ? (
        <p className="text-dark-text-muted">Loading…</p>
      ) : (
        <div className="overflow-x-auto glass-strong rounded-xl border border-dark-border">
          <table className="min-w-full text-sm text-left">
            <thead>
              <tr className="border-b border-dark-border text-dark-text-muted">
                <th className="p-3">User</th>
                <th className="p-3">Reason</th>
                <th className="p-3">Status</th>
                <th className="p-3">Requested</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-dark-border/60 align-top">
                  <td className="p-3 text-dark-text-primary">
                    <div className="font-medium">{r.user_email}</div>
                    <div className="text-xs text-dark-text-muted font-mono">{r.user_id}</div>
                  </td>
                  <td className="p-3 text-dark-text-secondary max-w-md whitespace-pre-wrap">{r.reason}</td>
                  <td className="p-3">
                    <span
                      className={
                        r.status === 'APPROVED'
                          ? 'text-emerald-400'
                          : r.status === 'REJECTED'
                            ? 'text-red-400'
                            : 'text-amber-400'
                      }
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="p-3 text-dark-text-muted text-xs whitespace-nowrap">
                    {r.created_at ? new Date(r.created_at).toLocaleString() : '—'}
                  </td>
                  <td className="p-3 text-right space-x-2 whitespace-nowrap">
                    {r.status === 'PENDING' && (
                      <>
                        <button
                          type="button"
                          className="px-3 py-1 rounded-lg bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30"
                          onClick={() => act(r.id, approvePasswordResetRequest, 'Approved; email sent')}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          className="px-3 py-1 rounded-lg bg-red-600/20 text-red-400 hover:bg-red-600/30"
                          onClick={() => act(r.id, rejectPasswordResetRequest, 'Request rejected')}
                        >
                          Reject
                        </button>
                      </>
                    )}
                    {r.status !== 'PENDING' && (
                      <button
                        type="button"
                        className="px-3 py-1 rounded-lg bg-dark-card border border-dark-border text-dark-text-muted hover:text-status-error"
                        onClick={() => removeRequest(r.id)}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!rows.length && (
            <p className="p-6 text-dark-text-muted text-center">No password reset requests yet.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default SuperAdminPasswordResetRequests;
