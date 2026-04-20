import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getCamera, updateCamera } from '../../api/cameras';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import CenteredModal from '../../components/CenteredModal';
import { useModal } from '../../hooks/useModal';

const Edit = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const { modalState, showSuccess, showError, hideModal } = useModal();
  const [formData, setFormData] = useState({
    name: '',
    rtsp_url: '',
    location: '',
    zone: '',
    status: 'ONLINE', // CORRECTED: Must be ONLINE or OFFLINE
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchCamera();
  }, [id]);

  const fetchCamera = async () => {
    try {
      const response = await getCamera(id);
      setFormData(response.data);
    } catch (error) {
      console.error('Error fetching camera:', error);
      showError('Failed to load camera details');
      setTimeout(() => {
        navigate('/cameras');
      }, 1500);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      await updateCamera(id, formData);
      showSuccess('Camera updated successfully');
      setTimeout(() => {
        navigate('/cameras');
      }, 1500);
    } catch (error) {
      console.error('Error updating camera:', error);
      showError(error.response?.data?.detail || 'Failed to update camera');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="animate-pulse h-96 bg-dark-card rounded-lg border border-dark-border"></div>;
  }

  return (
    <div className="space-y-6">
      <CenteredModal
        show={modalState.show}
        type={modalState.type}
        message={modalState.message}
        onClose={hideModal}
      />
      
      <div className="flex items-center space-x-4">
        <button
          onClick={() => navigate('/cameras')}
          className="p-2 hover:bg-dark-card rounded-full transition-colors"
        >
          <ArrowLeftIcon className="h-6 w-6 text-dark-text-secondary" />
        </button>
        <h1 className="text-3xl font-bold text-white">Control Room</h1>
      </div>

      <div className="glass rounded-xl border border-dark-border p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-dark-text-secondary">
                Camera Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="location" className="block text-sm font-medium text-dark-text-secondary">
                Location *
              </label>
              <input
                type="text"
                id="location"
                name="location"
                required
                value={formData.location}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="rtsp_url" className="block text-sm font-medium text-dark-text-secondary">
                RTSP URL *
              </label>
              <input
                type="text"
                id="rtsp_url"
                name="rtsp_url"
                required
                value={formData.rtsp_url}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="zone" className="block text-sm font-medium text-dark-text-secondary">
                Zone
              </label>
              <input
                type="text"
                id="zone"
                name="zone"
                value={formData.zone || ''}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="status" className="block text-sm font-medium text-dark-text-secondary">
                Status *
              </label>
              <select
                id="status"
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
              >
                <option value="ONLINE">Online</option>
                <option value="OFFLINE">Offline</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/cameras')}
              className="px-6 py-2 border border-dark-border rounded-md text-dark-text-secondary hover:bg-dark-card transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2 bg-ai-blue text-white rounded-md hover:bg-ai-blueDark transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            >
              {submitting ? 'Updating...' : 'Update Camera'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Edit;

