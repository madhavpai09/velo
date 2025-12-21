import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import MapView from '../shared/MapView';
import { useAuth } from '../context/AuthContext';
import {
  createRideRequest,
  getAvailableDrivers,
  rateDriver,
  cancelRide,
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

export default function Ride() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [pickupLocation, setPickupLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [dropoffLocation, setDropoffLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [drivers, setDrivers] = useState<DriverForMap[]>([]);
  const [rideId, setRideId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectionMode, setSelectionMode] = useState<'pickup' | 'dropoff'>('pickup');
  const [assignedDriver, setAssignedDriver] = useState<AssignedDriver | null>(null);
  const [waitingForDriver, setWaitingForDriver] = useState(false);
  const [selectedRideType, setSelectedRideType] = useState<'auto' | 'school_pool' | 'school_priority'>('auto');
  const [showRatingModal, setShowRatingModal] = useState(false);
  const [rating, setRating] = useState(0);
  const [ratingComment, setRatingComment] = useState('');
  const [lastCompletedRide, setLastCompletedRide] = useState<{ id: number, driverId: number } | null>(null);

  useEffect(() => {
    const type = searchParams.get('type');
    if (type === 'school_priority') {
      setSelectedRideType('school_priority');
    }
  }, [searchParams]);

  // Default center (Bangalore)
  const mapCenter: [number, number] = [12.9716, 77.5946];

  useEffect(() => {
    fetchDrivers();
    const interval = setInterval(fetchDrivers, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!user?.id) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/user/${user.id}/ride-status`);
        if (response.ok) {
          const data = await response.json();

          if (data.has_ride) {
            setWaitingForDriver(false);

            if (data.status === 'matched' || data.status === 'accepted' || data.status === 'in_progress') {
              console.log('📊 Ride status data:', data);
              console.log('🔐 OTP value:', data.otp);
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

              // Parse driver location for map
              if (data.driver_location) {
                const [dLat, dLng] = data.driver_location.split(',').map(Number);
                // Create a live driver object for the map
                setDrivers([{
                  driver_id: data.driver_id,
                  lat: dLat,
                  lng: dLng,
                  available: false // Busy with this ride
                }]);
              }

              if (data.ride_id) {
                setRideId(data.ride_id);
              }
            } else if (data.status === 'completed' && assignedDriver) {
              // Ride just completed
              setLastCompletedRide({ id: assignedDriver.ride_id!, driverId: assignedDriver.driver_id });
              setAssignedDriver(null);
              setShowRatingModal(true);
            }
          } else if (assignedDriver && (assignedDriver.status === 'in_progress' || assignedDriver.status === 'accepted')) {
            // Handle case where has_ride becomes false (Completed)
            // Catch both 'in_progress' and 'accepted' to handle race conditions where polling misses the in_progress state
            console.log("🏁 Ride finished (detected via polling). Showing rating.");
            setLastCompletedRide({ id: assignedDriver.ride_id!, driverId: assignedDriver.driver_id });
            setAssignedDriver(null);
            setShowRatingModal(true);
          }
        }
      } catch (error) {
        console.error('Failed to poll ride status:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [user, assignedDriver]);

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

  const calculateFare = (rideType: 'auto' | 'school_pool' | 'school_priority'): number => {
    switch (rideType) {
      case 'auto':
        return 100;
      case 'school_pool':
        return 150;
      case 'school_priority':
        return 250;
      default:
        return 100;
    }
  };

  const handleRequestRide = async () => {
    if (!pickupLocation || !dropoffLocation) {
      alert('Please select both pickup and dropoff locations');
      return;
    }

    setLoading(true);
    try {
      const fare = calculateFare(selectedRideType);
      const response = await createRideRequest(
        pickupLocation,
        dropoffLocation,
        user?.id || 7000,
        selectedRideType,
        fare
      );

      setRideId(response.data.id);
      setWaitingForDriver(true);
    } catch (error: any) {
      console.error('❌ Failed to create ride:', error);
      alert(`Failed to create ride: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelRide = async () => {
    if (!rideId) return;

    // eslint-disable-next-line no-restricted-globals
    if (confirm('Are you sure you want to cancel the ride?')) {
      try {
        await cancelRide(rideId);
        handleNewRide();
        alert('Ride cancelled successfully');
      } catch (error) {
        console.error('Failed to cancel ride:', error);
        alert('Failed to cancel ride');
      }
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

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Please Login Required</h2>
          <button
            onClick={() => navigate('/login')}
            className="bg-black text-white px-6 py-3 rounded-xl font-bold"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  if (showRatingModal) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl animate-scale-in">
          <div className="text-center mb-6">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">✅</span>
            </div>
            <h2 className="text-2xl font-bold mb-2">Ride Completed!</h2>
            <p className="text-gray-600">How was your ride with Driver {lastCompletedRide?.driverId}?</p>
          </div>

          <div className="flex justify-center gap-2 mb-8">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => setRating(star)}
                className={`text-4xl transition-transform hover:scale-110 ${rating >= star ? 'grayscale-0' : 'grayscale opacity-30'}`}
              >
                ⭐
              </button>
            ))}
          </div>

          <textarea
            value={ratingComment}
            onChange={(e) => setRatingComment(e.target.value)}
            placeholder="Add a comment (optional)..."
            className="w-full bg-gray-50 p-4 rounded-xl mb-6 text-sm focus:outline-none focus:ring-2 focus:ring-black/5 resize-none h-32"
          />

          <button
            onClick={async () => {
              if (rating === 0) {
                alert('Please select a rating');
                return;
              }
              try {
                await rateDriver(lastCompletedRide!.driverId, user!.id, lastCompletedRide!.id, rating, ratingComment);
                setShowRatingModal(false);
                setRating(0);
                setRatingComment('');
                setLastCompletedRide(null);
                handleNewRide();
              } catch (error) {
                console.error('Failed to submit rating:', error);
                alert('Failed to submit rating');
              }
            }}
            className="w-full bg-black text-white py-4 rounded-xl font-bold text-lg hover:bg-gray-800 transition-colors"
          >
            Submit Rating
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col md:flex-row overflow-hidden relative">
      {/* Sidebar Panel */}
      <div className="w-full md:w-[450px] bg-white z-20 shadow-2xl flex flex-col h-[50vh] md:h-full overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex justify-between items-center">
          <div className="text-2xl font-normal tracking-tight cursor-pointer" onClick={() => navigate('/')}>VELO Cabs</div>
          <div className="flex items-center gap-3">
            <div className="text-sm font-medium">{user.name}</div>
            <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">👤</div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 flex-1">
          {assignedDriver ? (
            <div className="space-y-6 animate-fade-in">
              {assignedDriver.status === 'in_progress' ? (
                <div className="bg-green-50 p-6 rounded-xl border border-green-100 text-center">
                  <div className="text-6xl mb-4 animate-bounce">🛺</div>
                  <h2 className="text-2xl font-bold text-green-800 mb-2">On Ride</h2>
                  <p className="text-green-600">Heading to destination</p>
                </div>
              ) : (
                <div className="bg-green-50 p-6 rounded-xl border border-green-100">
                  <div className="text-center mb-4">
                    <div className="text-5xl mb-2">🛺</div>
                    <h2 className="text-xl font-bold text-gray-900">Driver Arriving</h2>
                    <p className="text-gray-500">{assignedDriver.driver_name}</p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <span className="text-gray-500">Status</span>
                      <span className="font-medium text-green-600 capitalize">{assignedDriver.status?.replace('_', ' ')}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <span className="text-gray-500">Vehicle</span>
                      <span className="font-medium">Piaggio Ape • KA 01 AB 5789</span>
                    </div>
                    {assignedDriver.otp && (
                      <div className="flex items-center justify-between p-4 bg-black text-white rounded-lg shadow-lg">
                        <span className="text-gray-300">OTP</span>
                        <span className="font-mono text-2xl font-bold tracking-widest">{assignedDriver.otp}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <button
                onClick={handleNewRide}
                className="w-full bg-gray-100 text-black py-4 rounded-lg font-medium hover:bg-gray-200 transition-colors"
              >
                New Ride
              </button>
            </div>
          ) : waitingForDriver ? (
            <div className="text-center py-12 space-y-6">
              <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto animate-pulse">
                <span className="text-4xl">📡</span>
              </div>
              <div>
                <h2 className="text-2xl font-bold mb-2">Finding your ride</h2>
                <p className="text-gray-500">Connecting you with nearby drivers...</p>
              </div>
              <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden">
                <div className="h-full bg-black w-1/2 animate-[shimmer_1.5s_infinite]"></div>
              </div>

              <button
                onClick={handleCancelRide}
                className="mt-6 px-6 py-2 bg-red-100 text-red-600 rounded-full font-medium hover:bg-red-200 transition-colors"
              >
                Cancel Request
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              <h1 className="text-3xl font-bold">Get a ride</h1>

              {/* Input Fields */}
              <div className="relative space-y-4">
                {/* Connecting Line */}
                <div className="absolute left-4 top-10 bottom-10 w-0.5 bg-gray-300"></div>

                <div className="relative">
                  <div className={`absolute left-3 top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full ${selectionMode === 'pickup' ? 'bg-black ring-4 ring-black/10' : 'bg-gray-400'}`}></div>
                  <input
                    type="text"
                    readOnly
                    value={pickupLocation ? `${pickupLocation.lat.toFixed(4)}, ${pickupLocation.lng.toFixed(4)}` : ''}
                    placeholder="Pickup location"
                    onClick={() => setSelectionMode('pickup')}
                    className={`w-full bg-gray-100 p-3 pl-10 rounded-lg cursor-pointer transition-all ${selectionMode === 'pickup' ? 'ring-2 ring-black bg-white' : ''}`}
                  />
                </div>

                <div className="relative">
                  <div className={`absolute left-3 top-1/2 -translate-y-1/2 w-2.5 h-2.5 bg-black square`}></div>
                  <input
                    type="text"
                    readOnly
                    value={dropoffLocation ? `${dropoffLocation.lat.toFixed(4)}, ${dropoffLocation.lng.toFixed(4)}` : ''}
                    placeholder="Dropoff location"
                    onClick={() => setSelectionMode('dropoff')}
                    className={`w-full bg-gray-100 p-3 pl-10 rounded-lg cursor-pointer transition-all ${selectionMode === 'dropoff' ? 'ring-2 ring-black bg-white' : ''}`}
                  />
                </div>
              </div>

              {/* Ride Options */}
              {pickupLocation && dropoffLocation && (
                <div className="space-y-3 pt-4">
                  <h3 className="font-medium text-gray-500 mb-2">Suggested Rides</h3>

                  <div
                    className={`flex items-center justify-between p-4 border-2 rounded-xl cursor-pointer transition-colors ${selectedRideType === 'auto' ? 'border-black bg-gray-50' : 'border-gray-200 bg-white hover:bg-gray-50'}`}
                    onClick={() => setSelectedRideType('auto')}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-16"><img src="https://www.uber-assets.com/image/upload/f_auto,q_auto:eco,c_fill,w_188,h_188/v1548646935/assets/64/93c255-87c8-4e2e-9429-cf709bf1b838/original/3.png" alt="UberX" /></div>
                      <div>
                        <div className="font-bold text-lg flex items-center gap-2">VELO Auto <span className="text-xs font-normal text-gray-500">👤 3</span></div>
                        <div className="text-sm text-gray-500">Affordable, everyday rides</div>
                      </div>
                    </div>
                    <div className="font-bold text-lg">₹100</div>
                  </div>

                  <div
                    className={`flex items-center justify-between p-4 border-2 rounded-xl cursor-pointer transition-colors ${selectedRideType === 'school_pool' ? 'border-yellow-500 bg-yellow-50' : 'border-gray-200 bg-white hover:bg-gray-50'}`}
                    onClick={() => setSelectedRideType('school_pool')}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-16 flex items-center justify-center text-4xl">🎒</div>
                      <div>
                        <div className="font-bold text-lg flex items-center gap-2">Priority Rides <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded-full">Priority</span></div>
                        <div className="text-sm text-gray-500">Priority pickup for urgent rides</div>
                      </div>
                    </div>
                    <div className="font-bold text-lg">₹150</div>
                  </div>

                  <div
                    className={`flex items-center justify-between p-4 border-2 rounded-xl cursor-pointer transition-colors ${selectedRideType === 'school_priority' ? 'border-red-500 bg-red-50' : 'border-gray-200 bg-white hover:bg-gray-50'}`}
                    onClick={() => setSelectedRideType('school_priority')}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-16 flex items-center justify-center text-4xl">🚨</div>
                      <div>
                        <div className="font-bold text-lg flex items-center gap-2">School Ride <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full">Safe Driver</span></div>
                        <div className="text-sm text-gray-500">Verified safe driver • Immediate pickup</div>
                      </div>
                    </div>
                    <div className="font-bold text-lg">₹250</div>
                  </div>

                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-xl bg-white cursor-pointer hover:bg-gray-50 transition-colors opacity-60">
                    <div className="flex items-center gap-4">
                      <div className="w-16"><img src="https://www.uber-assets.com/image/upload/f_auto,q_auto:eco,c_fill,w_188,h_188/v1649231091/assets/2c/7fa194-c954-49b2-9c6d-a3b8601370f5/original/Uber_Moto_Orange_312x312_Logo_0690d9.png" alt="Moto" /></div>
                      <div>
                        <div className="font-bold text-lg flex items-center gap-2">Moto <span className="text-xs font-normal text-gray-500">👤 1</span></div>
                        <div className="text-sm text-gray-500">Affordable motorcycle rides</div>
                      </div>
                    </div>
                    <div className="font-bold text-lg">Coming Soon</div>
                  </div>
                </div>
              )}

              <button
                onClick={handleRequestRide}
                disabled={!pickupLocation || !dropoffLocation || loading}
                className="w-full bg-black text-white py-4 rounded-lg font-bold text-lg hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors mt-4"
              >
                {loading ? 'Requesting...' : 'Request velo'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Map Area */}
      <div className="flex-1 relative h-[50vh] md:h-full">
        {/* Floating Mode Indicator */}
        {!assignedDriver && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white px-4 py-2 rounded-full shadow-lg font-medium text-sm flex items-center gap-2">
            <span>{selectionMode === 'pickup' ? '📍 Set Pickup' : '🏁 Set Dropoff'}</span>
            <span className="text-gray-400">|</span>
            <span className="text-gray-500">Click on map</span>
          </div>
        )}

        <MapView
          center={mapCenter}
          zoom={14}
          onLocationSelect={!assignedDriver ? handleLocationSelect : undefined}
          pickupMarker={pickupLocation}
          dropoffMarker={dropoffLocation}
          drivers={drivers}
        />
      </div>
    </div >
  );
}