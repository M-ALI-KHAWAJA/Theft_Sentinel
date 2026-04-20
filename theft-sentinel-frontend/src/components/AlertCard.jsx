import { BellAlertIcon, TrashIcon } from '@heroicons/react/24/outline';

const AlertCard = ({ alert, onClick, onDelete, showDelete = false }) => {
  // Dark theme severity colors
  const severityColors = {
    low: 'border-status-info bg-status-info/10',
    medium: 'border-status-warning bg-status-warning/10',
    high: 'border-status-error bg-status-error/10',
    critical: 'border-status-error bg-status-error/20',
  };

  const severityBadgeColors = {
    low: 'bg-status-info/20 text-status-info border border-status-info/50',
    medium: 'bg-status-warning/20 text-status-warning border border-status-warning/50',
    high: 'bg-status-error/20 text-status-error border border-status-error/50',
    critical: 'bg-status-error/30 text-status-error border border-status-error animate-pulse',
  };

  const borderColor = severityColors[alert.severity] || 'border-dark-border bg-dark-card';
  const badgeColor = severityBadgeColors[alert.severity] || 'bg-dark-card text-dark-text-muted border border-dark-border';

  // Check if alert is acknowledged (status can be ACKED or acknowledged field)
  const isAcknowledged = alert.status === 'ACKED' || alert.status === 'RESOLVED' || alert.acknowledged;

  return (
    <div
      onClick={() => onClick && onClick(alert)}
      className={`glass rounded-xl p-6 border-l-4 ${borderColor} hover:shadow-glow-ai transition-all duration-300 cursor-pointer transform hover:scale-[1.02] ${
        !isAcknowledged ? 'ring-2 ring-status-error/50 shadow-glow-error' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-3 rounded-lg ${isAcknowledged ? 'bg-dark-card' : 'bg-status-error'}`}>
            <BellAlertIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-dark-text-primary">{alert.alert_type}</h3>
            <p className="text-sm text-dark-text-muted">{alert.description || 'No description'}</p>
          </div>
        </div>
        <div className="flex flex-col items-end space-y-2">
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${badgeColor}`}>
            {alert.severity?.toUpperCase() || 'UNKNOWN'}
          </span>
          {!isAcknowledged && (
            <span className="px-2 py-1 bg-status-error/20 text-status-error rounded-full text-xs font-semibold border border-status-error/50">
              NEW
            </span>
          )}
        </div>
      </div>

      <div className="mt-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-dark-text-muted">Camera:</span>
          <span className="font-medium text-dark-text-primary">{alert.camera_name || 'Unknown'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-dark-text-muted">Time:</span>
          <span className="font-medium text-dark-text-primary">
            {new Date(alert.timestamp).toLocaleString()}
          </span>
        </div>
        {isAcknowledged && (
          <div className="flex justify-between text-sm">
            <span className="text-dark-text-muted">Status:</span>
            <span className="font-medium text-status-success">✓ {alert.status || 'Acknowledged'}</span>
          </div>
        )}
      </div>

      {showDelete && (
        <div className="mt-4 pt-4 border-t border-dark-border">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete && onDelete(alert.id);
            }}
            className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-status-error text-white rounded-lg hover:bg-status-error/90 transition-all duration-200 font-semibold"
          >
            <TrashIcon className="h-4 w-4" />
            <span>Dismiss Alert</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default AlertCard;

