import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSetRecoilState } from 'recoil';
import toast from 'react-hot-toast';
import {
  getSuperAdminProfile,
  patchSuperAdminProfile,
  superAdminRequestPasswordEmail,
  superAdminDeleteAccount,
} from '../../api/tenants';
import { authUserState, authTokensState } from '../../store/authStore';

const emptyPartner = () => ({ partner_name: '', partner_cnic: '' });

const Profile = () => {
  const navigate = useNavigate();
  const setAuthUser = useSetRecoilState(authUserState);
  const setAuthTokens = useSetRecoilState(authTokensState);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [partners, setPartners] = useState([emptyPartner(), emptyPartner(), emptyPartner()]);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await getSuperAdminProfile();
      setEmail(data.email || '');
      setName(data.name || '');
      setPhone(data.phone || '');
      const p = Array.isArray(data.partners) ? data.partners : [];
      const padded = [...p, emptyPartner(), emptyPartner(), emptyPartner()].slice(0, 3);
      setPartners(padded.map((x) => ({ partner_name: x.partner_name || '', partner_cnic: x.partner_cnic || '' })));
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const updatePartner = (i, field, value) => {
    setPartners((prev) => {
      const next = [...prev];
      next[i] = { ...next[i], [field]: value };
      return next;
    });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const filled = partners
      .map((p) => ({
        partner_name: (p.partner_name || '').trim(),
        partner_cnic: (p.partner_cnic || '').trim(),
      }))
      .filter((p) => p.partner_name || p.partner_cnic);
    for (const p of filled) {
      if (!p.partner_name || !p.partner_cnic) {
        toast.error('Each partner needs name and CNIC (12345-1234567-1).');
        return;
      }
    }
    setSaving(true);
    try {
      await patchSuperAdminProfile({ name, phone, partners: filled });
      toast.success('Profile updated');
      await load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleEmailReset = async () => {
    try {
      await superAdminRequestPasswordEmail();
      toast.success('Check your email for the reset link.');
    } catch (e) {
      toast.error(e.response?.data?.error || 'Could not send email');
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm('Delete your Super Admin account permanently? This cannot be undone.')) return;
    try {
      const { data } = await superAdminDeleteAccount();
      if (data?.clear_tokens) {
        localStorage.clear();
        setAuthUser(null);
        setAuthTokens({ access: null, refresh: null });
      }
      toast.success(data?.message || 'Account deleted');
      navigate('/', { replace: true });
    } catch (e) {
      toast.error(e.response?.data?.error || 'Could not delete account');
    }
  };

  if (loading) {
    return <p className="text-dark-text-muted">Loading…</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-dark-text-primary mb-2">Super Admin profile</h1>
      <p className="text-dark-text-muted text-sm mb-6">Update your details or request a password reset email.</p>

      <div className="glass-strong rounded-xl border border-dark-border p-6 max-w-2xl space-y-4">
        <div>
          <label className="block text-xs text-dark-text-secondary mb-1">Email</label>
          <input
            readOnly
            className="w-full px-3 py-2 rounded-lg bg-dark-card/50 border border-dark-border text-dark-text-muted"
            value={email}
          />
        </div>
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs text-dark-text-secondary mb-1">Name</label>
            <input
              required
              className="w-full px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-dark-text-primary"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs text-dark-text-secondary mb-1">Phone</label>
            <input
              required
              className="w-full px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-dark-text-primary"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>
          <div>
            <p className="text-xs text-dark-text-muted mb-2">Partners (max 3; leave rows empty to omit)</p>
            {partners.map((p, i) => (
              <div key={i} className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
                <input
                  placeholder="Partner name"
                  className="px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-sm text-dark-text-primary"
                  value={p.partner_name}
                  onChange={(e) => updatePartner(i, 'partner_name', e.target.value)}
                />
                <input
                  placeholder="CNIC 12345-1234567-1"
                  className="px-3 py-2 rounded-lg bg-dark-card border border-dark-border text-sm font-mono text-dark-text-primary"
                  value={p.partner_cnic}
                  onChange={(e) => updatePartner(i, 'partner_cnic', e.target.value)}
                />
              </div>
            ))}
          </div>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-ai-blue to-ai-purple text-dark-bg font-medium disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </form>

        <div className="pt-4 border-t border-dark-border space-y-3">
          <button
            type="button"
            onClick={handleEmailReset}
            className="px-4 py-2 rounded-lg border border-ai-blue/40 text-ai-blue hover:bg-dark-card text-sm"
          >
            Email password reset link
          </button>
          <div>
            <button
              type="button"
              onClick={handleDeleteAccount}
              className="px-4 py-2 rounded-lg bg-red-600/20 text-red-400 hover:bg-red-600/30 text-sm"
            >
              Delete Super Admin account
            </button>
            <p className="text-xs text-dark-text-muted mt-1">
              Only allowed when no branches exist in the system.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
