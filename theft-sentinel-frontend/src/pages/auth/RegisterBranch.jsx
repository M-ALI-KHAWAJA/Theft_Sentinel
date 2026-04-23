import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LockClosedIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import CenteredModal from '../../components/CenteredModal';
import { useModal } from '../../hooks/useModal';
import { registerBranch } from '../../api/tenants';

const CNIC_RE = /^\d{5}-\d{7}-\d{1}$/;
const PHONE_INTL_RE = /^\+\d{8,20}$/;

const RegisterBranch = () => {
  const navigate = useNavigate();
  const { modalState, showSuccess, showError, hideModal } = useModal();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    branch_name: '',
    email: '',
    cnic: '',
    phone_number: '',
    password: '',
  });

  const onChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    const email = form.email.trim().toLowerCase();
    if (!email.endsWith('@gmail.com')) {
      showError('Email must be a Gmail address (@gmail.com).');
      return;
    }
    if (!CNIC_RE.test(form.cnic.trim())) {
      showError('CNIC must be in format 12345-1234567-1.');
      return;
    }
    const phone = form.phone_number.trim();
    if (!phone) {
      showError('Phone number is required.');
      return;
    }
    if (!phone.startsWith('+')) {
      showError('Phone number must start with + (international format, e.g. +923001234567).');
      return;
    }
    if (!phone.slice(1).split('').every((c) => c >= '0' && c <= '9')) {
      showError('Phone number must contain only digits after +.');
      return;
    }
    if (!PHONE_INTL_RE.test(phone)) {
      showError('Enter a valid international phone number (e.g. +923001234567).');
      return;
    }
    if (!form.branch_name.trim()) {
      showError('Branch name is required.');
      return;
    }
    setLoading(true);
    try {
      await registerBranch({
        branch_name: form.branch_name.trim(),
        email,
        cnic: form.cnic.trim(),
        phone_number: phone,
        password: form.password,
      });
      showSuccess('Registration submitted. You will get an email when approved.');
      setTimeout(() => navigate('/login'), 2200);
    } catch (err) {
      const msg =
        err.response?.data?.email?.[0] ||
        err.response?.data?.cnic?.[0] ||
        err.response?.data?.branch_name?.[0] ||
        err.response?.data?.password?.[0] ||
        err.response?.data?.phone_number?.[0] ||
        err.response?.data?.detail ||
        'Registration failed.';
      showError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg relative overflow-hidden">
      <CenteredModal
        show={modalState.show}
        type={modalState.type}
        message={modalState.message}
        onClose={hideModal}
      />
      <div className="absolute inset-0 overflow-hidden opacity-40">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-ai-blue/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-ai-purple/20 rounded-full blur-3xl" />
      </div>
      <div className="relative z-10 w-full max-w-md px-4">
        <div className="glass-strong rounded-2xl p-8 shadow-dark-lg">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-ai-blue to-ai-purple mb-4">
              <LockClosedIcon className="h-8 w-8 text-dark-bg" />
            </div>
            <h1 className="text-2xl font-bold text-gradient-ai">Register your branch</h1>
            <p className="text-dark-text-muted text-sm mt-2">
              Use a Gmail address. You can sign in after platform approval.
            </p>
          </div>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Branch name</label>
              <input
                name="branch_name"
                value={form.branch_name}
                onChange={onChange}
                required
                className="w-full px-4 py-2.5 bg-dark-card border border-dark-border rounded-lg text-dark-text-primary"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Gmail</label>
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={onChange}
                required
                placeholder="you@gmail.com"
                className="w-full px-4 py-2.5 bg-dark-card border border-dark-border rounded-lg text-dark-text-primary"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">CNIC</label>
              <input
                name="cnic"
                value={form.cnic}
                onChange={onChange}
                required
                placeholder="12345-1234567-1"
                className="w-full px-4 py-2.5 bg-dark-card border border-dark-border rounded-lg text-dark-text-primary font-mono text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">
                Phone number <span className="text-status-error">*</span>
              </label>
              <input
                name="phone_number"
                type="tel"
                value={form.phone_number}
                onChange={onChange}
                required
                placeholder="+923001234567"
                autoComplete="tel"
                className="w-full px-4 py-2.5 bg-dark-card border border-dark-border rounded-lg text-dark-text-primary font-mono text-sm"
              />
              <p className="text-xs text-dark-text-muted mt-1">International format: + then digits only (SMS alerts).</p>
            </div>
            <div>
              <label className="block text-sm text-dark-text-secondary mb-1">Password</label>
              <div className="relative">
                <input
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={onChange}
                  required
                  minLength={8}
                  className="w-full px-4 py-2.5 pr-11 bg-dark-card border border-dark-border rounded-lg text-dark-text-primary"
                />
                <button
                  type="button"
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-dark-text-muted"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
                </button>
              </div>
              <p className="text-xs text-dark-text-muted mt-1">
                8+ chars, upper, lower, number, special character.
              </p>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-gradient-to-r from-ai-blue to-ai-purple text-dark-bg font-semibold disabled:opacity-50"
            >
              {loading ? 'Submitting…' : 'Submit registration'}
            </button>
          </form>
          <div className="mt-6 text-center">
            <button type="button" className="text-sm text-ai-blue" onClick={() => navigate('/login')}>
              Back to sign in
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterBranch;
