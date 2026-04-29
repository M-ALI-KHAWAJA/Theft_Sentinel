import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CenteredModal from '../../components/CenteredModal';
import { useModal } from '../../hooks/useModal';
import { createSuperAdmin, superAdminExists } from '../../api/tenancy';

const CreateSuperAdmin = () => {
  const navigate = useNavigate();
  const { modalState, showSuccess, showError, hideModal } = useModal();

  const [checking, setChecking] = useState(true);
  const [allowed, setAllowed] = useState(false);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
    partners_count: 0,
    partner_names: [],
    partner_cnics: [],
  });

  useEffect(() => {
    const check = async () => {
      try {
        const res = await superAdminExists();
        setAllowed(!res.data?.exists);
      } catch {
        setAllowed(false);
      } finally {
        setChecking(false);
      }
    };
    check();
  }, []);

  const setPartnersCount = (count) => {
    const c = Number(count);
    setFormData((p) => {
      const names = [...(p.partner_names || [])].slice(0, c);
      const cnics = [...(p.partner_cnics || [])].slice(0, c);
      while (names.length < c) names.push('');
      while (cnics.length < c) cnics.push('');
      return { ...p, partners_count: c, partner_names: names, partner_cnics: cnics };
    });
  };

  const handleChange = (e) => {
    setFormData((p) => ({ ...p, [e.target.name]: e.target.value }));
  };

  const handlePartnerChange = (idx, key, value) => {
    setFormData((p) => {
      const arr = [...p[key]];
      arr[idx] = value;
      return { ...p, [key]: arr };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createSuperAdmin(formData);
      showSuccess('Super Admin created. You can now log in.');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.message || 'Failed to create Super Admin.';
      showError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-bg">
        <div className="glass-strong rounded-xl p-6 text-center">
          <p className="text-dark-text-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  if (!allowed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-bg">
        <div className="glass-strong rounded-xl p-8 text-center max-w-lg">
          <h2 className="text-2xl font-bold text-white mb-2">Super Admin Already Exists</h2>
          <p className="text-dark-text-muted mb-6">You can’t create another Super Admin account.</p>
          <button
            onClick={() => navigate('/login')}
            className="px-6 py-3 bg-ai-blue text-dark-bg font-bold rounded-lg"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg px-4 py-12">
      <CenteredModal show={modalState.show} type={modalState.type} message={modalState.message} onClose={hideModal} />

      <div className="w-full max-w-2xl glass-strong rounded-2xl p-8 border border-white/10">
        <h1 className="text-3xl font-bold text-white mb-2">Create Super Admin</h1>
        <p className="text-dark-text-muted mb-8">One-time setup for enterprise multi-tenant management.</p>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Full Name</label>
              <input
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Phone Number</label>
              <input
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Email</label>
              <input
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Password</label>
              <input
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-dark-text-secondary mb-1">Number of Partners (max 3)</label>
            <select
              value={formData.partners_count}
              onChange={(e) => setPartnersCount(e.target.value)}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </div>

          {formData.partners_count > 0 && (
            <div className="space-y-3">
              {[...Array(formData.partners_count)].map((_, idx) => (
                <div key={idx} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-dark-text-secondary mb-1">Partner Name #{idx + 1}</label>
                    <input
                      value={formData.partner_names[idx] || ''}
                      onChange={(e) => handlePartnerChange(idx, 'partner_names', e.target.value)}
                      required
                      className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-dark-text-secondary mb-1">Partner CNIC #{idx + 1}</label>
                    <input
                      value={formData.partner_cnics[idx] || ''}
                      onChange={(e) => handlePartnerChange(idx, 'partner_cnics', e.target.value)}
                      required
                      className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-ai-blue to-ai-purple text-dark-bg font-bold rounded-lg disabled:opacity-60"
          >
            {loading ? 'Creating...' : 'Create Super Admin'}
          </button>

          <button
            type="button"
            onClick={() => navigate('/')}
            className="w-full py-2 text-sm text-ai-blue"
          >
            ← Back to Home
          </button>
        </form>
      </div>
    </div>
  );
};

export default CreateSuperAdmin;

