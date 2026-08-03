"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface CameraCaptureProps {
  onCapture: (file: File, previewUrl: string) => void;
  onClose?: () => void;
}

export function CameraCapture({ onCapture, onClose }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>("");

  // Stop the camera stream
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsActive(false);
  }, []);

  // Start the camera
  const startCamera = useCallback(
    async (deviceId?: string) => {
      setError(null);
      try {
        // Stop any existing stream
        stopCamera();

        const constraints: MediaStreamConstraints = {
          video: {
            width: { ideal: 1920 },
            height: { ideal: 1080 },
            facingMode: "environment",
            ...(deviceId ? { deviceId: { exact: deviceId } } : {}),
          },
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }

        setIsActive(true);
      } catch (err) {
        const message =
          err instanceof DOMException
            ? err.name === "NotAllowedError"
              ? "摄像头权限被拒绝，请在浏览器设置中允许访问摄像头"
              : err.name === "NotFoundError"
                ? "未找到摄像头设备"
                : err.name === "NotReadableError"
                  ? "摄像头被其他应用占用"
                  : `摄像头启动失败: ${err.message}`
            : "摄像头启动失败";
        setError(message);
        toast.error(message);
      }
    },
    [stopCamera]
  );

  // Enumerate camera devices
  const enumerateDevices = useCallback(async () => {
    try {
      const allDevices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = allDevices.filter((d) => d.kind === "videoinput");
      setDevices(videoDevices);
      if (videoDevices.length > 0 && !selectedDevice) {
        setSelectedDevice(videoDevices[0].deviceId);
      }
    } catch {
      // Enumeration not supported
    }
  }, [selectedDevice]);

  // Capture a frame
  const capture = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Draw the video frame
    ctx.drawImage(video, 0, 0);

    // Convert to blob
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          toast.error("截图失败");
          return;
        }

        const file = new File([blob], `camera_${Date.now()}.jpg`, {
          type: "image/jpeg",
        });
        const previewUrl = URL.createObjectURL(blob);

        onCapture(file, previewUrl);
        stopCamera();
        toast.success("照片已捕获");
      },
      "image/jpeg",
      0.9
    );
  }, [onCapture, stopCamera]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  // Initial device enumeration
  useEffect(() => {
    enumerateDevices();
  }, [enumerateDevices]);

  if (error) {
    return (
      <div className="text-center py-8 space-y-4">
        <div className="text-4xl">📷</div>
        <p className="text-red-600 text-sm">{error}</p>
        <div className="flex gap-2 justify-center">
          <Button
            variant="outline"
            size="sm"
            onClick={() => startCamera(selectedDevice)}
          >
            🔄 重试
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={enumerateDevices}
          >
            🔍 检测摄像头
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Camera viewfinder */}
      <div className="relative bg-black rounded-xl overflow-hidden aspect-video">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />

        {/* Guide overlay — worksheet alignment helper */}
        {isActive && (
          <div className="absolute inset-0 pointer-events-none">
            {/* Outer corners */}
            <div className="absolute top-3 left-3 w-8 h-8 border-t-4 border-l-4 border-white/70 rounded-tl-lg" />
            <div className="absolute top-3 right-3 w-8 h-8 border-t-4 border-r-4 border-white/70 rounded-tr-lg" />
            <div className="absolute bottom-3 left-3 w-8 h-8 border-b-4 border-l-4 border-white/70 rounded-bl-lg" />
            <div className="absolute bottom-3 right-3 w-8 h-8 border-b-4 border-r-4 border-white/70 rounded-br-lg" />
            {/* Center alignment box */}
            <div className="absolute inset-[15%] border-2 border-dashed border-white/40 rounded-lg" />
            {/* Hint text */}
            <p className="absolute bottom-[18%] left-0 right-0 text-center text-white/60 text-xs">
              请将操作单置于框内
            </p>
          </div>
        )}

        {!isActive && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80">
            <div className="text-center space-y-4">
              <div className="text-4xl">📸</div>
              <p className="text-white text-sm">点击下方按钮启动摄像头</p>
              <Button onClick={() => startCamera(selectedDevice)}>
                📷 启动摄像头
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Hidden canvas for capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Controls */}
      <div className="flex items-center gap-3">
        {/* Device selector */}
        {devices.length > 1 && (
          <select
            value={selectedDevice}
            onChange={(e) => {
              setSelectedDevice(e.target.value);
              if (isActive) startCamera(e.target.value);
            }}
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm"
          >
            {devices.map((device) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label || `摄像头 ${device.deviceId.slice(0, 8)}`}
              </option>
            ))}
          </select>
        )}

        {isActive ? (
          <>
            <Button
              onClick={capture}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700"
            >
              📸 拍照
            </Button>
            <Button onClick={stopCamera} variant="outline">
              停止
            </Button>
          </>
        ) : (
          <Button
            onClick={() => startCamera(selectedDevice)}
            className="flex-1"
          >
            📷 打开摄像头
          </Button>
        )}

        {onClose && (
          <Button onClick={onClose} variant="ghost" size="sm">
            ✕
          </Button>
        )}
      </div>

      {/* Tips */}
      {isActive && (
        <div className="bg-amber-50 rounded-lg p-3 text-xs text-amber-700">
          💡 提示：将操作单平放在光线充足的桌面上，正对摄像头后点击拍照。
          确保四角都在画面内，避免阴影遮挡。
        </div>
      )}
    </div>
  );
}
