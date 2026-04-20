import { useState, useEffect, useRef, useCallback } from 'react';
import { startContinuousMonitoring, getMonitorStatus, stopContinuousMonitoring } from '../api/aiEngine';

/**
 * Custom Hook for Continuous Camera Monitoring
 * Uses backend continuous processing at 30 FPS instead of polling
 * @param {string} cameraId - Camera ID to monitor
 */
export const useContinuousMonitor = (cameraId) => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const intervalRef = useRef(null);
  const mountedRef = useRef(true);

  /**
   * Start continuous monitoring
   */
  const start = useCallback(async () => {
    if (!cameraId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await startContinuousMonitoring(cameraId);
      
      if (response.data.success) {
        setIsMonitoring(true);
      } else {
        setError(response.data.error || 'Failed to start monitoring');
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || 
                      err.response?.data?.detail || 
                      err.message || 
                      'Failed to start continuous monitoring';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [cameraId]);

  /**
   * Stop continuous monitoring
   */
  const stop = useCallback(async () => {
    if (!cameraId) return;
    
    setLoading(true);
    
    try {
      await stopContinuousMonitoring(cameraId);
      setIsMonitoring(false);
      setStats(null);
      setError(null);
    } catch (err) {
      const errorMsg = err.response?.data?.error || 
                      err.response?.data?.detail || 
                      err.message || 
                      'Failed to stop monitoring';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [cameraId]);

  /**
   * Toggle monitoring on/off
   */
  const toggle = useCallback(() => {
    if (isMonitoring) {
      stop();
    } else {
      start();
    }
  }, [isMonitoring, start, stop]);

  /**
   * Fetch monitor status
   */
  const fetchStatus = useCallback(async () => {
    if (!mountedRef.current || !cameraId) return;

    try {
      const response = await getMonitorStatus(cameraId);
      
      if (mountedRef.current) {
        if (response.data.monitor) {
          setStats(response.data.monitor);
          setError(null);
          
          // Check if monitor is still running
          if (!response.data.monitor.is_running) {
            setIsMonitoring(false);
          }
        } else {
          // Monitor stopped externally
          setIsMonitoring(false);
          setStats(null);
        }
      }
    } catch (err) {
      if (mountedRef.current) {
        // Don't set error for 404 (no monitor running)
        if (err.response?.status === 404) {
          setIsMonitoring(false);
          setStats(null);
        } else {
          const errorMsg = err.response?.data?.error || 
                          err.response?.data?.detail || 
                          'Failed to fetch status';
          setError(errorMsg);
        }
      }
    }
  }, [cameraId]);

  /**
   * Poll status while monitoring (every 1 second)
   */
  useEffect(() => {
    if (!isMonitoring) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Initial fetch
    fetchStatus();

    // Poll every 1 second for real-time updates
    intervalRef.current = setInterval(fetchStatus, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isMonitoring, fetchStatus]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    mountedRef.current = true;
    
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    isMonitoring,
    stats,
    loading,
    error,
    start,
    stop,
    toggle,
  };
};

