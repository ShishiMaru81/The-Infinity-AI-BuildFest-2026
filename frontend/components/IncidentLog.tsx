"use client";

import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Incident } from "@/lib/api";

const alertColors: Record<string, string> = {
  SENT: "text-green-400",
  PENDING: "text-yellow-400",
  ACKNOWLEDGED: "text-blue-400",
};

export function IncidentLog({ incidents }: { incidents: Incident[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Incident Log</CardTitle>
      </CardHeader>
      <div className="max-h-64 overflow-y-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-guardian-panel text-gray-500">
            <tr>
              <th className="p-2">Time</th>
              <th className="p-2">Type</th>
              <th className="p-2">Location</th>
              <th className="p-2">Alert</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((inc) => (
              <tr key={inc.id} className="border-t border-gray-800 hover:bg-gray-800/30">
                <td className="p-2 whitespace-nowrap">
                  {new Date(inc.created_at).toLocaleTimeString()}
                </td>
                <td className="p-2">
                  <Badge priority={inc.priority} className="text-[10px]">
                    {inc.incident_type.replace(/_/g, " ")}
                  </Badge>
                </td>
                <td className="p-2 max-w-[100px] truncate">{inc.location}</td>
                <td className={`p-2 font-medium ${alertColors[inc.alert_status] || ""}`}>
                  {inc.alert_status}
                </td>
              </tr>
            ))}
            {!incidents.length && (
              <tr>
                <td colSpan={4} className="p-4 text-center text-gray-500">
                  No incidents logged yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
