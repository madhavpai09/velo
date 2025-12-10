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
  rating?: number;
}

export interface DriverForMap {
  driver_id: number;
  lat: number;
  lng: number;
  available: boolean;
  rating?: number;
}

// ... (skipping unchanged parts)

export interface AdminDriver {
  driver_id: number;
  name: string;
  phone_number: string | null;
  vehicle_type: string;
  vehicle_details: string | null;
  is_verified_safe: boolean;
  available: boolean;
  current_location: string;
  penalty_count: number;
  rating: number;
  rating_count: number;
  assigned_routes: number;
  created_at: string | null;
  updated_at: string | null;
}

export const createRideRequest = async (
  pickup: Location,
  dropoff: Location,
  userId: number = 7000,
  rideType: string = 'auto',
  fare?: number
): Promise<RideResponse> => {
  const response = await fetch(`${API_BASE}/ride-request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_location: `${pickup.lat},${pickup.lng}`,
      dest_location: `${dropoff.lat},${dropoff.lng}`,
      user_id: userId,
      ride_type: rideType,
      fare: fare,
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
  current_ride_id?: number;
}

export const registerDriver = async (
  driverId: string,
  name: string,
  location: Location,
  vehicleType: string = 'auto',
  phoneNumber: string = '',
  vehicleDetails: string = ''
): Promise<any> => {
  try {
    const response = await fetch('http://localhost:8000/driver/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        driver_id: driverId.startsWith('DRIVER-') ? driverId : `DRIVER-${driverId}`,
        name: name,
        port: parseInt(driverId.replace('DRIVER-', '')) || 9000,
        location: location,
        vehicle_type: vehicleType,
        phone_number: phoneNumber,
        vehicle_details: vehicleDetails
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error: any) {
    throw new Error(error.message || 'Network request failed');
  }
};

export const loginDriver = async (driverId: string): Promise<any> => {
  const numericId = parseInt(driverId.replace('DRIVER-', ''));
  const response = await fetch('http://localhost:8000/driver/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ driver_id: numericId })
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }
  return response.json();
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

export const getDriverPendingRide = async (driverId: number): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE}/driver/${driverId}/pending-ride`);
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
};

export const acceptRideRequest = async (driverId: number, matchId: number): Promise<any> => {
  const response = await fetch(`${API_BASE}/driver/${driverId}/accept-ride/${matchId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!response.ok) throw new Error('Failed to accept ride');
  return await response.json();
};

export const declineRideRequest = async (driverId: number, matchId: number) => {
  const response = await fetch(`${API_BASE}/driver/${driverId}/decline-ride/${matchId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) throw new Error('Failed to decline ride');
  return await response.json();
};

export const verifyRideOtp = async (rideId: number, otp: string): Promise<any> => {
  const response = await fetch(`${API_BASE}/ride/${rideId}/verify-otp?otp=${otp}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!response.ok) throw new Error('Invalid OTP');
  return await response.json();
};

export const completeRide = async (driverId: number, rideId: number): Promise<any> => {
  const response = await fetch(`${API_BASE}/driver/${driverId}/complete-ride/${rideId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) throw new Error('Failed to complete ride');
  return await response.json();
};

export const rateDriver = async (
  driverId: number,
  userId: number,
  rideId: number,
  rating: number,
  comment?: string
): Promise<any> => {
  const response = await fetch(`${API_BASE}/rate-driver`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      driver_id: driverId,
      user_id: userId,
      ride_id: rideId,
      rating: rating,
      comment: comment
    }),
  });
  if (!response.ok) throw new Error('Failed to submit rating');
  return await response.json();
};

// ==================== SCHOOL POOL PASS APIs ====================

export interface School {
  id: number;
  name: string;
  address: string;
  city: string;
  latitude?: string;
  longitude?: string;
}

export interface RouteStop {
  id: number;
  name: string;
  address: string;
  latitude: string;
  longitude: string;
  eta_offset: number;
}

export interface SchoolRoute {
  id: number;
  name: string;
  type: string;
  start_time: string;
  capacity: number;
  available_seats: number;
  stops: RouteStop[];
}

export interface SubscriptionCreate {
  user_id: number;
  student_id: number;
  route_id: number;
  stop_id: number;
  subscription_type: 'monthly' | 'quarterly' | 'annual';
  start_date: string;
}

export const getSchools = async (): Promise<{ schools: School[] }> => {
  const response = await fetch(`${API_BASE}/schools`);
  if (!response.ok) throw new Error('Failed to fetch schools');
  return await response.json();
};

export const getSchoolRoutes = async (schoolId: number): Promise<{ school: School, routes: SchoolRoute[] }> => {
  const response = await fetch(`${API_BASE}/schools/${schoolId}/routes`);
  if (!response.ok) throw new Error('Failed to fetch routes');
  return await response.json();
};

export const createSchoolPassSubscription = async (data: SubscriptionCreate): Promise<any> => {
  const response = await fetch(`${API_BASE}/subscriptions/school-pass`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create subscription');
  }
  return await response.json();
};

export const getSubscription = async (subscriptionId: number): Promise<any> => {
  const response = await fetch(`${API_BASE}/subscriptions/school-pass/${subscriptionId}`);
  if (!response.ok) throw new Error('Failed to fetch subscription');
  return await response.json();
};

export const getDriverSchoolRoutes = async (driverId: number): Promise<any> => {
  const response = await fetch(`${API_BASE}/drivers/${driverId}/school-routes`);
  if (!response.ok) throw new Error('Failed to fetch driver routes');
  return await response.json();
};

export const recordPickupEvent = async (driverId: number, data: any): Promise<any> => {
  const response = await fetch(`${API_BASE}/drivers/${driverId}/pickup-event`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to record event');
  return await response.json();
};

// ==================== ADMIN APIs ====================

export interface AdminDriver {
  driver_id: number;
  name: string;
  phone_number: string | null;
  vehicle_type: string;
  vehicle_details: string | null;
  is_verified_safe: boolean;
  available: boolean;
  current_location: string;
  penalty_count: number;
  assigned_routes: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface AdminDriversResponse {
  total_drivers: number;
  verified_drivers: number;
  drivers: AdminDriver[];
}

export const getAllDrivers = async (): Promise<AdminDriversResponse> => {
  const response = await fetch(`${API_BASE}/admin/drivers`);
  if (!response.ok) throw new Error('Failed to fetch drivers');
  return await response.json();
};

export const verifyDriver = async (driverId: number): Promise<any> => {
  const response = await fetch(`${API_BASE}/admin/drivers/${driverId}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!response.ok) throw new Error('Failed to verify driver');
  return await response.json();
};

export const unverifyDriver = async (driverId: number): Promise<any> => {
  const response = await fetch(`${API_BASE}/admin/drivers/${driverId}/unverify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!response.ok) throw new Error('Failed to unverify driver');
  return await response.json();
};

export const getVerifiedDrivers = async (): Promise<{ count: number, drivers: any[] }> => {
  const response = await fetch(`${API_BASE}/admin/drivers/verified`);
  if (!response.ok) throw new Error('Failed to fetch verified drivers');
  return await response.json();
};

export const getDriverDetails = async (driverId: number): Promise<any> => {
  const response = await fetch(`${API_BASE}/admin/drivers/${driverId}/details`);
  if (!response.ok) throw new Error('Failed to fetch driver details');
  return await response.json();
};

export const startSchoolRoute = async (driverId: number, routeId: number) => {
  const response = await fetch(`${API_BASE}/drivers/${driverId}/start-school-route?route_id=${routeId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) throw new Error('Failed to start route');
  return await response.json();
};