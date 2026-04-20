import { Outlet } from 'react-router-dom';
import { useRecoilValue } from 'recoil';
import { sidebarOpenState } from '../store/uiStore';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

const AdminLayout = () => {
  const sidebarOpen = useRecoilValue(sidebarOpenState);

  return (
    <div className="min-h-screen bg-dark-bg">
      <Navbar />
      <Sidebar />
      <main
        className={`transition-all duration-300 pt-20 ${
          sidebarOpen ? 'ml-64' : 'ml-0 lg:ml-20'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8 lg:pl-8 pl-16">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;

