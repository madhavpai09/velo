// src/utils/api.ts - NO AXIOS, using native fetch

const API_BASE = 'http://localhost:8000/api';

export interface Location {
  lat: number;
  lng: number;
}

export interface RideResponse {
  message: string;
  data: {
    id: number;
    source_location: string;
    dest_location: string;
    user_id: number;
    status: string;
    created_at: string;
  };
}

export interface Driver {
  id: number;
  driver_id: number;
  current_location: string;
  available: boolean;
}

export interface DriverForMap {
  driver_id: number;
  lat: number;
  lng: number;
  available: boolean;
}

export const createRideRequest = async (
  pickup: Location,
  dropoff: Location,
  userId: number = 7000
): Promise<RideResponse> => {
  const response = await fetch(`${API_BASE}/ride-request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_location: `${pickup.lat},${pickup.lng}`,
      dest_location: `${dropoff.lat},${dropoff.lng}`,
      user_id: userId,
    }),
  });
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
};

export const getAvailableDrivers = async (): Promise<DriverForMap[]> => {
  try {
    const response = await fetch(`${API_BASE}/drivers/available`);
    if (!response.ok) return [];
    const data = await response.json();
    const drivers = data.drivers || [];
    return drivers.map((driver: Driver) => {
      const [lat, lng] = driver.current_location.split(',').map(Number);
      return { driver_id: driver.driver_id, lat, lng, available: driver.available };
    });
  } catch {
    return [];
  }
};

export const getRideStatus = async (rideId: number) => {
  const response = await fetch(`${API_BASE}/ride-request/${rideId}`);
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
};

export const getAllRideRequests = async () => {
  try {
    const response = await fetch(`${API_BASE}/ride-requests`);
    if (!response.ok) return [];
    return await response.json();
  } catch {
    return [];
  }
};

// Driver API functions
export interface DriverStatus {
  id: number;
  driver_id: number;
  current_location: string;
  available: boolean;
}

export const registerDriver = async (
  driverId: string,
  name: string,
  location: Location
): Promise<any> => {
  const response = await fetch('http://localhost:8000/driver/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      driver_id: driverId,
      name: name,
      port: parseInt(driverId.replace('DRIVER-', '')) || 9000,
      location: location,
    }),
  });
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
};

export const setDriverAvailability = async (
  driverId: string,
  isAvailable: boolean
): Promise<any> => {
  const response = await fetch(
    `http://localhost:8000/driver/set-availability?driver_id=${driverId}&is_available=${isAvailable}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }
  );
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
};

export const updateDriverLocation = async (
  driverId: string,
  location: Location
): Promise<any> => {
  const response = await fetch(
    `http://localhost:8000/driver/update-location?driver_id=${driverId}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(location),
    }
  );
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
};

export const getDriverStatus = async (driverId: number): Promise<DriverStatus | null> => {
  try {
    const response = await fetch(`${API_BASE}/drivers/${driverId}`);
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
};