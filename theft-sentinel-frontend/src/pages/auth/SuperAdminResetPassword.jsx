import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LockClosedIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { superAdminRequestPasswordEmail } from '../../api/tenants';
import CenteredModal from '../../components/CenteredModal';
import { useModal } from '../../hooks/useModal';

const SuperAdminResetPassword = () => {
  const navigate = useNavigate();
  const { modalState, showSuccess, showError, hideModal } = useModal();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = email.trim().toLowerCase();
    if (!trimmed) {
      showError('Email is required.');
      return;
    }
    setLoading(true);
    try {
      const { data } = await superAdminRequestPasswordEmail({ email: trimmed });
      showSuccess(data?.message || 'Reset link sent');
      setEmail('');
    } catch (err) {
      const d = err.response?.data;
      const msg =
        (typeof d?.error === 'string' && d.error) ||
        (typeof d?.message === 'string' && d.message) ||
        'Request failed. Try again later.';
      showError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg relative overflow-hidden px-4">
      <CenteredModal
        show={modalState.show}
        type={modalState.type}
        message={modalState.message}
        onClose={hideModal}
      />
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-ai-blue/20 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-ai-purple/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative z-10 w-full max-w-md glass-strong rounded-2xl p-8 shadow-dark-lg border border-dark-border">
        <button
          type="button"
          onClick={() => navigate('/login')}
          className="flex items-center gap-2 text-sm text-dark-text-muted hover:text-ai-blue mb-6"
        >
          <ArrowLeftIcon className="h-5 w-5" />
          Back to login
        </button>
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-ai-blue to-ai-purple mb-3">
            <LockClosedIcon className="h-8 w-8 text-dark-bg" />
          </div>
          <h1 className="text-2xl font-bold text-dark-text-primary">Super Admin reset password</h1>
          <p className="text-dark-text-muted text-sm mt-2">Enter your Super Admin account email. We will send a reset link.</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="sa-email" className="block text-sm text-dark-text-secondary mb-1">
              Email
            </label>
            <input
              id="sa-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(ev) => setEmail(ev.target.value)}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-dark-text-primary"
              placeholder="Super Admin email"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg bg-gradient-to-r from-ai-blue to-ai-purple text-dark-bg font-semibold disabled:opacity-50"
          >
            {loading ? 'Sending…' : 'Send reset link'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default SuperAdminResetPassword;
