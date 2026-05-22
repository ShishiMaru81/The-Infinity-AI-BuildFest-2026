"use client";

import { useCallback, useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { VideoFeed, type DetectionResult } from "@/components/VideoFeed";
import { IncidentPanel } from "@/components/IncidentPanel";
import { IncidentLog } from "@/components/IncidentLog";
import { IncidentMap } from "@/components/IncidentMap";
import { AlertModal, type HazardAlertData } from "@/components/AlertModal";
import {
  fetchStats,
  fetchIncidents,
  fetchSettings,
  dispatchEmergency,
  updateSettings,
  type Incident,
  type Stats,
} from "@/lib/api";
import { getAppMode, setAppMode, initAppModeDefault, type AppMode } from "@/lib/appMode";

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [detection, setDetection] = useState<DetectionResult | null>(null);
  const [hazardAlert, setHazardAlert] = useState<HazardAlertData | null>(null);
  const [mapCoords, setMapCoords] = useState({ lat: 23.8103, lng: 90.4125 });
  const [appMode, setAppModeState] = useState<AppMode>("test");
  const [frameFps, setFrameFps] = useState(8);
  const [fallbackAddress, setFallbackAddress] = useState("Mirpur, Dhaka, Bangladesh");

  useEffect(() => {
    initAppModeDefault();
    setAppModeState(getAppMode());
    fetchSettings().then((s) => {
      setFrameFps(s.frame_fps || 8);
      setFallbackAddress(s.fallback_address || "Mirpur, Dhaka, Bangladesh");
      if (s.app_mode) setAppModeState(s.app_mode as AppMode);
    });
  }, []);

  const refresh = useCallback(async () => {
    const [s, inc] = await Promise.all([fetchStats(), fetchIncidents()]);
    setStats(s);
    setIncidents(inc);
    if (inc[0]) setMapCoords({ lat: inc[0].latitude, lng: inc[0].longitude });
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, [refresh]);

  const onDetection = useCallback(
    (result: DetectionResult) => {
      setDetection(result);
      if (result.incident_type !== "NORMAL") refresh();
    },
    [refresh]
  );

  const onHazardAlert = useCallback(
    (data: HazardAlertData) => {
      setHazardAlert(data);
      refresh();
    },
    [refresh]
  );

  const handleToggleMode = () => {
    if (appMode === "test") {
      const ok = window.confirm(
        "Enable REAL Mode?\n\nReal dispatches email 999@police.gov.bd and may place live calls/SMS. " +
          "False reports to 999 are a criminal offense under Bangladesh law. Only enable for authorized testing."
      );
      if (!ok) return;
      setAppMode("real");
      setAppModeState("real");
      updateSettings({ app_mode: "real" });
    } else {
      setAppMode("test");
      setAppModeState("test");
      updateSettings({ app_mode: "test" });
    }
  };

  const handleDispatch = async () => {
    if (!hazardAlert) return null;
    const res = await dispatchEmergency({
      incident_id: hazardAlert.incident_id,
      threat_type: hazardAlert.hazard_type,
      confidence: hazardAlert.confidence,
      location: hazardAlert.location,
      latitude: hazardAlert.latitude,
      longitude: hazardAlert.longitude,
      description: hazardAlert.description,
      snapshot_b64: hazardAlert.snapshot_b64,
      mode: appMode,
    });
    refresh();
    return res;
  };

  const handleFalseAlarm = () => {
    setHazardAlert(null);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <TopBar stats={stats} appMode={appMode} onToggleMode={handleToggleMode} />
      <main className="grid flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-12">
        <section className="lg:col-span-4">
          <VideoFeed
            onDetection={onDetection}
            onHazardAlert={onHazardAlert}
            fps={frameFps}
            location={fallbackAddress}
            lat={23.8223}
            lng={90.3654}
            alertActive={!!hazardAlert}
          />
        </section>
        <section className="lg:col-span-4">
          <IncidentPanel detection={detection} />
        </section>
        <section className="space-y-4 lg:col-span-4">
          <IncidentLog incidents={incidents} />
          <div className="rounded-lg border border-guardian-border bg-guardian-panel p-3">
            <h3 className="mb-2 text-sm font-semibold uppercase text-gray-400">Incident Map — Dhaka</h3>
            <IncidentMap
              incidents={incidents}
              selectedLat={mapCoords.lat}
              selectedLng={mapCoords.lng}
            />
          </div>
        </section>
      </main>

      <footer className="border-t border-guardian-border bg-guardian-panel px-6 py-3 text-center text-xs text-gray-500">
        <strong className="text-amber-500">Legal notice:</strong> Filing false reports to Bangladesh National
        Emergency Service (999) is a criminal offense. Use Demo/Test Mode for development. GuardianAI sends
        automated alerts only after confirmed hazard detection.
      </footer>

      <AlertModal
        alert={hazardAlert}
        appMode={appMode}
        onClose={() => setHazardAlert(null)}
        onConfirmDispatch={handleDispatch}
        onFalseAlarm={handleFalseAlarm}
      />
    </div>
  );
}
