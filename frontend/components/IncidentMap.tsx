"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import type { Incident } from "@/lib/api";

const MapContainer = dynamic(
  () => import("react-leaflet").then((m) => m.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(() => import("react-leaflet").then((m) => m.TileLayer), { ssr: false });
const Marker = dynamic(() => import("react-leaflet").then((m) => m.Marker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then((m) => m.Popup), { ssr: false });

export function IncidentMap({
  incidents,
  selectedLat,
  selectedLng,
}: {
  incidents: Incident[];
  selectedLat?: number;
  selectedLng?: number;
}) {
  const [ready, setReady] = useState(false);
  const center: [number, number] = [
    selectedLat ?? 23.8103,
    selectedLng ?? 90.4125,
  ];

  useEffect(() => {
    import("leaflet/dist/leaflet.css");
    import("leaflet").then((L) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
        iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
        shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
      });
      setReady(true);
    });
  }, []);

  if (!ready) {
    return <div className="h-48 animate-pulse rounded-lg bg-gray-800" />;
  }

  return (
    <div className="h-48 w-full overflow-hidden rounded-lg">
      <MapContainer center={center} zoom={12} className="h-full w-full" scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {incidents.slice(0, 20).map((inc) => (
          <Marker key={inc.id} position={[inc.latitude, inc.longitude]}>
            <Popup>
              <strong>{inc.incident_type}</strong>
              <br />
              {inc.location}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
