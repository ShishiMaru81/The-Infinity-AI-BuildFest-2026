"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ShieldAlert, Phone, Mail, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import type { DispatchResult } from "@/lib/api";

export interface HazardAlertData {
  incident_id?: number;
  hazard_type: string;
  incident_type: string;
  priority: string;
  confidence: number;
  description: string;
  timestamp: number;
  snapshot_b64?: string;
  location: string;
  latitude: number;
  longitude: number;
}

function playAlertBeep() {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    gain.gain.value = 0.15;
    osc.start();
    setTimeout(() => {
      osc.stop();
      ctx.close();
    }, 200);
    setTimeout(() => {
      const ctx2 = new AudioContext();
      const o2 = ctx2.createOscillator();
      const g2 = ctx2.createGain();
      o2.connect(g2);
      g2.connect(ctx2.destination);
      o2.frequency.value = 660;
      g2.gain.value = 0.15;
      o2.start();
      setTimeout(() => {
        o2.stop();
        ctx2.close();
      }, 200);
    }, 250);
  } catch {
    /* ignore if AudioContext blocked */
  }
}

export function AlertModal({
  alert,
  appMode,
  onClose,
  onConfirmDispatch,
  onFalseAlarm,
}: {
  alert: HazardAlertData | null;
  appMode: "test" | "real";
  onClose: () => void;
  onConfirmDispatch: () => Promise<DispatchResult | null>;
  onFalseAlarm: () => void;
}) {
  const [countdown, setCountdown] = useState(10);
  const [dispatching, setDispatching] = useState(false);
  const [result, setResult] = useState<DispatchResult | null>(null);
  const dispatchedRef = useRef(false);

  const runDispatch = useCallback(async () => {
    if (dispatchedRef.current || dispatching) return;
    dispatchedRef.current = true;
    setDispatching(true);
    const res = await onConfirmDispatch();
    setResult(res);
    setDispatching(false);
  }, [dispatching, onConfirmDispatch]);

  useEffect(() => {
    if (!alert) {
      setCountdown(10);
      setResult(null);
      dispatchedRef.current = false;
      return;
    }
    playAlertBeep();
    setCountdown(10);
    setResult(null);
    dispatchedRef.current = false;
  }, [alert]);

  useEffect(() => {
    if (!alert || result || dispatching) return;
    if (countdown <= 0) {
      runDispatch();
      return;
    }
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [alert, countdown, result, dispatching, runDispatch]);

  if (!alert) return null;

  const snapshotSrc = alert.snapshot_b64
    ? `data:image/jpeg;base64,${alert.snapshot_b64}`
    : null;
  const ts = new Date(alert.timestamp * 1000).toLocaleString();

  const emailOk = result?.email?.status === "sent";
  const smsOk = ["sent", "mock_sent", "skipped_test_mode"].includes(result?.sms?.status || "");
  const callOk = ["called", "mock_called", "skipped_test_mode"].includes(result?.call?.status || "");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-flash bg-red-950/80 backdrop-blur-sm">
      <div className="mx-4 max-w-lg rounded-xl border-2 border-red-500 bg-gray-900 p-8 shadow-2xl animate-pulse-alert max-h-[90vh] overflow-y-auto">
        <div className="mb-4 flex items-center gap-3 text-red-500">
          <ShieldAlert className="h-10 w-10" />
          <h2 className="text-xl font-bold">⚠ Hazard detected — contacting 999</h2>
        </div>

        <p className="text-lg font-semibold text-white capitalize">
          {alert.hazard_type} detected ({(alert.confidence * 100).toFixed(0)}% confidence)
        </p>
        <p className="mt-1 text-xs text-gray-400">{ts} · {alert.location}</p>
        <p className="mt-2 text-sm text-gray-300">{alert.description}</p>

        {snapshotSrc && (
          <img
            src={snapshotSrc}
            alt="Detection snapshot"
            className="mt-4 w-full rounded-lg border border-gray-700"
          />
        )}

        {!result && (
          <>
            <div className="mt-4">
              <div className="flex justify-between text-xs text-amber-400">
                <span>Auto-dispatch in</span>
                <span>{countdown}s</span>
              </div>
              <Progress value={(10 - countdown) * 10} className="mt-1" />
            </div>
            <p className="mt-2 text-xs text-gray-500">
              Mode: <strong className={appMode === "real" ? "text-red-400" : "text-green-400"}>{appMode.toUpperCase()}</strong>
              {appMode === "test" ? " — emails go to your test address only." : " — LIVE dispatch to emergency services."}
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button variant="destructive" disabled={dispatching} onClick={runDispatch}>
                {dispatching ? "Dispatching..." : "Confirm & Dispatch"}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  dispatchedRef.current = true;
                  onFalseAlarm();
                }}
              >
                False Alarm
              </Button>
            </div>
          </>
        )}

        {result && (
          <div className="mt-6 space-y-2 rounded-lg border border-gray-700 bg-gray-800/50 p-4 text-sm">
            <p className="font-semibold text-white">Dispatch status</p>
            <div className="flex items-center gap-2 text-gray-300">
              <Mail className="h-4 w-4" />
              Email {emailOk ? "sent ✓" : result.email?.status || "pending"}
              {result.email_to && <span className="text-xs text-gray-500">→ {result.email_to}</span>}
            </div>
            <div className="flex items-center gap-2 text-gray-300">
              <Phone className="h-4 w-4" />
              Call {callOk ? "placed ✓" : result.call?.status || "skipped"}
            </div>
            <div className="flex items-center gap-2 text-gray-300">
              <MessageSquare className="h-4 w-4" />
              SMS {smsOk ? "sent ✓" : result.sms?.status || "skipped"}
            </div>
            <p className="text-xs text-amber-400/80">Awaiting confirmation from emergency services</p>
            {result.status === "blocked" && (
              <p className="text-red-400">{result.reason}</p>
            )}
            <Button className="mt-2" variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
