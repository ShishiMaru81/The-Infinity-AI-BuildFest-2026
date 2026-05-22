"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import type { DetectionResult } from "@/components/VideoFeed";

export function IncidentPanel({ detection }: { detection: DetectionResult | null }) {
  if (!detection) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Incident Analysis</CardTitle>
        </CardHeader>
        <p className="text-sm text-gray-500">Awaiting frame analysis...</p>
      </Card>
    );
  }

  const scene = detection.scene_analysis || {};

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Incident Analysis</CardTitle>
        <Badge priority={detection.priority}>
          {detection.hazard_type
            ? detection.hazard_type
            : detection.incident_type.replace(/_/g, " ")}
        </Badge>
      </CardHeader>

      <div className="space-y-4">
        <div>
          <p className="text-xs uppercase text-gray-500">Threat Level</p>
          <p
            className={`text-lg font-bold ${
              detection.threat_level === "CRITICAL"
                ? "text-red-500"
                : detection.threat_level === "DANGER"
                  ? "text-orange-500"
                  : detection.threat_level === "SUSPICIOUS"
                    ? "text-yellow-500"
                    : "text-green-500"
            }`}
          >
            {detection.threat_level}
          </p>
        </div>

        <div>
          <p className="text-xs uppercase text-gray-500">AI Scene Description</p>
          <p className="text-sm text-gray-300">
            {(scene as { description?: string; happening?: string }).description ||
              (scene as { happening?: string }).happening ||
              detection.description}
          </p>
        </div>

        <div>
          <p className="text-xs uppercase text-gray-500">Recommended Action</p>
          <p className="text-sm font-medium text-blue-400">{detection.recommended_action}</p>
        </div>

        <div>
          <p className="mb-2 text-xs uppercase text-gray-500">Detected Objects</p>
          <ul className="max-h-40 space-y-1 overflow-y-auto text-sm">
            {detection.detected_objects?.length ? (
              detection.detected_objects.map((o, i) => (
                <li key={i} className="flex justify-between rounded bg-gray-800/50 px-2 py-1">
                  <span>{o.label}</span>
                  <span className="text-gray-400">{(o.confidence * 100).toFixed(0)}%</span>
                </li>
              ))
            ) : (
              <li className="text-gray-500">None detected</li>
            )}
          </ul>
        </div>
      </div>
    </Card>
  );
}
