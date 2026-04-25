import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { getSuperAdminDashboard, listTenants } from '../../api/tenants';

const SuperAdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [tenants, setTenants] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [dashRes, tenantsRes] = await Promise.all([getSuperAdminDashboard(), listTenants()]);
        if (cancelled) return;
        setStats(dashRes.data);
        const list = tenantsRes.data?.results ?? tenantsRes.data;
        setTenants(Array.isArray(list) ? list : []);
      } catch (e) {
        if (!cancelled) setError(e.response?.data?.detail || 'Failed to load dashboard');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const approvedCount = tenants.filter((t) => t.status === 'APPROVED').length;
  const suspendedCount = tenants.filter((t) => t.status === 'SUSPENDED').length;
  const branchStatusChart = [
    { name: 'Approved', count: approvedCount },
    { name: 'Suspended', count: suspendedCount },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-dark-text-primary mb-2">Platform dashboard</h1>
      <p className="text-dark-text-muted text-sm mb-8">
        Manage branch registrations. Branch surveillance data is not shown here.
      </p>
      {error && <p className="text-status-error text-sm mb-4">{error}</p>}
      {stats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            {[
              ['Total branches', stats.tenants_total],
              ['Pending', stats.tenants_pending],
              ['Approved', stats.tenants_approved],
              ['Rejected', stats.tenants_rejected],
              ['Suspended', stats.tenants_suspended ?? 0],
              ['Total queries', stats.queries_total ?? 0],
            ].map(([label, value]) => (
              <div key={label} className="glass-strong rounded-xl p-4 border border-dark-border">
                <p className="text-xs text-dark-text-muted uppercase tracking-wide">{label}</p>
                <p className="text-2xl font-semibold text-ai-blue mt-1">{value}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
            <div className="glass-strong rounded-xl p-4 border border-dark-border">
              <h2 className="text-sm font-semibold text-dark-text-primary mb-4">Approved vs suspended branches</h2>
              <p className="text-xs text-dark-text-muted mb-2">Counts from the branch list below (same as tenant records).</p>
              <div className="h-64 w-full min-h-[240px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={branchStatusChart} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                    <YAxis allowDecimals={false} stroke="#94a3b8" fontSize={12} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                    <Legend />
                    <Bar dataKey="count" name="Branches" fill="#00d4ff" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="glass-strong rounded-xl border border-dark-border overflow-hidden">
            <h2 className="text-sm font-semibold text-dark-text-primary p-4 border-b border-dark-border">All branches</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-dark-border text-dark-text-muted">
                    <th className="p-3">Name</th>
                    <th className="p-3">Email</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {tenants.map((t) => (
                    <tr key={t.id} className="border-b border-dark-border/60">
                      <td className="p-3 text-dark-text-primary">{t.name}</td>
                      <td className="p-3 text-dark-text-secondary text-xs">{t.email}</td>
                      <td className="p-3">
                        <span
                          className={
                            t.status === 'APPROVED'
                              ? 'text-emerald-400'
                              : t.status === 'SUSPENDED'
                                ? 'text-amber-400'
                                : 'text-dark-text-muted'
                          }
                        >
                          {t.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!tenants.length && <p className="p-6 text-dark-text-muted text-center">No branches yet.</p>}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SuperAdminDashboard;
