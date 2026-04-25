import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useRecoilValue } from 'recoil';
import { authUserState, isAuthenticatedState } from '../store/authStore';

// Layouts
import AdminLayout from '../layouts/AdminLayout';
import InchargeLayout from '../layouts/InchargeLayout';
import GuardLayout from '../layouts/GuardLayout';
import SuperAdminLayout from '../layouts/SuperAdminLayout';

// Auth Pages
import Login from '../pages/auth/Login';
import ForgotPassword from '../pages/auth/ForgotPassword';
import ResetPassword from '../pages/auth/ResetPassword';
import RegisterBranch from '../pages/auth/RegisterBranch';
import CreateSuperAdmin from '../pages/auth/CreateSuperAdmin';
import SuperAdminResetPassword from '../pages/auth/SuperAdminResetPassword';
import TenantBranchAdminResetRequest from '../pages/auth/TenantBranchAdminResetRequest';

// Landing Page
import Landing from '../pages/Landing';

// Super Admin
import SuperAdminDashboard from '../pages/super-admin/Dashboard';
import SuperAdminTenants from '../pages/super-admin/Tenants';
import SuperAdminPasswordResetRequests from '../pages/super-admin/PasswordResetRequests';
import SuperAdminProfile from '../pages/super-admin/Profile';
import SuperAdminQueries from '../pages/super-admin/Queries';

// Dashboard Pages
import Overview from '../pages/dashboard/Overview';
import BranchQueries from '../pages/dashboard/BranchQueries';
import AlertsStats from '../pages/dashboard/AlertsStats';
import IncidentsStats from '../pages/dashboard/IncidentsStats';
import CamerasStats from '../pages/dashboard/CamerasStats';
import RecentActivity from '../pages/dashboard/RecentActivity';
import HistoricalReporting from '../pages/dashboard/HistoricalReporting';
import GuardDashboard from '../pages/dashboard/GuardDashboard';

// Camera Pages
import CamerasList from '../pages/cameras/List';
import CameraCreate from '../pages/cameras/Create';
import CameraEdit from '../pages/cameras/Edit';
import ControlRoom from '../pages/cameras/ControlRoom';

// Alert Pages
import AlertsList from '../pages/alerts/List';
import AlertView from '../pages/alerts/View';
import GuardAlerts from '../pages/alerts/GuardAlerts';

// Incident Pages
import IncidentsList from '../pages/incidents/List';
import MyIncidents from '../pages/incidents/MyIncidents';
import UnassignedIncidents from '../pages/incidents/Unassigned';
import IncidentView from '../pages/incidents/View';

// Tracking Pages
import TrackingRecords from '../pages/tracking/Records';
import PersonPath from '../pages/tracking/PersonPath';

// Feedback Pages
import FeedbackList from '../pages/feedback/List';
import FeedbackCreate from '../pages/feedback/Create';
import MyFeedback from '../pages/feedback/MyFeedback';

// Personnel Pages
import PersonnelList from '../pages/personnel/List';
import PersonnelCreate from '../pages/personnel/Create';
import PersonnelEdit from '../pages/personnel/Edit';

// AI Pages
import AIDashboard from '../pages/ai/Dashboard';
import AIHistory from '../pages/ai/History';

