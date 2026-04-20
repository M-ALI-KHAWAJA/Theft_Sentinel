import { useState } from 'react';
import { getPersonPath } from '../../api/tracking';
import toast from 'react-hot-toast';
import { MapIcon } from '@heroicons/react/24/outline';

const PersonPath = () => {
  const [personId, setPersonId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [path, setPath] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!personId) {
      toast.error('Please enter a person ID');
      return;
    }

    setLoading(true);
    try {
      const response = await getPersonPath(personId, {
        start_date: startDate,
        end_date: endDate,
      });
      setPath(response.data);
      if (response.data.length === 0) {
        toast.info('No tracking data found for this person');
      }
    } catch (error) {
      console.error('Error fetching person path:', error);
      toast.error('Failed to load person path');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Tracking</h1>

      {/* Search Form */}
      <div className="glass p-6 rounded-xl border border-dark-border">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                Person ID *
              </label>
              <input
                type="text"
                required
                value={personId}
                onChange={(e) => setPersonId(e.target.value)}
                className="w-full px-4 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary placeholder-dark-text-muted focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
                placeholder="Enter person ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                Start Date/Time
              </label>
              <input
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                End Date/Time
              </label>
              <input
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-ai-blue text-white rounded-md hover:bg-ai-blueDark transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
          >
            {loading ? 'Searching...' : 'Track Path'}
          </button>
        </form>
      </div>

      {/* Path Results */}
      {path.length > 0 && (
        <div className="glass rounded-xl border border-dark-border p-6">
          <h2 className="text-xl font-semibold text-dark-text-primary mb-4 flex items-center">
            <MapIcon className="h-6 w-6 mr-2" />
            Path Timeline ({path.length} locations)
          </h2>
          <div className="space-y-4">
            {path.map((point, index) => (
              <div key={index} className="flex items-start space-x-4 pb-4 border-b border-dark-border last:border-b-0">
                <div className="bg-ai-blue text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 font-semibold">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-dark-text-primary">
                        {point.camera_name || `Camera ${point.camera_id}`}
                      </h3>
                      <p className="text-sm text-dark-text-secondary">{point.location || 'Unknown location'}</p>
                    </div>
                    <span className="text-sm text-dark-text-muted">
                      {new Date(point.timestamp).toLocaleString()}
                    </span>
                  </div>
                  {point.confidence && (
                    <p className="text-sm text-dark-text-muted mt-1">
                      Confidence: {(point.confidence * 100).toFixed(1)}%
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PersonPath;

