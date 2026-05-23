"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Camera, Upload, Radio, Satellite } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { WS_URL } from "@/lib/utils";
import { uploadVideo, getVideoJob } from "@/lib/api";
import type { HazardAlertData } from "@/components/AlertModal";

export interface DetectionResult {
  incident_type: string;
  priority: string;
  threat_level: string;
  confidence: number;
  description: string;
  detected_objects: { label: string; confidence: number; bbox: number[] }[];
  scene_analysis: Record<string, unknown>;
  annotated_frame?: string;
  recommended_action: string;
  hazard_type?: string | null;
  hazard_confirmed?: boolean;
  hazard_streak?: number;
}

interface VideoFeedProps {
  onDetection: (result: DetectionResult) => void;
  onHazardAlert: (data: HazardAlertData) => void;
  fps?: number;
  location?: string;
  lat?: number;
  lng?: number;
  alertActive?: boolean;
}

type InputMode = "webcam" | "upload" | "rtsp" | "drone";

export function VideoFeed({
  onDetection,
  onHazardAlert,
  fps = 8,
  location: locationProp,
  lat: latProp,
  lng: lngProp,
  alertActive = false,
}: VideoFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [mode, setMode] = useState<InputMode>("webcam");
  const [active, setActive] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [rtspUrl, setRtspUrl] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState("");
  const [hazardStreak, setHazardStreak] = useState(0);
  const [location, setLocation] = useState(locationProp || "Dhaka, Bangladesh");
  const [lat, setLat] = useState(latProp ?? 23.8223);
  const [lng, setLng] = useState(lngProp ?? 90.3654);

  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude);
        setLng(pos.coords.longitude);
        setLocation(`GPS ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`);
      },
      () => {
        if (locationProp) setLocation(locationProp);
      },
      { enableHighAccuracy: false, timeout: 8000 }
    );
  }, [locationProp]);

  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return wsRef.current;
    const ws = new WebSocket(WS_URL);
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === "detection") {
        onDetection(data);
        setConfidence(data.confidence * 100);
        if (data.hazard_streak != null) setHazardStreak(data.hazard_streak);
        if (data.annotated_frame) setPreview(`data:image/jpeg;base64,${data.annotated_frame}`);
      }
      if (data.type === "hazard_alert") {
        onHazardAlert({
          incident_id: data.incident_id,
          hazard_type: data.hazard_type,
          incident_type: data.incident_type,
          priority: data.priority,
          confidence: data.confidence,
          description: data.description,
          timestamp: data.timestamp,
          snapshot_b64: data.snapshot_b64,
          location: data.location,
          latitude: data.latitude,
          longitude: data.longitude,
        });
      }
    };
    wsRef.current = ws;
    return ws;
  }, [onDetection, onHazardAlert]);

  const sendFrame = useCallback(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video || video.readyState < 2) return;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const b64 = canvas.toDataURL("image/jpeg", 0.7).split(",")[1];
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(
        JSON.stringify({
          type: "frame",
          frame: b64,
          lat,
          lng,
          location,
          source: mode,
        })
      );
    }
  }, [lat, lng, location, mode]);

  const startWebcam = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
    }
    const ws = connectWs();
    ws.onopen = () => {
      setActive(true);
      intervalRef.current = setInterval(sendFrame, 1000 / fps);
    };
  };

  const stopAll = () => {
    setActive(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    wsRef.current?.close();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadStatus("Uploading...");
    const { job_id } = await uploadVideo(file, fps, lat, lng);
    setUploadStatus("Analyzing video...");
    const poll = setInterval(async () => {
      const job = await getVideoJob(job_id);
      setUploadProgress(job.progress || 0);
      if (job.status === "completed") {
        clearInterval(poll);
        setUploadStatus(`Done: ${job.summary?.total_incidents || 0} incidents found`);
        job.timeline?.forEach((ev: DetectionResult & { timestamp_sec: number }) => {
          onDetection({
            incident_type: ev.incident_type,
            priority: ev.priority,
            threat_level: ev.threat_level,
            confidence: ev.confidence,
            description: ev.description,
            detected_objects: [],
            scene_analysis: {},
            recommended_action: "none",
          });
        });
      }
    }, 2000);
  };

  const startRtsp = () => {
    setMode("rtsp");
    connectWs();
    setActive(true);
  };

  useEffect(() => () => stopAll(), []);

  useEffect(() => {
    if (active && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = setInterval(sendFrame, 1000 / fps);
    }
  }, [fps, active, sendFrame]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Live Surveillance Feed</CardTitle>
        <div className="flex gap-1">
          <Button size="sm" variant={mode === "webcam" ? "default" : "outline"} onClick={() => setMode("webcam")}>
            <Camera className="h-4 w-4" />
          </Button>
          <Button size="sm" variant={mode === "upload" ? "default" : "outline"} onClick={() => setMode("upload")}>
            <Upload className="h-4 w-4" />
          </Button>
          <Button size="sm" variant={mode === "rtsp" ? "default" : "outline"} onClick={() => setMode("rtsp")}>
            <Radio className="h-4 w-4" />
          </Button>
          <Button size="sm" variant={mode === "drone" ? "default" : "outline"} onClick={() => setMode("drone")}>
            <Satellite className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <div
        className={`relative aspect-video overflow-hidden rounded-lg bg-black ${
          alertActive ? "ring-4 ring-red-500 animate-pulse-alert" : ""
        }`}
      >
        <video ref={videoRef} className="h-full w-full object-contain" playsInline muted />
        {preview && active && (
          <img src={preview} alt="Detection overlay" className="absolute inset-0 h-full w-full object-contain" />
        )}
        {!active && mode !== "upload" && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500">No active feed</div>
        )}
      </div>
      <canvas ref={canvasRef} className="hidden" />

      <div className="mt-3 space-y-2">
        <div className="flex justify-between text-xs text-gray-400">
          <span>Detection confidence</span>
          <span>{confidence.toFixed(0)}%</span>
        </div>
        <Progress value={confidence} />
        <p className="text-[10px] text-gray-500">
          Inference ~{fps} FPS · knife, gun, fire, lighter
          {hazardStreak > 0 && (
            <span className="ml-2 text-amber-400">confirming… {hazardStreak} frame(s)</span>
          )}
        </p>
      </div>

      {mode === "webcam" && (
        <div className="mt-3 flex gap-2">
          {!active ? (
            <Button onClick={startWebcam}>Start Webcam</Button>
          ) : (
            <Button variant="destructive" onClick={stopAll}>
              Stop
            </Button>
          )}
        </div>
      )}

      {mode === "upload" && (
        <div className="mt-3">
          <input type="file" accept="video/*" onChange={handleFileUpload} className="text-sm text-gray-400" />
          {uploadStatus && <p className="mt-2 text-xs text-gray-400">{uploadStatus}</p>}
          {uploadProgress > 0 && <Progress value={uploadProgress} className="mt-2" />}
        </div>
      )}

      {mode === "rtsp" && (
        <div className="mt-3 space-y-2">
          <input
            className="w-full rounded border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
            placeholder="rtsp://..."
            value={rtspUrl}
            onChange={(e) => setRtspUrl(e.target.value)}
          />
          <Button onClick={startRtsp}>Connect RTSP</Button>
        </div>
      )}

      {mode === "drone" && (
        <div className="mt-3">
          <p className="mb-2 text-xs text-gray-500">Upload drone/satellite recording</p>
          <input type="file" accept="video/*" onChange={handleFileUpload} />
        </div>
      )}
    </Card>
  );
}
