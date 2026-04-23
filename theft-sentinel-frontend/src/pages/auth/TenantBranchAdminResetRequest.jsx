import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BuildingOffice2Icon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { requestPasswordReset } from '../../api/auth';
import CenteredModal from '../../components/CenteredModal';
import { useModal } from '../../hooks/useModal';

const TenantBranchAdminResetRequest = () => {
  const navigate = useNavigate();
  const { modalState, showSuccess, showError, hideModal } = useModal();
  const [email, setEmail] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const em = email.trim().toLowerCase();
    const rs = reason.trim();
    if (!em) {
      showError('Email is required.');
      return;
    }
    if (!rs) {
      showError('Reason is required.');
      return;
    }
    setLoading(true);
    try {
      const { data } = await requestPasswordReset({ email: em, reason: rs });
      showSuccess(data?.message || 'Request sent to Super Admin');
      setEmail('');
      setReason('');
    } catch (err) {
      const d = err.response?.data;
      let msg =
        (typeof d?.error === 'string' && d.error) ||
        (typeof d?.message === 'string' && d.message) ||
        (d?.email && (Array.isArray(d.email) ? d.email[0] : d.email)) ||
        (d?.reason && (Array.isArray(d.reason) ? d.reason[0] : d.reason)) ||
        'Request failed.';
      if (typeof msg !== 'string') msg = String(msg);
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
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-ai-purple/15 rounded-full blur-3xl" />
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
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-ai-blue/80 to-ai-purple mb-3">
            <BuildingOffice2Icon className="h-8 w-8 text-dark-bg" />
          </div>
          <h1 className="text-2xl font-bold text-dark-text-primary">Branch Admin reset request</h1>
          <p className="text-dark-text-muted text-sm mt-2">
            For branch administrators only. Your request is sent to the platform Super Admin for approval.
          </p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="ba-email" className="block text-sm text-dark-text-secondary mb-1">
              Email <span className="text-status-error">*</span>
            </label>
            <input
              id="ba-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(ev) => setEmail(ev.target.value)}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-dark-text-primary"
              placeholder="Branch Admin email"
            />
          </div>
          <div>
            <label htmlFor="ba-reason" className="block text-sm text-dark-text-secondary mb-1">
              Reason <span className="text-status-error">*</span>
            </label>
            <textarea
              id="ba-reason"
              rows={4}
              required
              value={reason}
              onChange={(ev) => setReason(ev.target.value)}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg text-dark-text-primary text-sm"
              placeholder="Explain why you need a password reset (min. 10 characters)"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg bg-gradient-to-r from-ai-blue to-ai-purple text-dark-bg font-semibold disabled:opacity-50"
          >
            {loading ? 'Submitting…' : 'Submit request'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default TenantBranchAdminResetRequest;
