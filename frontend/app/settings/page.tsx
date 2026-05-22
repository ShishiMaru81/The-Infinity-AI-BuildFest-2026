"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchSettings, updateSettings } from "@/lib/api";
import { getAppMode, setAppMode, type AppMode } from "@/lib/appMode";

export default function SettingsPage() {
  const [alertMode, setAlertMode] = useState("mock");
  const [policeNumber, setPoliceNumber] = useState("999");
  const [appMode, setAppModeState] = useState<AppMode>("test");
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.6);
  const [consecutiveFrames, setConsecutiveFrames] = useState(5);
  const [frameFps, setFrameFps] = useState(8);
  const [cooldownSec, setCooldownSec] = useState(300);
  const [testEmail, setTestEmail] = useState("");
  const [fallbackAddress, setFallbackAddress] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    initLocalMode();
    fetchSettings().then((s) => {
      setAlertMode(s.alert_mode || "mock");
      setPoliceNumber(s.police_number || "999");
      setAppModeState((s.app_mode as AppMode) || getAppMode());
      setConfidenceThreshold(s.detection_confidence_threshold ?? 0.6);
      setConsecutiveFrames(s.detection_consecutive_frames ?? 5);
      setFrameFps(s.frame_fps ?? 8);
      setCooldownSec(s.real_dispatch_cooldown_sec ?? 300);
      setTestEmail(s.test_email || "");
      setFallbackAddress(s.fallback_address || "");
    });
  }, []);

  const initLocalMode = () => {
    const m = getAppMode();
    setAppModeState(m);
  };

  const onAppModeChange = (mode: AppMode) => {
    if (mode === "real") {
      const ok = window.confirm(
        "Switch to REAL Mode? Live dispatches target emergency services. Misuse may be prosecuted under Bangladesh law."
      );
      if (!ok) return;
    }
    setAppMode(mode);
    setAppModeState(mode);
  };

  const save = async () => {
    await updateSettings({
      alert_mode: alertMode,
      police_number: policeNumber,
      app_mode: appMode,
      detection_confidence_threshold: confidenceThreshold,
      detection_consecutive_frames: consecutiveFrames,
      frame_fps: frameFps,
      real_dispatch_cooldown_sec: cooldownSec,
      test_email: testEmail,
      fallback_address: fallbackAddress,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link href="/" className="text-sm text-blue-400 hover:underline">
        ← Back to Dashboard
      </Link>
      <h1 className="mt-4 text-2xl font-bold">GuardianAI Settings</h1>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Safety & Dispatch</CardTitle>
        </CardHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-gray-400">App Mode (default: Test)</label>
            <select
              className="mt-1 w-full rounded border border-gray-700 bg-gray-900 px-3 py-2"
              value={appMode}
              onChange={(e) => onAppModeChange(e.target.value as AppMode)}
            >
              <option value="test">Demo / Test — emails to test address only</option>
              <option value="real">Real — dispatches to 999@police.gov.bd</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-400">Test email recipient</label>
            <input
              className="mt-1 w-full rounded border border-gray-700 bg-gray-900 px-3 py-2"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              placeholder="your.email@example.com"
            />
          </div>
          <div>
            <label className="text-sm text-gray-400">Fallback address (if GPS denied)</label>
            <input
              className="mt-1 w-full rounded border border-gray-700 bg-gray-900 px-3 py-2"
              value={fallbackAddress}
              onChange={(e) => setFallbackAddress(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm text-gray-400">Real dispatch cooldown (seconds)</label>
            <input
              type="number"
              className="mt-1 w-full rounded border border-gray-700 bg-gray-900 px-3 py-2"
              value={cooldownSec}
              onChange={(e) => setCooldownSec(Number(e.target.value))}
            />
          </div>
        </div>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Detection</CardTitle>
        </CardHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-gray-400">
              Confidence threshold ({confidenceThreshold})
            </label>
            <input
              type="range"
              min={0.3}
              max={0.95}
              step={0.05}
              className="mt-1 w-full"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
            />
          </div>
          <div>
            <label className="text-sm text-gray-400">Consecutive frames required</label>
            <input
              type="number"
              min={1}
              max={30}
              className="mt-1 w-full rounded border border-gray-700 bg-gray-900 px-3 py-2"
              value={consecutiveFrames}
              onChange={(e) => setConsecutiveFrames(Number(e.target.value))}
            />
          </div>
          <div>
            <label className="text-sm text-gray-400">Inference FPS (5–10 recommended)</label>
            <input
              type="number"
              min={1}
              max={15}
              className="mt-1 w-full rounded border border-gray-700 bg-gray-900 px-3 py-2"
              value={frameFps}
              onChange={(e) => setFrameFps(Number(e.target.value))}
            />
          </div>
        </div>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Legacy Twilio Alert Mode</CardTitle>
        </CardHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-gray-400">Alert Mode</label>
            <select
              className="mt-1 w-full rounded border border-gray-700 bg-gray-900 px-3 py-2"
              value={alertMode}
              onChange={(e) => setAlertMode(e.target.value)}
            >
              <option value="mock">Mock (console)</option>
              <option value="live">Live (Twilio)</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-400">Police / Emergency Number</label>
            <input
              className="mt-1 w-full rounded border border-gray-700 bg-gray-900 px-3 py-2"
              value={policeNumber}
              onChange={(e) => setPoliceNumber(e.target.value)}
            />
          </div>
          <p className="text-xs text-amber-600/90">
            False reports to 999 are a criminal offense under Bangladesh law. Configure SMTP and Twilio in
            backend <code className="text-gray-400">.env</code>.
          </p>
          <Button onClick={save}>{saved ? "Saved!" : "Save Settings"}</Button>
        </div>
      </Card>
    </div>
  );
}
