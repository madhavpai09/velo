import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MapView from '../shared/MapView';
import RideForm from '../shared/RideForm';
import {
  createRideRequest,
  getAvailableDrivers,
  DriverForMap
} from '../utils/api';

interface AssignedDriver {
  ride_id?: number;
  driver_id: number;
  driver_name: string;
  driver_location: string;
  pickup_location: string;
  dropoff_location: string;
  status?: string;
  otp?: string;
}

export default function Home() {
  const navigate = useNavigate();
  const [pickupLocation, setPickupLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [dropoffLocation, setDropoffLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [drivers, setDrivers] = useState<DriverForMap[]>([]);
  const [rideId, setRideId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectionMode, setSelectionMode] = useState<'pickup' | 'dropoff'>('pickup');
  const [assignedDriver, setAssignedDriver] = useState<AssignedDriver | null>(null);
  const [waitingForDriver, setWaitingForDriver] = useState(false);
  const [activeSubscription, setActiveSubscription] = useState<any>(null);
  const [isUserOnline, setIsUserOnline] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const [showUserIdInput, setShowUserIdInput] = useState(true);

  const mapCenter: [number, number] = [12.9716, 77.5946];

  useEffect(() => {
    // Auto-generate User ID if not set
    if (!userId) {
      const randomId = Math.floor(Math.random() * 9000) + 1000;
      setUserId(randomId);
      setIsUserOnline(true);
    }
    return () => {
      setIsUserOnline(false);
    };
  }, []);

  useEffect(() => {
    fetchDrivers();
    const interval = setInterval(fetchDrivers, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!userId || !isUserOnline) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/user/${userId}/ride-status`);
        if (response.ok) {
          const data = await response.json();
          console.log('🚗 Poll Data:', data); // DEBUG LOG

          if (data.has_ride) {
            setWaitingForDriver(false);

            if (data.status === 'matched' || data.status === 'accepted' || data.status === 'in_progress') {
              setAssignedDriver({
                ride_id: data.ride_id,
                driver_id: data.driver_id,
                driver_name: `Driver ${data.driver_id}`,
                driver_location: data.driver_location || 'Unknown',
                pickup_location: data.pickup_location,
                dropoff_location: data.dropoff_location,
                status: data.status,
                otp: data.otp
              });

              if (data.ride_id) {
                setRideId(data.ride_id);
              }
            } else if (data.status === 'completed') {
              // Ride finished, clear state
              setAssignedDriver(null);
              setRideId(null);
              alert("Ride Completed! 🏁");
            }
          } else {
            // No active ride found
            if (assignedDriver) {
              setAssignedDriver(null);
              setRideId(null);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll ride status:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [userId, isUserOnline]);

  // NEW: Fetch active subscription
  useEffect(() => {
    if (userId) {
      console.log('Fetching subscriptions for user:', userId);
      fetch(`http://localhost:8000/api/user/${userId}/subscriptions`)
        .then(res => res.json())
        .then(data => {
          console.log('Subscription data:', data);
          if (data.subscriptions && data.subscriptions.length > 0) {
            const active = data.subscriptions.find((s: any) => s.status === 'active');
            console.log('Active subscription:', active);
            if (active) setActiveSubscription(active);
          }
        })
        .catch(err => console.error("Failed to fetch subs", err));
    }
  }, [userId]);

  const fetchDrivers = async () => {
    const driverData = await getAvailableDrivers();
    setDrivers(driverData);
  };

  const handleLocationSelect = (lat: number, lng: number) => {
    if (selectionMode === 'pickup') {
      setPickupLocation({ lat, lng });
      setSelectionMode('dropoff');
    } else {
      setDropoffLocation({ lat, lng });
    }
  };

  const handleRequestRide = async () => {
    if (!pickupLocation || !dropoffLocation) {
      alert('Please select both pickup and dropoff locations');
      return;
    }

    setLoading(true);
    try {
      const response = await createRideRequest(
        pickupLocation,
        dropoffLocation,
        userId || 7000
      );

      setRideId(response.data.id);
      setWaitingForDriver(true);
      console.log('✅ Ride created:', response.data);
    } catch (error: any) {
      console.error('❌ Failed to create ride:', error);
      alert(`Failed to create ride: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNewRide = () => {
    setRideId(null);
    setAssignedDriver(null);
    setWaitingForDriver(false);
    setPickupLocation(null);
    setDropoffLocation(null);
    setSelectionMode('pickup');
  };

  return (
    <div className="h-screen flex flex-col">
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl"><img src="/0796f710-7ecb-4a40-8176-2eba9ee3c5cd.png" alt="VELO" className="w-11 h-11" /></span>
              <div>
                <h1 className="text-3xl font-bold">VELO</h1>
                <p className="text-sm text-blue-200">Your ride, your way</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {isUserOnline && userId && (
                <div className="flex items-center gap-2 bg-white/20 px-4 py-2 rounded-lg">
                  <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div>
                  <span className="font-semibold">🟢 User {userId} Online</span>
                </div>
              )}
              <button
                onClick={() => navigate('/')}
                className="bg-white/20 text-white px-4 py-2 rounded-lg font-semibold hover:bg-white/30 transition-colors"
              >
                Switch Role
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-96">
          {/* Services Grid */}
          <div className="grid grid-cols-2 gap-4 px-6 mb-8">
            {activeSubscription && (
              <div className="col-span-2 bg-green-50 border border-green-200 p-4 rounded-xl flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-green-800 uppercase mb-1">Active Subscription</div>
                  <div className="font-bold">{activeSubscription.student_name}'s Ride</div>
                  <div className="text-sm text-gray-600">Driver ID: {activeSubscription.driver_id || 'Pending'}</div>
                  {activeSubscription.otp && (
                    <div className="mt-2 bg-white px-2 py-1 rounded border border-green-200 inline-block">
                      <span className="text-xs text-gray-500 mr-2">OTP:</span>
                      <span className="font-mono font-bold text-lg tracking-widest">{activeSubscription.otp}</span>
                    </div>
                  )}
                </div>
                <div className="text-2xl">🚌</div>
              </div>
            )}

            <div
              onClick={() => navigate('/ride')}
              className="bg-gray-100 p-4 rounded-xl aspect-square flex flex-col justify-between cursor-pointer hover:bg-gray-200 transition-colors"
            >
              <div className="self-end w-16">
                <img src="https://www.uber-assets.com/image/upload/f_auto,q_auto:eco,c_fill,w_188,h_188/v1548646935/assets/64/93c255-87c8-4e2e-9429-cf709bf1b838/original/3.png" alt="Ride" />
              </div>
              <span className="font-medium text-lg">Ride</span>
            </div>

            <div
              onClick={() => navigate('/school-pool')}
              className="bg-yellow-100 p-4 rounded-xl aspect-square flex flex-col justify-between cursor-pointer hover:bg-yellow-200 transition-colors border-2 border-transparent hover:border-yellow-400"
            >
              <div className="self-end w-16 text-4xl flex justify-end">
                🎒
              </div>
              <div>
                <span className="font-bold text-lg block">School Pool</span>
                <span className="text-xs text-yellow-800">For Students</span>
              </div>
            </div>

            <div className="bg-gray-100 p-4 rounded-xl aspect-square flex flex-col justify-between opacity-50">
              <div className="self-end w-16">
                {/* Placeholder for future service icon */}
              </div>
              <span className="font-medium text-lg">More Services</span>
            </div>
          </div>

          {showUserIdInput && (
            <div className="bg-white border-b p-4 shadow-sm">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your User ID
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={userId || ''}
                  onChange={(e) => setUserId(parseInt(e.target.value) || null)}
                  placeholder="e.g., 6000, 7000"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={() => {
                    if (userId) {
                      setShowUserIdInput(false);
                      setIsUserOnline(true);
                    } else {
                      alert('Please enter a valid User ID');
                    }
                  }}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                >
                  Set ID
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Auto-generated ID: {userId}. You can change it if needed.
              </p>
            </div>
          )}

          {!showUserIdInput && userId && (
            <div className="bg-blue-50 border-b p-3 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm text-gray-600">User ID: </span>
                  <span className="font-semibold text-blue-600">{userId}</span>
                </div>
                <button
                  onClick={() => {
                    setShowUserIdInput(true);
                    setIsUserOnline(false);
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Change
                </button>
              </div>
            </div>
          )}

          <RideForm
            pickupLocation={pickupLocation}
            dropoffLocation={dropoffLocation}
            onRequestRide={handleRequestRide}
            loading={loading}
            rideId={rideId}
            drivers={drivers}
            selectionMode={selectionMode}
            onSelectionModeChange={setSelectionMode}
            waitingForDriver={waitingForDriver}
            assignedDriver={assignedDriver}
            onNewRide={handleNewRide}
          />
        </div>

        <div className="flex-1 relative">
          {!assignedDriver && (
            <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3">
              <div className="text-xs text-gray-600 mb-1">Click mode:</div>
              <div className={`font-bold text-lg ${selectionMode === 'pickup' ? 'text-green-600' : 'text-red-600'
                }`}>
                {selectionMode === 'pickup' ? '📍 Pickup' : '🎯 Dropoff'}
              </div>
            </div>
          )}

          {assignedDriver && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-white rounded-lg shadow-2xl p-6 min-w-[400px] animate-bounce">
              <div className="text-center">
                <div className="text-6xl mb-3">🎉</div>
                <div className="text-2xl font-bold text-green-600 mb-2">Driver Assigned!</div>
                <div className="bg-blue-50 p-4 rounded-lg mb-4">
                  <div className="text-lg font-semibold text-gray-800 mb-2">
                    🚗 {assignedDriver.driver_name}
                  </div>
                  <div className="text-sm text-gray-600">
                    Driver ID: {assignedDriver.driver_id}
                  </div>
                  {assignedDriver.status && (
                    <div className="text-xs text-gray-500 mt-2">
                      Status: {assignedDriver.status}
                    </div>
                  )}
                  {assignedDriver.otp && (
                    <div className="mt-4 p-3 bg-yellow-100 rounded-lg border border-yellow-300">
                      <div className="text-xs text-yellow-800 uppercase font-bold">Share OTP with Driver</div>
                      <div className="text-3xl font-mono font-bold tracking-widest text-center mt-1">
                        {assignedDriver.otp}
                      </div>
                    </div>
                  )}
                </div>
                <button
                  onClick={handleNewRide}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700"
                >
                  Request Another Ride
                </button>
              </div>
            </div>
          )}

          <MapView
            center={mapCenter}
            zoom={13}
            onLocationSelect={!assignedDriver ? handleLocationSelect : undefined}
            pickupMarker={pickupLocation}
            dropoffMarker={dropoffLocation}
            drivers={drivers}
          />
        </div>
      </div>
    </div>
  );
}