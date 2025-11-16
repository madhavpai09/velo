import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import type { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { DriverForMap } from '../utils/api';

// Fix Leaflet default marker icon issue
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

// @ts-ignore - assign default icon for all markers (Leaflet typings don't like mutation)
L.Marker.prototype.options.icon = DefaultIcon;

// Custom icons for different marker types
const pickupIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const dropoffIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const driverIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const myLocationIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: iconShadow,
  iconSize: [30, 46],
  iconAnchor: [15, 46],
  popupAnchor: [1, -34],
});

interface MapViewProps {
  center: LatLngExpression;
  zoom?: number;
  onLocationSelect?: (lat: number, lng: number) => void;
  pickupMarker?: { lat: number; lng: number } | null;
  dropoffMarker?: { lat: number; lng: number } | null;
  // Accept the canonical DriverForMap type (imported) but also allow any for flexibility
  drivers?: DriverForMap[] | any[];
  driverLocation?: { lat: number; lng: number } | null;
  height?: string;
}

function LocationMarker({
  onSelect,
}: {
  onSelect: (lat: number, lng: number) => void;
}) {
  useMapEvents({
    click(e) {
      onSelect(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// Helper to extract id, lat and lng from various driver shapes
function extractDriverCoords(driver: any): { id: string | number | null; lat: number | null; lng: number | null } {
  if (!driver) return { id: null, lat: null, lng: null };

  // Common shapes handled below. Add more branches if your backend returns different shapes.
  const id = driver.driver_id ?? driver.id ?? driver._id ?? null;

  // direct lat/lng
  if (typeof driver.lat === 'number' && typeof driver.lng === 'number') {
    return { id, lat: driver.lat, lng: driver.lng };
  }

  // nested location: { location: { lat, lng } }
  if (driver.location && typeof driver.location.lat === 'number' && typeof driver.location.lng === 'number') {
    return { id, lat: driver.location.lat, lng: driver.location.lng };
  }

  // geo fields: { position: { latitude, longitude } }
  if (driver.position && typeof driver.position.latitude === 'number' && typeof driver.position.longitude === 'number') {
    return { id, lat: driver.position.latitude, lng: driver.position.longitude };
  }

  // coordinates arrays: { coords: [lng, lat] } or { coords: [lat, lng] }
  if (Array.isArray(driver.coords) && driver.coords.length >= 2) {
    // heuristic: if value looks like [lat, lng] (both numbers)
    const [a, b] = driver.coords;
    if (typeof a === 'number' && typeof b === 'number') {
      // assume [lat, lng]
      return { id, lat: a, lng: b };
    }
  }

  return { id, lat: null, lng: null };
}

export default function MapView({
  center,
  zoom = 13,
  onLocationSelect,
  pickupMarker,
  dropoffMarker,
  drivers = [],
  driverLocation = null,
  height = '100%',
}: MapViewProps) {
  return (
    <div style={{ height, width: '100%' }}>
      <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%' }} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {onLocationSelect && <LocationMarker onSelect={onLocationSelect} />}

        {/* Pickup Marker */}
        {pickupMarker && (
          <Marker position={[pickupMarker.lat, pickupMarker.lng]} icon={pickupIcon}>
            <Popup>
              <div className="text-center">
                <div className="font-bold">📍 Pickup Location</div>
                <div className="text-xs text-gray-600">{pickupMarker.lat.toFixed(5)}, {pickupMarker.lng.toFixed(5)}</div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Dropoff Marker */}
        {dropoffMarker && (
          <Marker position={[dropoffMarker.lat, dropoffMarker.lng]} icon={dropoffIcon}>
            <Popup>
              <div className="text-center">
                <div className="font-bold">🎯 Dropoff Location</div>
                <div className="text-xs text-gray-600">{dropoffMarker.lat.toFixed(5)}, {dropoffMarker.lng.toFixed(5)}</div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Driver's Own Location Marker */}
        {driverLocation && (
          <Marker position={[driverLocation.lat, driverLocation.lng]} icon={myLocationIcon}>
            <Popup>
              <div className="text-center">
                <div className="font-bold">📍 Your Location</div>
                <div className="text-xs text-gray-600">{driverLocation.lat.toFixed(5)}, {driverLocation.lng.toFixed(5)}</div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Driver Markers - robust extraction from DriverForMap or flexible shapes */}
        {Array.isArray(drivers) && drivers.map((driver) => {
          const { id, lat, lng } = extractDriverCoords(driver);
          if (id == null || lat == null || lng == null) return null; // skip invalid entries

          return (
            <Marker key={String(id)} position={[lat, lng]} icon={driverIcon}>
              <Popup>
                <div className="text-center">
                  <div className="font-bold">🚗 Driver {id}</div>
                  <div className="text-xs text-green-600">Available</div>
                  <div className="text-xs text-gray-600">{lat.toFixed(5)}, {lng.toFixed(5)}</div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
