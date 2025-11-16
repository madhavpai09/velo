import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

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
  drivers?: Array<{ driver_id: number; lat: number; lng: number }>;
  driverLocation?: { lat: number; lng: number } | null;
  height?: string;
}

function LocationMarker({ 
  onSelect 
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

export default function MapView({ 
  center, 
  zoom = 13,
  onLocationSelect,
  pickupMarker,
  dropoffMarker,
  drivers = [],
  driverLocation = null,
  height = '100%'
}: MapViewProps) {
  return (
    <div style={{ height, width: '100%' }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {onLocationSelect && (
          <LocationMarker onSelect={onLocationSelect} />
        )}

        {/* Pickup Marker */}
        {pickupMarker && (
          <Marker 
            position={[pickupMarker.lat, pickupMarker.lng]}
            icon={pickupIcon}
          >
            <Popup>
              <div className="text-center">
                <div className="font-bold">📍 Pickup Location</div>
                <div className="text-xs text-gray-600">
                  {pickupMarker.lat.toFixed(5)}, {pickupMarker.lng.toFixed(5)}
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Dropoff Marker */}
        {dropoffMarker && (
          <Marker 
            position={[dropoffMarker.lat, dropoffMarker.lng]}
            icon={dropoffIcon}
          >
            <Popup>
              <div className="text-center">
                <div className="font-bold">🎯 Dropoff Location</div>
                <div className="text-xs text-gray-600">
                  {dropoffMarker.lat.toFixed(5)}, {dropoffMarker.lng.toFixed(5)}
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Driver's Own Location Marker */}
        {driverLocation && (
          <Marker 
            position={[driverLocation.lat, driverLocation.lng]}
            icon={myLocationIcon}
          >
            <Popup>
              <div className="text-center">
                <div className="font-bold">📍 Your Location</div>
                <div className="text-xs text-gray-600">
                  {driverLocation.lat.toFixed(5)}, {driverLocation.lng.toFixed(5)}
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Driver Markers */}
        {drivers.map((driver) => (
          <Marker 
            key={driver.driver_id} 
            position={[driver.lat, driver.lng]}
            icon={driverIcon}
          >
            <Popup>
              <div className="text-center">
                <div className="font-bold">🚗 Driver {driver.driver_id}</div>
                <div className="text-xs text-green-600">Available</div>
                <div className="text-xs text-gray-600">
                  {driver.lat.toFixed(5)}, {driver.lng.toFixed(5)}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
