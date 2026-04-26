/**
 * CameraFeedWithOverlay
 *
 * Renders the raw MJPEG camera feed in an <img> and overlays an HTML5
 * <canvas> on top.  When the AI pipeline fires an alert or flags suspicious
 * persons the canvas draws LERP-smoothed bounding boxes labelled with the
 * re-ID global ID — 100 % client-side, zero extra backend bandwidth.
 *
 * ┌──────────────────────────────────────────┐
 * │  <img>  z-index:1   raw MJPEG feed       │
 * │  <canvas> z-index:10  (pointer-events:   │
 * │            none — click-through)         │
 * │  LIVE badge / AI badge   z-index:20      │
 * │  [Stop Tracking] — full mode only here   │
 * └──────────────────────────────────────────┘
 * │  [Stop Tracking] — grid mode: block flow │   ← below the video box
 */
import { useRef, useEffect, useCallback, useState, memo } from 'react';
import PropTypes from 'prop-types';
import useRealtimeTracking from '../hooks/useRealtimeTracking';

// ── Tunable constants ─────────────────────────────────────────────────────────

/** X3D score ≥ this threshold qualifies as suspicious. */
const SUSPICIOUS_THRESHOLD = 0.5;

/**
 * LERP factor applied every rAF tick (~60 Hz).
 * 0.0 = frozen,  1.0 = instant snap.
 */
const LERP_FACTOR = 0.2;

// ─────────────────────────────────────────────────────────────────────────────

