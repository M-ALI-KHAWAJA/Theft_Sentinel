import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useRecoilValue } from 'recoil';
import { authUserState } from '../../store/authStore';
import { approveQuery, createQuery, deleteQuery, listMyQueries } from '../../api/queries';

const statusLabel = (s) => {
  if (s === 'PENDING_ADMIN_APPROVAL') return 'Awaiting branch admin';
  if (s === 'PENDING_SUPERADMIN') return 'Awaiting platform';
  if (s === 'ANSWERED') return 'Answered';
  return s || '—';
};

const statusClass = (s) => {
  if (s === 'ANSWERED') return 'text-emerald-400 text-xs font-medium';
  if (s === 'PENDING_SUPERADMIN') return 'text-sky-400 text-xs font-medium';
  return 'text-amber-400 text-xs font-medium';
};

const BranchQueries = () => {
  const user = useRecoilValue(authUserState);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await listMyQueries();
      const list = data?.results ?? data;
      setRows(Array.isArray(list) ? list : []);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load queries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const m = message.trim();
    if (m.length < 5) {
      toast.error('Please describe your issue (at least 5 characters).');
      return;
    }
    setSubmitting(true);
    try {
      await createQuery(m);
      toast.success('Query submitted');
      setMessage('');
      await load();
    } catch (e) {
      toast.error(e.response?.data?.message || e.response?.data?.error || 'Submit failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      await approveQuery(id);
      toast.success('Query forwarded to platform');
      await load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Approve failed');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this answered query?')) return;
    try {
      await deleteQuery(id);
      toast.success('Deleted');
      await load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Delete failed');
    }
  };

  const isAdmin = user?.role === 'ADMIN';

  return (
    <div>
      <h1 className="text-2xl font-bold text-dark-text-primary mb-2">Platform support</h1>
      <p className="text-dark-text-muted text-sm mb-6">
        Send a message to the platform operator. Guards and Incharge requests are reviewed by your branch admin
        before they reach the platform.
      </p>

      <form onSubmit={handleSubmit} className="glass-strong rounded-xl border border-dark-border p-4 mb-8 max-w-2xl">
        <label className="block text-sm text-dark-text-secondary mb-2">New message</label>
        <textarea
          required
          minLength={5}
          rows={4}
          className="w-full px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-dark-text-primary mb-3"
          placeholder="Describe your issue…"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-ai-blue to-ai-purple text-dark-bg font-medium disabled:opacity-50"
        >
          {submitting ? 'Sending…' : 'Submit query'}
        </button>
      </form>

      <h2 className="text-lg font-semibold text-dark-text-primary mb-3">Your queries</h2>
      {loading ? (
        <p className="text-dark-text-muted">Loading…</p>
      ) : (
        <div className="space-y-3">
          {rows.map((q) => (
            <div key={q.id} className="glass-strong rounded-xl border border-dark-border p-4">
              <div className="flex justify-between items-start gap-4 flex-wrap">
                <span className={statusClass(q.status)}>{statusLabel(q.status)}</span>
                <div className="flex items-center gap-2 flex-wrap">
                  {q.created_at ? (
                    <span className="text-xs text-dark-text-muted">
                      {new Date(q.created_at).toLocaleString()}
                    </span>
                  ) : null}
                  {isAdmin && q.status === 'PENDING_ADMIN_APPROVAL' && (
                    <button
                      type="button"
                      onClick={() => handleApprove(q.id)}
                      className="px-3 py-1 rounded-lg bg-emerald-600/20 text-emerald-400 text-xs hover:bg-emerald-600/30"
                    >
                      Approve & forward
                    </button>
                  )}
                  {q.status === 'ANSWERED' && (
                    <button
                      type="button"
                      onClick={() => handleDelete(q.id)}
                      className="px-3 py-1 rounded-lg bg-red-600/20 text-red-400 text-xs hover:bg-red-600/30"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
              {q.created_by_username ? (
                <p className="text-xs text-dark-text-muted mt-1">From: {q.created_by_username}</p>
              ) : null}
              <p className="text-dark-text-primary text-sm mt-2 whitespace-pre-wrap">{q.message}</p>
              {q.response ? (
                <div className="mt-3 pt-3 border-t border-dark-border">
                  <p className="text-xs text-dark-text-muted uppercase mb-1">Response</p>
                  <p className="text-dark-text-secondary text-sm whitespace-pre-wrap">{q.response}</p>
                </div>
              ) : null}
            </div>
          ))}
          {!rows.length && <p className="text-dark-text-muted text-sm">No queries yet.</p>}
        </div>
      )}
    </div>
  );
};

export default BranchQueries;
