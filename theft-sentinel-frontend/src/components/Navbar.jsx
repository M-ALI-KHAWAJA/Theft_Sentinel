import { Link, useNavigate } from 'react-router-dom';
import { useRecoilValue, useSetRecoilState } from 'recoil';
import { authUserState, authTokensState } from '../store/authStore';
import { CpuChipIcon, UserCircleIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { logout } from '../api/auth';

const Navbar = () => {
  const user = useRecoilValue(authUserState);
  const navigate = useNavigate();
  const setAuthUser = useSetRecoilState(authUserState);
  const setAuthTokens = useSetRecoilState(authTokensState);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      // Even if logout fails, clear local state
      console.error('Logout error:', error);
    } finally {
      // Clear all auth state
      localStorage.clear();
      setAuthUser(null);
      setAuthTokens({ access: null, refresh: null });
      
      toast.success('Logged out successfully');
      // Smooth redirect to login
      navigate('/login', { replace: true });
    }
  };

  const getRoleDisplay = (role) => {
    switch (role) {
      case 'ADMIN':
        return 'Admin';
      case 'SECURITY_INCHARGE':
        return 'Security In-Charge';
      case 'SECURITY_GUARD':
        return 'Security Guard';
      default:
        return role || 'User';
    }
  };


  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-dark-surface/95 backdrop-blur-lg border-b border-dark-border shadow-dark">
      <div className="max-w-full px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left: Logo */}
          <div className="flex items-center space-x-6 flex-1">
            <Link to="/dashboard" className="flex items-center space-x-2 group">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-ai-blue to-ai-purple flex items-center justify-center shadow-glow-ai group-hover:shadow-glow-ai-lg transition-all">
                <CpuChipIcon className="h-6 w-6 text-dark-bg" />
              </div>
              <span className="text-xl font-bold text-gradient-ai hidden sm:block">
                Theft Sentinel
              </span>
            </Link>
          </div>

          {/* Right: Profile Info & Logout */}
          <div className="flex items-center space-x-4">
            {/* Profile Info */}
            <div className="flex items-center space-x-3 px-4 py-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-ai-blue to-ai-purple flex items-center justify-center">
                <UserCircleIcon className="h-6 w-6 text-dark-bg" />
              </div>
              <div className="text-left hidden sm:block">
                <p className="text-sm font-medium text-dark-text-primary">
                  {user?.username || 'User'}
                </p>
                <p className="text-xs text-dark-text-muted">
                  {getRoleDisplay(user?.role)}
                </p>
              </div>
            </div>
            
            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm text-status-error hover:bg-dark-card rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