// Protected Route Component - Redirects unauthenticated users to login
const ProtectedRoute = ({ children, allowedRoles }) => {
  const isAuthenticated = useRecoilValue(isAuthenticatedState);
  const user = useRecoilValue(authUserState);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role === 'SUPER_ADMIN') {
    if (!allowedRoles || !allowedRoles.includes('SUPER_ADMIN')) {
      return <Navigate to="/super-admin/dashboard" replace />;
    }
    return children;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    if (user.role === 'SECURITY_GUARD') {
      return <Navigate to="/dashboard/guard" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Public Route Component - Redirects authenticated users away from public pages
const PublicRoute = ({ children }) => {
  const isAuthenticated = useRecoilValue(isAuthenticatedState);
  const user = useRecoilValue(authUserState);

  if (isAuthenticated && user) {
    if (user.role === 'SUPER_ADMIN') {
      return <Navigate to="/super-admin/dashboard" replace />;
    }
    if (user.role === 'SECURITY_GUARD') {
      return <Navigate to="/dashboard/guard" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

const AppRouter = () => {
  const user = useRecoilValue(authUserState);

  const getLayout = () => {
    if (!user) return AdminLayout;

    switch (user.role) {
      case 'ADMIN':
        return AdminLayout;
      case 'SECURITY_INCHARGE':
        return InchargeLayout;
      case 'SECURITY_GUARD':
        return GuardLayout;
      default:
        return AdminLayout;
    }
  };

  const Layout = getLayout();

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <PublicRoute>
              <Landing />
            </PublicRoute>
          }
        />
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/super-admin/reset-password"
          element={
            <PublicRoute>
              <SuperAdminResetPassword />
            </PublicRoute>
          }
        />
        <Route
          path="/tenant/reset-password-request"
          element={
            <PublicRoute>
              <TenantBranchAdminResetRequest />
            </PublicRoute>
          }
        />
        <Route path="/register-branch" element={<RegisterBranch />} />
        <Route
          path="/create-super-admin"
          element={
            <PublicRoute>
              <CreateSuperAdmin />
            </PublicRoute>
          }
        />
        <Route
          path="/forgot-password"
          element={
            <PublicRoute>
              <ForgotPassword />
            </PublicRoute>
          }
        />
        <Route
          path="/reset-password/:token"
          element={
            <PublicRoute>
              <ResetPassword />
            </PublicRoute>
          }
        />
        <Route
          path="/reset-password"
          element={
            <PublicRoute>
              <ResetPassword />
            </PublicRoute>
          }
        />

        <Route
          path="/super-admin"
          element={
            <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
              <SuperAdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<SuperAdminDashboard />} />
          <Route path="tenants" element={<SuperAdminTenants />} />
          <Route path="password-reset-requests" element={<SuperAdminPasswordResetRequests />} />
          <Route path="queries" element={<SuperAdminQueries />} />
          <Route path="profile" element={<SuperAdminProfile />} />
        </Route>

        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route
            path="dashboard"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <Overview />
              </ProtectedRoute>
            }
          />
          <Route
            path="dashboard/guard"
            element={
              <ProtectedRoute allowedRoles={['SECURITY_GUARD']}>
                <GuardDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="dashboard/platform-queries"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE', 'SECURITY_GUARD']}>
                <BranchQueries />
              </ProtectedRoute>
            }
          />
          <Route
            path="dashboard/alerts-stats"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <AlertsStats />
              </ProtectedRoute>
            }
          />
          <Route
            path="dashboard/incidents-stats"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <IncidentsStats />
              </ProtectedRoute>
            }
          />
          <Route
            path="dashboard/cameras-stats"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <CamerasStats />
              </ProtectedRoute>
            }
          />
          <Route
            path="dashboard/recent-activity"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <RecentActivity />
              </ProtectedRoute>
            }
          />
          <Route
            path="dashboard/historical-reporting"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <HistoricalReporting />
              </ProtectedRoute>
            }
          />

          <Route
            path="cameras"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <CamerasList />
              </ProtectedRoute>
            }
          />
          <Route
            path="cameras/control-room"
            element={
              <ProtectedRoute allowedRoles={['SECURITY_GUARD']}>
                <ControlRoom />
              </ProtectedRoute>
            }
          />
          <Route
            path="cameras/create"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <CameraCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="cameras/edit/:id"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <CameraEdit />
              </ProtectedRoute>
            }
          />

          <Route
            path="alerts"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <AlertsList />
              </ProtectedRoute>
            }
          />
          <Route
            path="alerts/guard"
            element={
              <ProtectedRoute allowedRoles={['SECURITY_GUARD']}>
                <GuardAlerts />
              </ProtectedRoute>
            }
          />
          <Route
            path="alerts/:id"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE', 'SECURITY_GUARD']}>
                <AlertView />
              </ProtectedRoute>
            }
          />

          <Route
            path="incidents"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <IncidentsList />
              </ProtectedRoute>
            }
          />
          <Route
            path="incidents/my"
            element={
              <ProtectedRoute allowedRoles={['SECURITY_GUARD']}>
                <MyIncidents />
              </ProtectedRoute>
            }
          />
          <Route
            path="incidents/unassigned"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <UnassignedIncidents />
              </ProtectedRoute>
            }
          />
          <Route path="incidents/:id" element={<IncidentView />} />

          <Route
            path="tracking"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <TrackingRecords />
              </ProtectedRoute>
            }
          />
          <Route
            path="tracking/person-path"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <PersonPath />
              </ProtectedRoute>
            }
          />

          <Route
            path="feedback"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <FeedbackList />
              </ProtectedRoute>
            }
          />
          <Route
            path="feedback/create"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE', 'SECURITY_GUARD']}>
                <FeedbackCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="feedback/my"
            element={
              <ProtectedRoute allowedRoles={['SECURITY_GUARD']}>
                <MyFeedback />
              </ProtectedRoute>
            }
          />

          <Route
            path="personnel"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <PersonnelList />
              </ProtectedRoute>
            }
          />
          <Route
            path="personnel/create"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <PersonnelCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="personnel/edit/:id"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <PersonnelEdit />
              </ProtectedRoute>
            }
          />

          <Route
            path="ai/dashboard"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <AIDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="ai/history"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
                <AIHistory />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRouter;
