import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { listSuperAdminQueries } from '../../api/tenants';
import { answerQuery } from '../../api/queries';

const Queries = () => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [answerId, setAnswerId] = useState(null);
  const [answerText, setAnswerText] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await listSuperAdminQueries();
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

  const submitAnswer = async (id) => {
    if (!answerText.trim()) {
      toast.error('Enter a response');
      return;
    }
    try {
      await answerQuery(id, answerText.trim());
      toast.success('Query answered');
      setAnswerId(null);
      setAnswerText('');
      await load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed to answer');
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-dark-text-primary mb-2">Tenant queries</h1>
      <p className="text-dark-text-muted text-sm mb-6">
        Queries appear here after branch admin approval. Answer to close the request.
      </p>
      {loading ? (
        <p className="text-dark-text-muted">Loading…</p>
      ) : (
        <div className="overflow-x-auto glass-strong rounded-xl border border-dark-border">
          <table className="min-w-full text-sm text-left">
            <thead>
              <tr className="border-b border-dark-border text-dark-text-muted">
                <th className="p-3">Branch</th>
                <th className="p-3">Email</th>
                <th className="p-3">Submitted by</th>
                <th className="p-3">Message</th>
                <th className="p-3">Response</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((q) => (
                <tr key={q.id} className="border-b border-dark-border/60 align-top">
                  <td className="p-3 text-dark-text-primary">{q.tenant_name}</td>
                  <td className="p-3 text-dark-text-secondary text-xs">{q.tenant_email}</td>
                  <td className="p-3 text-dark-text-secondary text-xs">{q.created_by_username || '—'}</td>
                  <td className="p-3 text-dark-text-secondary max-w-xs whitespace-pre-wrap">{q.message}</td>
                  <td className="p-3 text-dark-text-muted text-xs max-w-xs whitespace-pre-wrap">{q.response || '—'}</td>
                  <td className="p-3">
                    <span className={q.status === 'ANSWERED' ? 'text-emerald-400' : 'text-amber-400'}>
                      {q.status === 'PENDING_SUPERADMIN' ? 'PENDING (platform)' : q.status}
                    </span>
                  </td>
                  <td className="p-3 text-right space-y-2">
                    {q.status === 'PENDING_SUPERADMIN' && (
                      <>
                        {answerId === q.id ? (
                          <div className="flex flex-col gap-2 items-end">
                            <textarea
                              className="w-56 px-2 py-1 rounded bg-dark-card border border-dark-border text-xs text-dark-text-primary"
                              rows={3}
                              value={answerText}
                              onChange={(e) => setAnswerText(e.target.value)}
                              placeholder="Response…"
                            />
                            <div className="space-x-2">
                              <button
                                type="button"
                                className="px-2 py-1 rounded bg-emerald-600/20 text-emerald-400 text-xs"
                                onClick={() => submitAnswer(q.id)}
                              >
                                Send
                              </button>
                              <button
                                type="button"
                                className="px-2 py-1 rounded text-dark-text-muted text-xs"
                                onClick={() => {
                                  setAnswerId(null);
                                  setAnswerText('');
                                }}
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            type="button"
                            className="px-3 py-1 rounded-lg bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30"
                            onClick={() => {
                              setAnswerId(q.id);
                              setAnswerText('');
                            }}
                          >
                            Answer
                          </button>
                        )}
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!rows.length && (
            <p className="p-6 text-dark-text-muted text-center">No queries yet.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Queries;
