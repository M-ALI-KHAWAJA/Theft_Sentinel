import { XMarkIcon } from '@heroicons/react/24/outline';
import CameraFeed from './CameraFeed';

const FullScreenCameraModal = ({ show, camera, onClose }) => {
  if (!show || !camera) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black flex items-center justify-center">
      {/* Close Button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 z-10 bg-white bg-opacity-20 hover:bg-opacity-30 text-white p-3 rounded-full transition-all"
        aria-label="Close"
      >
        <XMarkIcon className="h-8 w-8" />
      </button>

      {/* Camera Info Header */}
      <div className="absolute top-4 left-4 z-10 bg-black bg-opacity-70 text-white px-4 py-2 rounded-lg">
        <h2 className="text-xl font-bold">{camera.name}</h2>
        <p className="text-sm text-gray-300">{camera.location}</p>
      </div>

      {/* Full Screen Feed */}
      <div className="w-full h-full flex items-center justify-center">
        <CameraFeed 
          cameraId={camera.id} 
          width="100%" 
          height="100%" 
          className="w-full h-full"
        />
      </div>
    </div>
  );
};

export default FullScreenCameraModal;