const CameraFeedWithOverlay = memo(({
  cameraId,
  width         = '100%',
  height        = 'auto',
  className     = '',
  enableOverlay = true,
  viewMode      = 'full',   // 'full' | 'grid'
}) => {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const isGridMode   = viewMode === 'grid';

  // DOM refs
  const imgRef    = useRef(null);
  const canvasRef = useRef(null);
  const rafRef    = useRef(null);

  // ── Frame-level metadata (alert status, frame dims, suspicious IDs) ────────
  const frameMetaRef = useRef({
    alert_triggered: false,
    classification:  'normal',
    confidence:      0,
    frame_width:     640,
    frame_height:    480,
    suspicious_ids:  new Set(),
  });

  // ── Map-based Suspect LERP State ───────────────────────────────────────────
  const latchedSuspectsRef = useRef(new Map());
  const visualBoxRef = useRef({});
  const targetBoxRef = useRef({}); 

  // ── Tracking & Alert UI State ──────────────────────────────────────────────
  const [isTrackingActive, setIsTrackingActive] = useState(false);
  const [currentFrameAlert, setCurrentFrameAlert] = useState(false);

  // ── SSE hook ───────────────────────────────────────────────────────────────
  const { trackingData, connected } = useRealtimeTracking(cameraId, enableOverlay);

  // ── Process every incoming SSE event ──────────────────────────────────────
  useEffect(() => {
    if (!trackingData) return;

    frameMetaRef.current = {
      alert_triggered: Boolean(trackingData.alert_triggered),
      classification:  trackingData.classification ?? 'normal',
      confidence:      trackingData.confidence      ?? 0,
      frame_width:     trackingData.frame_width     || 640,
      frame_height:    trackingData.frame_height    || 480,
      suspicious_ids:  new Set(trackingData.suspicious_ids || []),
    };

    const now = performance.now();
    const tracks = trackingData.tracks || [];

    for (const track of tracks) {
      const trackId = track.global_id || track.track_id;

      const isSuspicious = 
        track.is_suspicious === true ||
        frameMetaRef.current.suspicious_ids.has(track.global_id) ||
        frameMetaRef.current.suspicious_ids.has(track.track_id) ||
        (track.x3d_score ?? 0) >= SUSPICIOUS_THRESHOLD ||
        trackingData.alert_triggered;

      // Lock-On
      if (isSuspicious) {
        latchedSuspectsRef.current.set(trackId, now);
      } 
      // Keep Alive
      else if (latchedSuspectsRef.current.has(trackId)) {
        latchedSuspectsRef.current.set(trackId, now);
      }

      // Update target for LERP if they are latched
      if (latchedSuspectsRef.current.has(trackId)) {
        const [x1, y1, x2, y2] = track.bbox;
        const x = x1;
        const y = y1;
        const w = x2 - x1;
        const h = y2 - y1;
        
        const effectiveAlert = trackingData.alert_triggered;
        const color = effectiveAlert ? '#FF1111' : '#FF8800';
        const gid = track.global_id ?? '?';
        const label = `SUSPECT G:${gid}`;
        const score = `${((track.x3d_score ?? 0) * 100).toFixed(0)}%`;

        targetBoxRef.current[trackId] = {
          x, y, w, h,
          lastUpdated: now,
          label,
          score,
          color
        };

        if (!visualBoxRef.current[trackId]) {
          visualBoxRef.current[trackId] = { x, y, w, h, label, score, color };
        }
      }
    }

    // Sync React state for button visibility without causing rapid renders
    if (latchedSuspectsRef.current.size > 0 && !isTrackingActive) {
      setIsTrackingActive(true);
    } else if (latchedSuspectsRef.current.size === 0 && isTrackingActive) {
      setIsTrackingActive(false);
    }

    setCurrentFrameAlert(Boolean(trackingData.alert_triggered));

  }, [trackingData, isTrackingActive]);

  // ── Stop Tracking handler ──────────────────────────────────────────────────
  const handleStopTracking = useCallback(() => {
    latchedSuspectsRef.current.clear();
    targetBoxRef.current = {};
    visualBoxRef.current = {};
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    setIsTrackingActive(false);
  }, []);

  // ── Canvas drawing loop (requestAnimationFrame) ────────────────────────────
  const drawLoop = useCallback(() => {
    const canvas = canvasRef.current;
    const img    = imgRef.current;

    if (!canvas || !img) {
      rafRef.current = requestAnimationFrame(drawLoop);
      return;
    }

    const ctx = canvas.getContext('2d');

    const imgRect = img.getBoundingClientRect();
    const bufW    = Math.round(imgRect.width);
    const bufH    = Math.round(imgRect.height);
    if (canvas.width !== bufW || canvas.height !== bufH) {
      canvas.width  = bufW;
      canvas.height = bufH;
    }

    // Task 3: Single-Clear Render Loop - Called exactly ONCE at the top.
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const now = performance.now();

    for (const [trackId, timestamp] of latchedSuspectsRef.current.entries()) {
      const target = targetBoxRef.current[trackId];
      const visual = visualBoxRef.current[trackId];

      if (target && visual) {
        if (now - timestamp < 1500) {
          // Calculate LERP, protected against NaN
          const tX = Number.isFinite(target.x) ? target.x : visual.x;
          const tY = Number.isFinite(target.y) ? target.y : visual.y;
          const tW = Number.isFinite(target.w) ? target.w : visual.w;
          const tH = Number.isFinite(target.h) ? target.h : visual.h;

          visual.x += (tX - visual.x) * LERP_FACTOR;
          visual.y += (tY - visual.y) * LERP_FACTOR;
          visual.w += (tW - visual.w) * LERP_FACTOR;
          visual.h += (tH - visual.h) * LERP_FACTOR;

          if (Number.isNaN(visual.x)) visual.x = tX || 0;
          if (Number.isNaN(visual.y)) visual.y = tY || 0;
          if (Number.isNaN(visual.w)) visual.w = tW || 0;
          if (Number.isNaN(visual.h)) visual.h = tH || 0;

          if (visual.w > 0 && visual.h > 0) {
            const meta     = frameMetaRef.current;
            const nativeW  = meta.frame_width || 640;
            const nativeH  = meta.frame_height || 480;
            const displayW = canvas.clientWidth  || bufW;
            const displayH = canvas.clientHeight || bufH;
            const scaleX   = displayW / nativeW;
            const scaleY   = displayH / nativeH;

            const drawX = visual.x * scaleX;
            const drawY = visual.y * scaleY;
            const drawW = visual.w * scaleX;
            const drawH = visual.h * scaleY;

            ctx.save();
            ctx.strokeStyle = target.color || '#FF8800';
            ctx.lineWidth   = 2.5;
            ctx.shadowColor = target.color || '#FF8800';
            ctx.shadowBlur  = 6;
            ctx.strokeRect(drawX, drawY, drawW, drawH);
            ctx.restore();

            const label = target.label || 'SUSPECT';
            ctx.font = 'bold 12px "Courier New", monospace';
            const textW = ctx.measureText(label).width;

            const badgeColor = target.color === '#FF1111' ? 'rgba(220,0,0,0.85)' : 'rgba(200,100,0,0.85)';
            
            ctx.fillStyle = badgeColor;
            ctx.beginPath();
            if (ctx.roundRect) {
              ctx.roundRect(drawX, drawY - 22, textW + 10, 22, [3, 3, 0, 0]);
            } else {
              ctx.rect(drawX, drawY - 22, textW + 10, 22);
            }
            ctx.fill();

            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(label, drawX + 5, drawY - 6);

            const score = target.score || '0%';
            const scoreW = ctx.measureText(score).width;

            ctx.fillStyle = badgeColor;
            ctx.beginPath();
            if (ctx.roundRect) {
              ctx.roundRect(drawX, drawY + drawH, scoreW + 10, 18, [0, 0, 3, 3]);
            } else {
              ctx.rect(drawX, drawY + drawH, scoreW + 10, 18);
            }
            ctx.fill();

            ctx.fillStyle = '#FFFFFF';
            ctx.font      = '11px "Courier New", monospace';
            ctx.fillText(score, drawX + 5, drawY + drawH + 13);
          }
        } else {
          // Off-Screen Cleanup: Person left the frame. Stop drawing them entirely.
          latchedSuspectsRef.current.delete(trackId);
          delete targetBoxRef.current[trackId];
          delete visualBoxRef.current[trackId];
        }
      }
    }

    // Task 3: Ensure requestAnimationFrame schedules itself regardless of drawing
    rafRef.current = requestAnimationFrame(drawLoop);
  }, []); // stable — reads refs, never captures React state

  // Start / stop rAF loop
  useEffect(() => {
    if (!enableOverlay) return undefined;
    rafRef.current = requestAnimationFrame(drawLoop);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [drawLoop, enableOverlay]);

  // ── Stop Tracking / Paused notice ──────────────────────────────────────────
  const stopTrackingButton = enableOverlay && isTrackingActive && (
    <button
      onClick={(e) => { e.stopPropagation(); handleStopTracking(); }}
      className="flex items-center gap-2 bg-red-700 hover:bg-red-800
                 active:scale-95 text-white font-bold text-sm
                 py-2 px-5 rounded-full shadow-xl transition-all"
    >
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
        <rect x="6" y="6" width="12" height="12" rx="1" />
      </svg>
      Stop Tracking
    </button>
  );

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <>
      <div
        className={`${className}`}
        style={{
          position:   'relative',
          width,
          display:    'block',
          lineHeight: 0,
        }}
      >
        {/* Raw MJPEG feed */}
        <img
          ref={imgRef}
          src={`${API_BASE_URL}/api/cameras/${cameraId}/feed/`}
          alt="Live Camera Feed"
          style={{
            width:    '100%',
            height,
            display:  'block',
            position: 'relative',
            zIndex:   1,
          }}
          className="rounded-lg shadow-md"
          onError={(e) => {
            e.target.onerror = null;
            e.target.src =
              'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg"' +
              ' width="640" height="360"%3E%3Crect fill="%23111827" width="640"' +
              ' height="360"/%3E%3Ctext fill="%236B7280" font-family="sans-serif"' +
              ' font-size="18" x="50%25" y="50%25" text-anchor="middle"' +
              ' dy=".35em"%3ECamera Feed Unavailable%3C/text%3E%3C/svg%3E';
          }}
        />

        {/* Canvas overlay */}
        {enableOverlay && (
          <canvas
            ref={canvasRef}
            style={{
              position:      'absolute',
              top:           0,
              left:          0,
              width:         '100%',
              height:        '100%',
              pointerEvents: 'none',
              zIndex:        10,
            }}
          />
        )}

        {/* Real-Time Alert UI Badge */}
        {enableOverlay && (
          <div
            style={{ zIndex: 20 }}
            className={`absolute top-2 left-2 flex items-center space-x-1 px-3 py-1 rounded text-xs font-bold shadow-md transition-colors ${
              currentFrameAlert ? 'bg-red-600 text-white animate-pulse' : 'bg-green-600 text-white'
            }`}
          >
            <span>{currentFrameAlert ? 'THEFT DETECTED' : 'NORMAL'}</span>
          </div>
        )}

        {/* LIVE badge */}
        <div
          style={{ zIndex: 20 }}
          className="absolute top-2 right-2 flex items-center space-x-1
                     bg-red-600 text-white px-2 py-0.5 rounded text-xs font-semibold"
        >
          <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
          <span>LIVE</span>
        </div>

        {/* AI connection badge */}
        {enableOverlay && (
          <div
            style={{ zIndex: 20 }}
            className={`absolute bottom-2 right-2 px-2 py-0.5 rounded text-xs
                        font-semibold transition-colors ${
                          connected
                            ? 'bg-green-600 text-white'
                            : 'bg-yellow-400 text-gray-900'
                        }`}
          >
            {connected ? '● AI LIVE' : '◌ AI…'}
          </div>
        )}

        {/* FULL mode: Stop Tracking */}
        {!isGridMode && (
          <>
            {stopTrackingButton && (
              <div
                style={{
                  position:  'absolute',
                  bottom:    48,
                  left:      '50%',
                  transform: 'translateX(-50%)',
                  zIndex:    20,
                }}
              >
                {stopTrackingButton}
              </div>
            )}
          </>
        )}
      </div>

      {/* GRID mode: Stop Tracking */}
      {isGridMode && stopTrackingButton && (
        <div className="flex justify-center items-center py-2 px-3">
          {stopTrackingButton}
        </div>
      )}
    </>
  );
});

CameraFeedWithOverlay.displayName = 'CameraFeedWithOverlay';

CameraFeedWithOverlay.propTypes = {
  cameraId:      PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  width:         PropTypes.string,
  height:        PropTypes.string,
  className:     PropTypes.string,
  enableOverlay: PropTypes.bool,
  viewMode:      PropTypes.oneOf(['full', 'grid']),
};

export default CameraFeedWithOverlay;
