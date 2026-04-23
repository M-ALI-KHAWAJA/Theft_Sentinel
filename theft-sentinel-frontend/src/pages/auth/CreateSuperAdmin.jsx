import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CpuChipIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import CenteredModal from '../../components/CenteredModal';
import { useModal } from '../../hooks/useModal';
import { createSuperAdmin, getCreateSuperAdminStatus } from '../../api/auth';
import { validatePassword, PASSWORD_EXAMPLE } from '../../utils/validation';

const CNIC_RE = /^\d{5}-\d{7}-\d{1}$/;

/** Turn DRF { field: [msg], nested: { 0: {...} } } into readable text for modals. */
function flattenDrfErrors(data) {
  if (!data || typeof data !== 'object') return '';
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) return data.detail.join(' ');
  if (data.error && typeof data.error === 'string') return data.error;
  const lines = [];
  const walk = (obj, prefix) => {
    for (const [k, v] of Object.entries(obj)) {
      if (k === 'detail') continue;
      const path = prefix ? `${prefix}.${k}` : k;
      if (Array.isArray(v) && v.length && typeof v[0] === 'string') {
        lines.push(`${path}: ${v.join(' ')}`);
      } else if (v && typeof v === 'object' && !Array.isArray(v)) {
        walk(v, path);
      } else if (Array.isArray(v)) {
        v.forEach((item, i) => {
          if (typeof item === 'string') lines.push(`${path}[${i}]: ${item}`);
          else if (item && typeof item === 'object') walk(item, `${path}[${i}]`);
        });
      } else if (v !== undefined && v !== null && v !== '') {
        lines.push(`${path}: ${String(v)}`);
      }
    }
  };
  walk(data, '');
  return lines.join('\n').trim();
}

const emptyPartner = () => ({ partner_name: '', partner_cnic: '' });

