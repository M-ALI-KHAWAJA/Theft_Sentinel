import { useState, useEffect } from 'react';
import { listTrackingRecords } from '../../api/tracking';
import Table, { Pagination } from '../../components/Table';
import toast from 'react-hot-toast';

const Records = () => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    camera_id: '',
    start_date: '',
    end_date: '',
  });

  useEffect(() => {
    fetchRecords();
  }, [currentPage, filters]);

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const response = await listTrackingRecords({
        page: currentPage,
        ...filters,
      });
      setRecords(response.data.results || response.data);
      setTotalPages(Math.ceil((response.data.count || records.length) / 10));
    } catch (error) {
      console.error('Error fetching tracking records:', error);
      toast.error('Failed to load tracking records');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { key: 'person_id', label: 'Person ID' },
    { key: 'camera_name', label: 'Camera', render: (row) => row.camera_name || row.camera_id },
    { key: 'timestamp', label: 'Timestamp', render: (row) => new Date(row.timestamp).toLocaleString() },
    { key: 'location', label: 'Location' },
    {
      key: 'confidence',
      label: 'Confidence',
      render: (row) => `${(row.confidence * 100).toFixed(1)}%`,
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Tracking</h1>

      {/* Filters */}
      <div className="glass p-4 rounded-xl border border-dark-border">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Camera ID..."
            value={filters.camera_id}
            onChange={(e) => setFilters({ ...filters, camera_id: e.target.value })}
            className="px-4 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary placeholder-dark-text-muted focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
          />
          <input
            type="datetime-local"
            placeholder="Start Date"
            value={filters.start_date}
            onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
            className="px-4 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary placeholder-dark-text-muted focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
          />
          <input
            type="datetime-local"
            placeholder="End Date"
            value={filters.end_date}
            onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
            className="px-4 py-2 bg-dark-card border border-dark-border rounded-md text-dark-text-primary placeholder-dark-text-muted focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-transparent"
          />
        </div>
      </div>

      {/* Table */}
      <Table columns={columns} data={records} loading={loading} />

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
      )}
    </div>
  );
};

export default Records;

