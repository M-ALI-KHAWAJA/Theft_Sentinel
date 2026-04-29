import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CenteredModal from '../../components/CenteredModal';
import { useModal } from '../../hooks/useModal';
import { registerBranch } from '../../api/tenancy';
import { validatePassword } from '../../utils/validation';

const formatApiError = (data) => {
  if (!data) return 'Registration failed.';
  if (typeof data === 'string') return data;
  if (data.error || data.message || data.detail) {
    return data.error || data.message || data.detail;
  }

  if (typeof data === 'object') {
    const messages = Object.entries(data).flatMap(([field, value]) => {
      const label = field.replace(/_/g, ' ');
      const values = Array.isArray(value) ? value : [value];
      return values.map((item) => `${label}: ${item}`);
    });
    if (messages.length > 0) return messages.join('\n');
  }

  return 'Registration failed.';
};

const BranchRegister = () => {
  const navigate = useNavigate();
  const { modalState, showSuccess, showError, hideModal } = useModal();

  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    company_name: '',
    branch_name: '',
    admin_name: '',
    cnic: '',
    email: '',
    phone_number: '',
    company_address: '',
    password: '',
  });

  const handleChange = (e) => setFormData((p) => ({ ...p, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();

    const passwordCheck = validatePassword(formData.password);
    if (!passwordCheck.valid) {
      showError(passwordCheck.message);
      return;
    }

    setLoading(true);
    try {
      const payload = Object.fromEntries(
        Object.entries(formData).map(([key, value]) => [
          key,
          key === 'password' ? value : value.trim(),
        ])
      );

      await registerBranch(payload);
      showSuccess('Registration submitted. Your branch is pending Super Admin approval.');
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      showError(formatApiError(err.response?.data));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg px-4 py-12">
      <CenteredModal show={modalState.show} type={modalState.type} message={modalState.message} onClose={hideModal} />

      <div className="w-full max-w-2xl glass-strong rounded-2xl p-8 border border-white/10">
        <h1 className="text-3xl font-bold text-white mb-2">Branch Registration</h1>
        <p className="text-dark-text-muted mb-8">Create your company branch (approval required).</p>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Company Name</label>
              <input
                name="company_name"
                value={formData.company_name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Branch Name</label>
              <input
                name="branch_name"
                value={formData.branch_name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Admin Name</label>
              <input
                name="admin_name"
                value={formData.admin_name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">CNIC</label>
              <input
                name="cnic"
                value={formData.cnic}
                onChange={handleChange}
                required
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
              <label className="block text-sm text-dark-text-secondary mb-1">Phone Number (alerts)</label>
              <input
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-dark-text-secondary mb-1">Company Address</label>
            <input
              name="company_address"
              value={formData.company_address}
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

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-ai-blue to-ai-purple text-dark-bg font-bold rounded-lg disabled:opacity-60"
          >
            {loading ? 'Submitting...' : 'Submit Registration'}
          </button>

          <button type="button" onClick={() => navigate('/')} className="w-full py-2 text-sm text-ai-blue">
            ← Back to Home
          </button>
        </form>
      </div>
    </div>
  );
};

export default BranchRegister;

