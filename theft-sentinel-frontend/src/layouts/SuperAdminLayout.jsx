import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useRecoilValue, useSetRecoilState } from 'recoil';
import { authUserState, authTokensState } from '../store/authStore';
import {
  CpuChipIcon,
  BuildingOffice2Icon,
  ChartPieIcon,
  EnvelopeOpenIcon,
  UserCircleIcon,
  ChatBubbleLeftRightIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { logout } from '../api/auth';

const SuperAdminLayout = () => {
  const user = useRecoilValue(authUserState);
  const setAuthUser = useSetRecoilState(authUserState);
  const setAuthTokens = useSetRecoilState(authTokensState);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (e) {
      console.error(e);
    } finally {
      localStorage.clear();
      setAuthUser(null);
      setAuthTokens({ access: null, refresh: null });
      toast.success('Logged out');
      navigate('/login', { replace: true });
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-dark-surface/95 backdrop-blur-lg border-b border-dark-border">
        <div className="max-w-full px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <Link to="/super-admin/dashboard" className="flex items-center space-x-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-ai-blue to-ai-purple flex items-center justify-center">
              <CpuChipIcon className="h-6 w-6 text-dark-bg" />
            </div>
            <span className="text-lg font-bold text-gradient-ai">Theft Sentinel — Platform</span>
          </Link>
          <div className="flex items-center gap-6 text-sm">
            <Link
              to="/super-admin/dashboard"
              className="text-dark-text-secondary hover:text-ai-blue flex items-center gap-1"
            >
              <ChartPieIcon className="h-5 w-5" />
              Dashboard
            </Link>
            <Link
              to="/super-admin/tenants"
              className="text-dark-text-secondary hover:text-ai-blue flex items-center gap-1"
            >
              <BuildingOffice2Icon className="h-5 w-5" />
              Branches
            </Link>
            <Link
              to="/super-admin/password-reset-requests"
              className="text-dark-text-secondary hover:text-ai-blue flex items-center gap-1"
            >
              <EnvelopeOpenIcon className="h-5 w-5" />
              Reset requests
            </Link>
            <Link
              to="/super-admin/queries"
              className="text-dark-text-secondary hover:text-ai-blue flex items-center gap-1"
            >
              <ChatBubbleLeftRightIcon className="h-5 w-5" />
              Queries
            </Link>
            <Link
              to="/super-admin/profile"
              className="text-dark-text-secondary hover:text-ai-blue flex items-center gap-1"
            >
              <UserCircleIcon className="h-5 w-5" />
              Profile
            </Link>
            <span className="text-dark-text-muted hidden sm:inline">{user?.username}</span>
            <button
              type="button"
              onClick={handleLogout}
              className="px-3 py-1.5 text-status-error hover:bg-dark-card rounded-lg"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>
      <main className="pt-20 px-4 sm:px-8 pb-12 max-w-7xl mx-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default SuperAdminLayout;
