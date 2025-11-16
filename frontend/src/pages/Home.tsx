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

  // Bangalore, India coordinates
  const mapCenter: [number, number] = [12.9716, 77.5946];

  // Mark user as online when component mounts
  useEffect(() => {
    setIsUserOnline(true);
    return () => {
      setIsUserOnline(false);
    };
  }, []);

  // Fetch drivers periodically
  useEffect(() => {
    fetchDrivers();
    const interval = setInterval(fetchDrivers, 5000);
    return () => clearInterval(interval);
  }, []);

  // Poll for ride status when waiting for driver or when user is online
  useEffect(() => {
    if (!userId || !isUserOnline) return;

    const pollInterval = setInterval(async () => {
      try {
        // Poll for ride status using user ID
        const response = await fetch(`http://localhost:8000/api/user/${userId}/ride-status`);
        if (response.ok) {
          const data = await response.json();
          
          if (data.has_ride) {
            // IMPORTANT: Only show driver info if ride has been ACCEPTED by driver
            // NOT during "broadcasting" or "pending" status
            if (data.status === 'accepted' || data.status === 'in_progress') {
              setWaitingForDriver(false);
              
              setAssignedDriver({
                ride_id: data.ride_id,
                driver_id: data.driver_id,
                driver_name: `Driver ${data.driver_id}`,
                driver_location: data.driver_location || 'Unknown',
                pickup_location: data.pickup_location,
                dropoff_location: data.dropoff_location,
                status: data.status,
              });
              
              // Update rideId if we got a new ride
              if (data.ride_id) {
                setRideId(data.ride_id);
              }
            } else if (data.status === 'completed' || data.status === 'cancelled') {
              // Ride completed - clear state
              if (assignedDriver) {
                console.log('✅ Ride completed!');
                setAssignedDriver(null);
                setRideId(null);
                setWaitingForDriver(false);
              }
            } else {
              // Still broadcasting or pending - keep showing waiting message
              console.log(`⏳ Ride status: ${data.status} - still waiting for driver to accept`);
            }
          } else {
            // No active ride
            if (assignedDriver && assignedDriver.status !== 'pending') {
              // Ride was completed
              console.log('✅ Ride completed - no active ride found');
              setAssignedDriver(null);
              setRideId(null);
              setWaitingForDriver(false);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll ride status:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [userId, isUserOnline, assignedDriver]);

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
      console.log('✅ Ride created - Broadcasting to nearby drivers:', response.data);
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

  const getRideStatusText = (status?: string) => {
    switch (status) {
      case 'pending':
        return 'Finding driver...';
      case 'matched':
        return 'Driver found!';
      case 'accepted':
        return 'Driver accepted - On the way!';
      case 'in_progress':
        return 'Ride in progress';
      case 'completed':
        return 'Ride completed';
      default:
        return 'Ride assigned';
    }
  };

  const getRideStatusColor = (status?: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-50 border-yellow-400 text-yellow-800';
      case 'matched':
        return 'bg-blue-50 border-blue-400 text-blue-800';
      case 'accepted':
        return 'bg-green-50 border-green-400 text-green-800';
      case 'in_progress':
        return 'bg-purple-50 border-purple-400 text-purple-800';
      case 'completed':
        return 'bg-gray-50 border-gray-400 text-gray-800';
      default:
        return 'bg-blue-50 border-blue-400 text-blue-800';
    }
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
              {/* User Online Status */}
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
                title="Go back to landing page to switch between User and Driver"
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
          {/* User ID Input */}
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

        {/* Map */}
        <div className="flex-1 relative">
          {/* Selection Mode Indicator */}
          {!assignedDriver && !waitingForDriver && (
            <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3">
              <div className="text-xs text-gray-600 mb-1">Click mode:</div>
              <div className={`font-bold text-lg ${
                selectionMode === 'pickup' ? 'text-green-600' : 'text-red-600'
              }`}>
                {selectionMode === 'pickup' ? '📍 Pickup' : '🎯 Dropoff'}
              </div>
            </div>
          )}

          {/* Waiting for Driver */}
          {waitingForDriver && !assignedDriver && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-white rounded-lg shadow-2xl p-6 min-w-[400px]">
              <div className="text-center">
                <div className="text-6xl mb-3 animate-bounce">📡</div>
                <div className="text-2xl font-bold text-blue-600 mb-2">Finding drivers...</div>
                <div className="text-sm text-gray-600 mb-3">
                  Broadcasting to nearby drivers
                </div>
                <div className="text-xs text-gray-500">
                  First driver to accept will be assigned to your ride
                </div>
              </div>
            </div>
          )}

          {/* Active Ride Status */}
          {assignedDriver && (
            <div className={`absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-white rounded-lg shadow-2xl p-6 min-w-[400px] border-2 ${getRideStatusColor(assignedDriver.status)}`}>
              <div className="text-center">
                <div className="text-6xl mb-3">
                  {assignedDriver.status === 'accepted' ? '🚗' :
                   assignedDriver.status === 'in_progress' ? '🚙' : '✅'}
                </div>
                <div className="text-2xl font-bold mb-2">
                  {getRideStatusText(assignedDriver.status)}
                </div>
                <div className="bg-white p-4 rounded-lg mb-4 border">
                  <div className="text-lg font-semibold text-gray-800 mb-2">
                    🚗 {assignedDriver.driver_name}
                  </div>
                  <div className="text-sm text-gray-600">
                    Driver ID: {assignedDriver.driver_id}
                  </div>
                  <div className="text-sm text-gray-600 mt-2">
                    Ride ID: {assignedDriver.ride_id}
                  </div>
                </div>
                
                {/* Ride Details */}
                <div className="text-left space-y-2 mb-4 text-sm">
                  <div className="bg-white/50 p-2 rounded">
                    <div className="font-semibold text-gray-700">📍 Pickup:</div>
                    <div className="text-gray-600 text-xs">{assignedDriver.pickup_location}</div>
                  </div>
                  <div className="bg-white/50 p-2 rounded">
                    <div className="font-semibold text-gray-700">🎯 Dropoff:</div>
                    <div className="text-gray-600 text-xs">{assignedDriver.dropoff_location}</div>
                  </div>
                </div>

                {/* Status Messages */}
                {assignedDriver.status === 'accepted' && (
                  <div className="bg-green-100 border border-green-300 rounded-lg p-3 mb-4">
                    <div className="text-sm font-semibold text-green-800">
                      🚗 Your driver is on the way to pick you up!
                    </div>
                  </div>
                )}
                
                {assignedDriver.status === 'in_progress' && (
                  <div className="bg-purple-100 border border-purple-300 rounded-lg p-3 mb-4">
                    <div className="text-sm font-semibold text-purple-800">
                      🚙 Ride in progress - Enjoy your trip!
                    </div>
                  </div>
                )}

                <div className="text-xs text-gray-500">
                  {assignedDriver.status === 'accepted' && 'Driver will arrive shortly'}
                  {assignedDriver.status === 'in_progress' && 'You will arrive at your destination soon'}
                  {assignedDriver.status === 'matched' && 'Driver has been matched to your ride'}
                </div>
              </div>
            </div>
          )}

          <MapView
            center={mapCenter}
            zoom={13}
            onLocationSelect={!assignedDriver && !waitingForDriver ? handleLocationSelect : undefined}
            pickupMarker={pickupLocation}
            dropoffMarker={dropoffLocation}
            drivers={drivers}
          />
        </div>
      </div>
    </div>
  );
}