const CreateSuperAdmin = () => {
  const navigate = useNavigate();
  const { modalState, showSuccess, showError, hideModal } = useModal();
  const [allowed, setAllowed] = useState(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
  });
  const [partners, setPartners] = useState([emptyPartner(), emptyPartner(), emptyPartner()]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await getCreateSuperAdminStatus();
        if (!cancelled) setAllowed(!!data?.can_create);
      } catch {
        if (!cancelled) setAllowed(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const updatePartner = (index, field, value) => {
    setPartners((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm_password) {
      showError('Passwords do not match.');
      return;
    }
    const pwdCheck = validatePassword(form.password);
    if (!pwdCheck.valid) {
      showError(pwdCheck.message);
      return;
    }
    const filled = partners
      .map((p) => ({
        partner_name: (p.partner_name || '').trim(),
        partner_cnic: (p.partner_cnic || '').trim(),
      }))
      .filter((p) => p.partner_name || p.partner_cnic);
    if (!filled.length) {
      showError('Add at least one partner with name and CNIC.');
      return;
    }
    if (filled.length > 3) {
      showError('A maximum of three partners is allowed.');
      return;
    }
    for (const p of filled) {
      if (!p.partner_name || !p.partner_cnic) {
        showError('Each partner must have both name and CNIC (format 12345-1234567-1).');
        return;
      }
      if (!CNIC_RE.test(p.partner_cnic)) {
        showError('Partner CNIC must match 12345-1234567-1 (digits and dashes only).');
        return;
      }
    }
    setLoading(true);
    try {
      const { data } = await createSuperAdmin({
        name: form.name.trim(),
        email: form.email.trim().toLowerCase(),
        phone: form.phone.trim(),
        password: form.password,
        partners: filled,
      });
      showSuccess(data.message || 'Super Admin created. You can sign in now.');
      setTimeout(() => navigate('/login', { replace: true }), 2000);
    } catch (err) {
      const d = err.response?.data;
      const flat = flattenDrfErrors(d);
      showError(flat || d?.error || d?.message || 'Could not create Super Admin.');
    } finally {
      setLoading(false);
    }
  };

  if (allowed === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-bg text-dark-text-muted">
        Loading…
      </div>
    );
  }

  if (!allowed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-bg px-4">
        <div className="glass-strong rounded-2xl p-8 max-w-md text-center border border-dark-border">
          <CpuChipIcon className="h-12 w-12 mx-auto text-ai-blue mb-4" />
          <h1 className="text-xl font-semibold text-dark-text-primary mb-2">Super Admin already exists</h1>
          <p className="text-sm text-dark-text-muted mb-6">This setup page is only available when no Super Admin is registered.</p>
          <button
            type="button"
            onClick={() => navigate('/login')}
            className="text-ai-blue hover:underline text-sm"
          >
            Go to login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg relative overflow-hidden px-4 py-12">
      <CenteredModal
        show={modalState.show}
        type={modalState.type}
        message={modalState.message}
        onClose={hideModal}
      />
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-ai-blue/20 rounded-full blur-3xl animate-pulse-slow" />
        <div
          className="absolute bottom-0 right-1/4 w-96 h-96 bg-ai-purple/20 rounded-full blur-3xl animate-pulse-slow"
          style={{ animationDelay: '1s' }}
        />
      </div>
      <div className="relative z-10 w-full max-w-lg">
        <div className="glass-strong rounded-2xl p-8 shadow-dark-lg border border-dark-border">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-ai-blue to-ai-purple mb-3">
              <CpuChipIcon className="h-8 w-8 text-dark-bg" />
            </div>
            <h1 className="text-2xl font-bold text-gradient-ai">Create Super Admin</h1>
            <p className="text-xs text-dark-text-muted mt-2">One-time setup. Up to three partners (CNIC format 12345-1234567-1).</p>
          </div>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs text-dark-text-secondary mb-1">Full name</label>
              <input
                required
                className="w-full px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-dark-text-primary"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs text-dark-text-secondary mb-1">Email</label>
              <input
                type="email"
                required
                className="w-full px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-dark-text-primary"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs text-dark-text-secondary mb-1">Phone</label>
              <input
                required
                className="w-full px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-dark-text-primary"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs text-dark-text-secondary mb-1">Password</label>
              <input
                type="password"
                required
                minLength={8}
                className="w-full px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-dark-text-primary"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
              <p className="mt-1 text-[11px] text-dark-text-muted">
                Same rules as branch signup: 8+ chars, upper, lower, number, special (e.g. {PASSWORD_EXAMPLE}).
              </p>
            </div>
            <div>
              <label className="block text-xs text-dark-text-secondary mb-1">Confirm password</label>
              <input
                type="password"
                required
                minLength={8}
                className="w-full px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-dark-text-primary"
                value={form.confirm_password}
                onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
              />
            </div>
            <div className="pt-2 border-t border-dark-border">
              <p className="text-xs text-dark-text-muted mb-3">Partners (fill rows you need; empty rows are ignored)</p>
              {partners.map((p, i) => (
                <div key={i} className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
                  <input
                    placeholder={`Partner ${i + 1} name`}
                    className="px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-sm text-dark-text-primary"
                    value={p.partner_name}
                    onChange={(e) => updatePartner(i, 'partner_name', e.target.value)}
                  />
                  <input
                    placeholder="CNIC 12345-1234567-1"
                    className="px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-sm text-dark-text-primary font-mono"
                    value={p.partner_cnic}
                    onChange={(e) => updatePartner(i, 'partner_cnic', e.target.value)}
                  />
                </div>
              ))}
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-gradient-to-r from-ai-blue to-ai-purple text-dark-bg font-semibold disabled:opacity-50"
            >
              {loading ? 'Creating…' : 'Create Super Admin'}
            </button>
          </form>
          <button
            type="button"
            onClick={() => navigate('/login')}
            className="mt-4 w-full flex items-center justify-center gap-2 text-sm text-dark-text-secondary hover:text-ai-blue"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to login
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateSuperAdmin;
