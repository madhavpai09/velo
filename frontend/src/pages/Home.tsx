import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MapView from '../shared/MapView';
import RideForm from '../shared/RideForm';
import { 
  createRideRequest, 
  getAvailableDrivers,
  getRideStatus,
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
  
  // NEW: OTP related states
  const [rideOTP, setRideOTP] = useState<string | null>(null);
  const [showOTP, setShowOTP] = useState(false);

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

  // Poll for ride status (only runs when userId is set)
  useEffect(() => {
    if (!userId || !isUserOnline) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/user/${userId}/ride-status`);
        if (response.ok) {
          const data = await response.json();
          // console.log("user ride-status poll:", data);

          if (data.has_ride) {
            setWaitingForDriver(false);
            
            if (data.status === 'matched' || data.status === 'accepted') {
              const driverInfo = {
                ride_id: data.ride_id,
                driver_id: data.driver_id,
                driver_name: `Driver ${data.driver_id}`,
                driver_location: data.driver_location || 'Unknown',
                pickup_location: data.pickup_location,
                dropoff_location: data.dropoff_location,
                status: data.status,
              };
              
              setAssignedDriver(driverInfo);

              if (data.ride_id) {
                setRideId(data.ride_id);

                // Generate OTP when driver is accepted (status = accepted)
                if (data.status === 'accepted' && !rideOTP) {
                  console.log(`Driver accepted ride ${data.ride_id} — generating OTP...`);
                  generateOTP(data.ride_id);
                }
              }
            } else if (data.status === 'in_progress') {
              // Ride has started - hide OTP
              setShowOTP(false);
              setRideOTP(null);
            }
          } else {
            // no ride
            // keep waitingForDriver state as is, don't clear assignedDriver immediately
          }
        } else {
          console.warn('ride-status poll returned non-ok', response.status);
        }
      } catch (error) {
        console.error('Failed to poll ride status:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [userId, isUserOnline, rideOTP]);

  const generateOTP = async (rideId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/ride/${rideId}/generate-otp`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setRideOTP(data.otp);
        setShowOTP(true);
        console.log('✅ OTP Generated:', data.otp);
      } else {
        console.warn('Failed to generate OTP - server returned non-ok:', response.status);
      }
    } catch (error) {
      console.error('Failed to generate OTP:', error);
    }
  };

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
      // Use explicit usedUserId and ensure we store it in state so polling starts
      const usedUserId = userId || 7000;
      // Ensure UI reflects that userId is set (so polling starts)
      setUserId(usedUserId);
      setShowUserIdInput(false);
      
      const response = await createRideRequest(
        pickupLocation,
        dropoffLocation,
        usedUserId
      );

      setRideId(response.data.id);
      setWaitingForDriver(true);
      console.log('✅ Ride created:', response.data, 'for user:', usedUserId);
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
    setRideOTP(null);
    setShowOTP(false);
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl"><img src="/0796f710-7ecb-4a40-8176-2eba9ee3c5cd.png" alt="VELO" className="w-11 h-11" /></span>
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

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Ride Form */}
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
                      alert('Please enter a valid User ID or leave blank to use default 7000 (it will be auto-set when you request).');
                    }
                  }}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                >
                  Set ID
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Each user needs a unique ID (e.g., 6000, 7000, 8000). Leave blank to use default 7000 (will be auto-set on request).
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
            rideOTP={rideOTP}
            showOTP={showOTP}
          />
        </div>

        {/* Map */}
        <div className="flex-1 relative">
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

          {/* OTP Display Popup */}
          {showOTP && rideOTP && assignedDriver && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-gradient-to-br from-green-400 to-green-600 rounded-lg shadow-2xl p-6 min-w-[350px] animate-pulse">
              <div className="text-center text-white">
                <div className="text-4xl mb-2">🔐</div>
                <div className="text-lg font-bold mb-1">Share OTP with Driver</div>
                <div className="text-sm mb-4 opacity-90">To start your ride</div>
                <div className="bg-white text-green-600 rounded-lg p-4 mb-3">
                  <div className="text-5xl font-bold tracking-widest">{rideOTP}</div>
                </div>
                <div className="text-xs opacity-90">
                  Don't share this OTP with anyone except your driver
                </div>
              </div>
            </div>
          )}

          {/* Assigned Driver Popup */}
          {assignedDriver && !showOTP && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-white rounded-lg shadow-2xl p-6 min-w-[400px]">
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
