import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSetRecoilState } from 'recoil';
import { authUserState, authTokensState } from '../../store/authStore';
import { login as loginAPI, getCreateSuperAdminStatus } from '../../api/auth';
import { LockClosedIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import CenteredModal from '../../components/CenteredModal';
import { useModal } from '../../hooks/useModal';

const Login = () => {
  const navigate = useNavigate();
  const setAuthUser = useSetRecoilState(authUserState);
  const setAuthTokens = useSetRecoilState(authTokensState);
  const { modalState, showSuccess, showError, hideModal } = useModal();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState(null);
  const [showSuperAdminSetup, setShowSuperAdminSetup] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await getCreateSuperAdminStatus();
        if (!cancelled && data?.can_create) setShowSuperAdminSetup(true);
      } catch {
        /* ignore — setup link hidden */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await loginAPI(formData);
      const { access, refresh, user } = response.data;

      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      setAuthTokens({ access, refresh });
      setAuthUser(user);

      showSuccess('Login successful! Redirecting to dashboard...');
      setTimeout(() => {
        if (user.role === 'SUPER_ADMIN') {
          navigate('/super-admin/dashboard');
        } else if (user.role === 'SECURITY_GUARD') {
          navigate('/dashboard/guard');
        } else {
          navigate('/dashboard');
        }
      }, 1500);
    } catch (error) {
      const d = error.response?.data;
      let errorMsg =
        d?.error ||
        d?.message ||
        (typeof d?.detail === 'string' ? d.detail : null) ||
        (Array.isArray(d?.detail) ? d.detail[0] : null) ||
        (d?.detail && typeof d.detail === 'object' ? Object.values(d.detail).flat()[0] : null) ||
        'Login failed. Please check your credentials.';
      if (typeof errorMsg !== 'string') errorMsg = String(errorMsg);
      showError(errorMsg);
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

      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-ai-blue/20 rounded-full blur-3xl animate-pulse-slow" />
        <div
          className="absolute bottom-0 right-1/4 w-96 h-96 bg-ai-purple/20 rounded-full blur-3xl animate-pulse-slow"
          style={{ animationDelay: '1s' }}
        />
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage:
              'linear-gradient(rgba(0, 217, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 217, 255, 0.1) 1px, transparent 1px)',
            backgroundSize: '50px 50px',
          }}
        />
      </div>

      <div className="relative z-10 w-full max-w-md px-4">
        <div className="glass-strong rounded-2xl p-8 shadow-dark-lg animate-fadeIn">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-ai-blue to-ai-purple mb-4 shadow-glow-ai">
              <LockClosedIcon className="h-10 w-10 text-dark-bg" />
            </div>
            <h1 className="text-4xl font-bold mb-2">
              <span className="text-gradient-ai">Theft Sentinel</span>
            </h1>
            <p className="text-dark-text-muted text-sm">AI-Powered Intelligent Surveillance System</p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label
                htmlFor="username"
                className={`block text-sm font-medium transition-colors ${
                  focusedField === 'username' ? 'text-ai-blue' : 'text-dark-text-secondary'
                }`}
              >
                Username or email
              </label>
              <div className="relative">
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={formData.username}
                  onChange={handleChange}
                  onFocus={() => setFocusedField('username')}
                  onBlur={() => setFocusedField(null)}
                  className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-lg
                           text-dark-text-primary placeholder-dark-text-muted
                           focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent
                           transition-all duration-200"
                  placeholder="Username or work email"
                />
                {focusedField === 'username' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-ai-blue to-ai-purple animate-slideIn" />
                )}
              </div>
            </div>

            <div className="space-y-2">
              <label
                htmlFor="password"
                className={`block text-sm font-medium transition-colors ${
                  focusedField === 'password' ? 'text-ai-blue' : 'text-dark-text-secondary'
                }`}
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={handleChange}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  className="w-full px-4 py-3 pr-12 bg-dark-card border border-dark-border rounded-lg
                           text-dark-text-primary placeholder-dark-text-muted
                           focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent
                           transition-all duration-200"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-dark-text-muted hover:text-ai-blue transition-colors"
                >
                  {showPassword ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
                </button>
                {focusedField === 'password' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-ai-blue to-ai-purple animate-slideIn" />
                )}
              </div>
            </div>

            <p className="text-xs text-amber-400/90 bg-amber-400/10 border border-amber-400/20 rounded-lg px-3 py-2">
              Security Guards and Security Incharge must contact their Branch Admin for password reset.
            </p>

            <div className="grid grid-cols-1 gap-2">
              <button
                type="button"
                onClick={() => navigate('/super-admin/reset-password')}
                className="w-full py-2.5 px-4 rounded-lg border border-ai-blue/50 text-ai-blue text-sm font-medium hover:bg-ai-blue/10 transition-colors"
              >
                Super Admin Reset Password
              </button>
              <button
                type="button"
                onClick={() => navigate('/tenant/reset-password-request')}
                className="w-full py-2.5 px-4 rounded-lg border border-dark-border text-dark-text-secondary text-sm font-medium hover:bg-dark-card transition-colors"
              >
                Branch Admin Reset Request
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="group relative w-full py-3 px-4 bg-gradient-to-r from-ai-blue to-ai-purple
                       text-dark-bg font-semibold rounded-lg
                       hover:shadow-glow-ai-lg transition-all duration-300
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transform hover:scale-[1.02] active:scale-[0.98]"
            >
              <span className="relative z-10">
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-dark-bg"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  'Sign In'
                )}
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-ai-blue to-ai-purple rounded-lg blur-xl opacity-50 group-hover:opacity-75 transition-opacity" />
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-dark-border">
            <div className="text-center space-y-2">
              <p className="text-xs text-dark-text-muted">Contact your administrator for account access</p>
              <button
                type="button"
                onClick={() => navigate('/register-branch')}
                className="text-xs text-dark-text-secondary hover:text-ai-blue transition-colors block w-full"
              >
                Register your branch
              </button>
              {showSuperAdminSetup && (
                <button
                  type="button"
                  onClick={() => navigate('/create-super-admin')}
                  className="text-xs text-amber-400/90 hover:text-amber-300 transition-colors block w-full"
                >
                  Create Super Admin (first-time only)
                </button>
              )}
              <button
                type="button"
                onClick={() => navigate('/')}
                className="text-xs text-ai-blue hover:text-ai-blueDark transition-colors"
              >
                ← Back to Home
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
