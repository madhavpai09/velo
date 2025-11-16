const API_BASE_URL = 'http://localhost:8000/api';

export interface DriverForMap {
  id: number;
  driver_id: number;
  current_location: string;
  available: boolean;
}

export interface DriverStatus {
  id: number;
  driver_id: number;
  current_location: string | null;
  available: boolean;
}

export async function createRideRequest(
  pickupLocation: { lat: number; lng: number },
  dropoffLocation: { lat: number; lng: number },
  userId: number,
  pickupAddress?: string,
  dropoffAddress?: string
) {
  const response = await fetch(`${API_BASE_URL}/ride-request`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      source_location: pickupAddress || `${pickupLocation.lat},${pickupLocation.lng}`,
      dest_location: dropoffAddress || `${dropoffLocation.lat},${dropoffLocation.lng}`,
      user_id: userId,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to create ride request');
  }

  return await response.json();
}

export async function getAvailableDrivers(): Promise<DriverForMap[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/drivers/available`);
    if (!response.ok) {
      return [];
    }
    const data = await response.json();
    return data.drivers || [];
  } catch (error) {
    console.error('Failed to fetch drivers:', error);
    return [];
  }
}

export async function getAllRideRequests() {
  try {
    const response = await fetch(`${API_BASE_URL}/ride-requests`);
    if (!response.ok) {
      return [];
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch ride requests:', error);
    return [];
  }
}

export async function getRideStatus(userId: number) {
  try {
    const response = await fetch(`${API_BASE_URL}/user/${userId}/ride-status`);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch ride status:', error);
    return null;
  }
}

export async function getDriverStatus(driverId: number): Promise<DriverStatus | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/drivers/${driverId}`);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch driver status:', error);
    return null;
  }
}

export async function registerDriver(
  driverId: string,
  driverName: string,
  location: { lat: number; lng: number }
) {
  const response = await fetch('http://localhost:8000/driver/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      driver_id: driverId,
      name: driverName,
      port: parseInt(driverId.replace('DRIVER-', '')) || parseInt(driverId),
      location: location,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to register driver');
  }

  return await response.json();
}

export async function setDriverAvailability(driverId: string, isAvailable: boolean) {
  const response = await fetch(
    `http://localhost:8000/driver/set-availability?driver_id=${encodeURIComponent(driverId)}&is_available=${isAvailable}`,
    {
      method: 'POST',
    }
  );

  if (!response.ok) {
    throw new Error('Failed to set driver availability');
  }

  return await response.json();
}

export async function updateDriverLocation(driverId: string, location: { lat: number; lng: number }) {
  const response = await fetch(
    `http://localhost:8000/driver/update-location?driver_id=${encodeURIComponent(driverId)}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(location),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to update driver location');
  }

  return await response.json();
}