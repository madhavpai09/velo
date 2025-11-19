// frontend/src/pages/Home.tsx - Updated with OTP display
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
  otp?: string;  // NEW: OTP from backend
  otp_verified?: boolean;  // NEW: OTP verification status
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
  const [isUserOnline, setIsUserOnline] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const [showUserIdInput, setShowUserIdInput] = useState(true);
  const [showOtp, setShowOtp] = useState(false);  // NEW: Show OTP to user

  const mapCenter: [number, number] = [12.9716, 77.5946];

  useEffect(() => {
    setIsUserOnline(true);
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
                otp: data.otp,  // NEW: Get OTP from backend
                otp_verified: data.otp_verified  // NEW: Check if OTP verified
              });
              
              // NEW: Show OTP when driver accepts (status = 'accepted')
              if (data.status === 'accepted' && data.otp && !data.otp_verified) {
                setShowOtp(true);
              }
              
              // NEW: Hide OTP when ride starts (status = 'in_progress')
              if (data.status === 'in_progress' && data.otp_verified) {
                setShowOtp(false);
              }
              
              if (data.ride_id) {
                setRideId(data.ride_id);
              }
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll ride status:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [userId, isUserOnline]);

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
    setShowOtp(false);  // NEW: Reset OTP display
  };

  return (
    <div className="h-screen flex flex-col">
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl">🚗</span>
              <div>
                <h1 className="text-3xl font-bold">VELOcabs</h1>
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
                onClick={() => navigate('/ride')}
                className="bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
              >
                View Rides
              </button>
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
                Each user needs a unique ID (e.g., 6000, 7000, 8000)
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
          {/* NEW: OTP Display Modal */}
          {showOtp && assignedDriver?.otp && (
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[1001] bg-white rounded-2xl shadow-2xl p-8 min-w-[400px] border-4 border-green-500 animate-pulse">
              <div className="text-center">
                <div className="text-6xl mb-4">🔐</div>
                <div className="text-2xl font-bold text-gray-800 mb-3">Your OTP</div>
                <div className="text-sm text-gray-600 mb-6">
                  Share this with your driver to start the ride
                </div>
                <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-6 rounded-xl mb-6">
                  <div className="text-6xl font-bold tracking-widest">
                    {assignedDriver.otp}
                  </div>
                </div>
                <div className="text-xs text-gray-500 mb-4">
                  Driver {assignedDriver.driver_id} will verify this OTP
                </div>
                <div className="flex items-center justify-center gap-2 text-sm text-yellow-600">
                  <span className="animate-pulse">⏳</span>
                  Waiting for driver to verify OTP...
                </div>
              </div>
            </div>
          )}

          {!assignedDriver && (
            <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3">
              <div className="text-xs text-gray-600 mb-1">Click mode:</div>
              <div className={`font-bold text-lg ${
                selectionMode === 'pickup' ? 'text-green-600' : 'text-red-600'
              }`}>
                {selectionMode === 'pickup' ? '📍 Pickup' : '🎯 Dropoff'}
              </div>
            </div>
          )}

          {assignedDriver && !showOtp && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-white rounded-lg shadow-2xl p-6 min-w-[400px]">
              <div className="text-center">
                <div className="text-6xl mb-3">
                  {assignedDriver.status === 'in_progress' ? '🚗' : '🎉'}
                </div>
                <div className="text-2xl font-bold text-green-600 mb-2">
                  {assignedDriver.status === 'in_progress' ? 'Ride In Progress!' : 'Driver Assigned!'}
                </div>
                <div className="bg-blue-50 p-4 rounded-lg mb-4">
                  <div className="text-lg font-semibold text-gray-800 mb-2">
                    🚗 {assignedDriver.driver_name}
                  </div>
                  <div className="text-sm text-gray-600">
                    Driver ID: {assignedDriver.driver_id}
                  </div>
                  {assignedDriver.status && (
                    <div className="text-xs text-gray-500 mt-2">
                      Status: {assignedDriver.status === 'in_progress' ? 'In Progress' : 'Accepted'}
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