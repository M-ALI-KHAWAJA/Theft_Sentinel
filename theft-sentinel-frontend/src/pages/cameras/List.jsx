import { useState, useEffect } from 'react';
import { listCameras, deleteCamera, updateCameraStatus } from '../../api/cameras';
import { useNavigate } from 'react-router-dom';
import { useRecoilValue } from 'recoil';
import { authUserState } from '../../store/authStore';
import CameraCardWithAI from '../../components/CameraCardWithAI';
import { Pagination } from '../../components/Table';
import { PlusIcon } from '@heroicons/react/24/outline';
import CenteredModal from '../../components/CenteredModal';
import ConfirmationModal from '../../components/ConfirmationModal';
import FullScreenCameraModal from '../../components/FullScreenCameraModal';
import { useModal } from '../../hooks/useModal';

const List = () => {
  const navigate = useNavigate();
  const user = useRecoilValue(authUserState);
  const { modalState, showSuccess, showError, hideModal } = useModal();
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showLiveFeeds, setShowLiveFeeds] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    zone: '',
  });
  const [fullScreenCamera, setFullScreenCamera] = useState(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState({ show: false, camera: null });

  const isAdmin = user?.role === 'ADMIN';
  const isSecurityIncharge = user?.role === 'SECURITY_INCHARGE';

  useEffect(() => {
    fetchCameras();
  }, [currentPage, filters]);

  const fetchCameras = async () => {
    setLoading(true);
    try {
      const response = await listCameras({
        page: currentPage,
        search: filters.search,
        status: filters.status,
        zone: filters.zone,
      });
      setCameras(response.data.results || response.data);
      setTotalPages(Math.ceil((response.data.count || cameras.length) / 10));
    } catch (error) {
      console.error('Error fetching cameras:', error);
      showError('Failed to load cameras');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (camera) => {
    setDeleteConfirmation({ show: true, camera });
  };

  const handleDeleteConfirm = async () => {
    const cameraId = deleteConfirmation.camera.id;
    setDeleteConfirmation({ show: false, camera: null });
    
    try {
      await deleteCamera(cameraId);
      showSuccess('Camera deleted successfully');
      fetchCameras();
    } catch (error) {
      console.error('Error deleting camera:', error);
      showError('Failed to delete camera');
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmation({ show: false, camera: null });
  };

  const handleViewFeed = (camera) => {
    setFullScreenCamera(camera);
  };

  const handleEditCamera = (camera) => {
    navigate(`/cameras/edit/${camera.id}`);
  };

  const handleStatusChange = async (camera, status) => {
    try {
      await updateCameraStatus(camera.id, status);
      showSuccess(status === 'ONLINE' ? 'Camera activated successfully' : 'Camera turned off successfully');
      fetchCameras();
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Failed to update camera status';
      showError(errorMsg);
      fetchCameras();
    }
  };


  return (
    <div className="space-y-6">
      <CenteredModal
        show={modalState.show}
        type={modalState.type}
        message={modalState.message}
        onClose={hideModal}
      />

      <ConfirmationModal
        show={deleteConfirmation.show}
        title="Delete Camera"
        message={`Are you sure you want to delete "${deleteConfirmation.camera?.name}"? This action cannot be undone.`}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        confirmText="Delete"
        cancelText="Cancel"
        type="danger"
      />

      <FullScreenCameraModal
        show={!!fullScreenCamera}
        camera={fullScreenCamera}
        onClose={() => setFullScreenCamera(null)}
      />
      
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
        <h1 className="text-3xl font-bold text-white">Control Room</h1>
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <button
            onClick={() => setShowLiveFeeds(!showLiveFeeds)}
            className={`px-4 py-2 rounded-md transition-colors flex items-center justify-center space-x-2 font-semibold ${
              showLiveFeeds 
                ? 'bg-status-success text-white hover:bg-status-success/90' 
                : 'glass border border-dark-border text-dark-text-secondary hover:bg-dark-card'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${showLiveFeeds ? 'bg-white animate-pulse' : 'bg-dark-text-muted'}`}></span>
            <span>{showLiveFeeds ? 'Live Feeds ON' : 'Live Feeds OFF'}</span>
          </button>
          {isAdmin && (
            <button
              onClick={() => navigate('/cameras/create')}
              className="px-4 py-2 bg-ai-blue text-white rounded-md hover:bg-ai-blueDark transition-colors flex items-center justify-center space-x-2 font-semibold"
            >
              <PlusIcon className="h-5 w-5" />
              <span>Add Camera</span>
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="glass p-4 rounded-xl border border-dark-border">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Search cameras..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="px-4 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary placeholder-dark-text-muted focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
          />
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="px-4 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
          >
            <option value="">All Status</option>
            <option value="ONLINE">Online</option>
            <option value="OFFLINE">Offline</option>
          </select>
          <input
            type="text"
            placeholder="Filter by zone..."
            value={filters.zone}
            onChange={(e) => setFilters({ ...filters, zone: e.target.value })}
            className="px-4 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary placeholder-dark-text-muted focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
          />
        </div>
      </div>

      {/* Camera Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          [...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-dark-card rounded-lg animate-pulse border border-dark-border"></div>
          ))
        ) : cameras.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-dark-text-muted">
            No cameras found
          </div>
        ) : (
          cameras.map((camera) => (
            <CameraCardWithAI
              key={camera.id}
              camera={camera}
              onViewFeed={handleViewFeed}
              onEdit={isAdmin ? handleEditCamera : null}
              onDelete={isAdmin ? handleDeleteClick : null}
              onStatusChange={isAdmin ? handleStatusChange : null}
              showFeed={showLiveFeeds}
              showActions={isAdmin}
            />
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      )}
    </div>
  );
};

export default List;

