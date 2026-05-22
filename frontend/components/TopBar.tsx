"use client";

import { Shield, Activity, AlertTriangle, FlaskConical } from "lucide-react";
import type { Stats } from "@/lib/api";
import Link from "next/link";

export function TopBar({
  stats,
  appMode,
  onToggleMode,
}: {
  stats: Stats | null;
  appMode: "test" | "real";
  onToggleMode: () => void;
}) {
  return (
    <header className="flex items-center justify-between border-b border-guardian-border bg-guardian-panel px-6 py-3">
      <div className="flex items-center gap-3">
        <Shield className="h-8 w-8 text-blue-500" />
        <div>
          <h1 className="text-xl font-bold tracking-tight">GuardianAI</h1>
          <p className="text-xs text-gray-500">Bangladesh Public Safety Surveillance</p>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <button
          type="button"
          onClick={onToggleMode}
          className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${
            appMode === "test"
              ? "border-green-600/50 bg-green-900/30 text-green-400"
              : "border-red-600/50 bg-red-900/30 text-red-400"
          }`}
        >
          <FlaskConical className="h-3.5 w-3.5" />
          {appMode === "test" ? "Demo / Test Mode" : "REAL Mode"}
        </button>
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              stats?.system_status === "OPERATIONAL" ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm">{stats?.system_status || "CONNECTING"}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Activity className="h-4 w-4 text-blue-400" />
          <span>{stats?.active_cameras ?? 0} cameras active</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
          <span>{stats?.incidents_today ?? 0} incidents today</span>
        </div>
        <Link href="/settings" className="text-sm text-blue-400 hover:underline">
          Settings
        </Link>
      </div>
    </header>
  );
}
