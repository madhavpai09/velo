import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MapView from '../shared/MapView';
import RideForm from '../shared/RideForm';
import { useAuth } from '../context/AuthContext';
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
  const { user, logout } = useAuth();
  const [pickupLocation, setPickupLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [dropoffLocation, setDropoffLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [drivers, setDrivers] = useState<DriverForMap[]>([]);
  const [rideId, setRideId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectionMode, setSelectionMode] = useState<'pickup' | 'dropoff'>('pickup');
  const [assignedDriver, setAssignedDriver] = useState<AssignedDriver | null>(null);
  const [waitingForDriver, setWaitingForDriver] = useState(false);
  const [activeSubscription, setActiveSubscription] = useState<any>(null);

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
          // console.log('🚗 Poll Data:', data); 

          if (data.has_ride) {
            setWaitingForDriver(false);

            if (data.status === 'matched' || data.status === 'accepted' || data.status === 'in_progress') {
              console.log('🔐 OTP from backend:', data.otp); // Debug log
              setAssignedDriver({
                ride_id: data.ride_id,
                driver_id: data.driver_id,
                driver_name: `Driver ${data.driver_id}`,
                driver_location: data.driver_location || 'Unknown',
                pickup_location: data.pickup_location,
                dropoff_location: data.dropoff_location,
                status: data.status,
                otp: data.otp || null
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
  }, [user, assignedDriver]);

  // Fetch active subscription
  useEffect(() => {
    if (user?.id) {
      fetch(`http://localhost:8000/api/user/${user.id}/subscriptions`)
        .then(res => res.json())
        .then(data => {
          if (data.subscriptions && data.subscriptions.length > 0) {
            const active = data.subscriptions.find((s: any) => s.status === 'active');
            if (active) setActiveSubscription(active);
          }
        })
        .catch(err => console.error("Failed to fetch subs", err));
    }
  }, [user]);

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

    if (!user?.id) {
      alert('You must be logged in to request a ride.');
      return;
    }

    setLoading(true);
    try {
      const response = await createRideRequest(
        pickupLocation,
        dropoffLocation,
        user.id
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
              {user && (
                <div className="flex items-center gap-2 bg-white/20 px-4 py-2 rounded-lg">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                  <span className="font-semibold text-sm">Hello, {user.name}</span>
                </div>
              )}
              <button
                onClick={logout}
                className="text-white/80 hover:text-white text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-96 flex flex-col bg-white shadow-xl z-20">
          {/* Services Grid - Compact */}
          <div className="p-4 border-b">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Services</h2>
            <div className="grid grid-cols-2 gap-3">
              {activeSubscription && (
                <div className="col-span-2 bg-green-50 border border-green-200 p-3 rounded-lg flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-green-800 uppercase mb-1">Active</div>
                    <div className="font-bold text-sm">{activeSubscription.student_name}'s Ride</div>
                  </div>
                  <div className="text-xl">🚌</div>
                </div>
              )}

              <div
                onClick={() => navigate('/ride')}
                className="bg-gray-50 hover:bg-gray-100 p-3 rounded-lg cursor-pointer transition-colors flex flex-col items-center gap-2 border border-gray-100"
              >
                <img src="https://www.uber-assets.com/image/upload/f_auto,q_auto:eco,c_fill,w_188,h_188/v1548646935/assets/64/93c255-87c8-4e2e-9429-cf709bf1b838/original/3.png" alt="Ride" className="w-10 h-10 object-contain" />
                <span className="font-medium text-sm text-gray-700">Ride</span>
              </div>

              <div
                onClick={() => navigate('/school-pool')}
                className="bg-yellow-50 hover:bg-yellow-100 p-3 rounded-lg cursor-pointer transition-colors border border-yellow-100 flex flex-col items-center gap-2"
              >
                <div className="text-2xl">🎒</div>
                <div className="text-center">
                  <span className="font-medium text-sm text-gray-800 block">School Pool</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
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
        </div>

        <div className="flex-1 relative">
          {!assignedDriver && (
            <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-2 px-4">
              <div className="text-xs text-gray-500">Pick mode</div>
              <div className={`font-bold ${selectionMode === 'pickup' ? 'text-green-600' : 'text-red-600'
                }`}>
                {selectionMode === 'pickup' ? '📍 Pickup' : '🎯 Dropoff'}
              </div>
            </div>
          )}

          {assignedDriver && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-white rounded-xl shadow-2xl p-6 min-w-[400px] animate-bounce-slight border border-gray-100">
              <div className="text-center">
                <div className="text-5xl mb-2">🎉</div>
                <div className="text-xl font-bold text-green-600 mb-1">Driver Found!</div>
                <div className="bg-gray-50 p-4 rounded-xl mb-4 text-left">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-lg font-bold text-gray-800">
                      {assignedDriver.driver_name}
                    </div>
                    <div className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full font-bold">
                      #{assignedDriver.driver_id}
                    </div>
                  </div>
                  {assignedDriver.otp && (
                    <div className="mt-3 flex items-center justify-between bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                      <span className="text-xs font-bold text-yellow-800 uppercase">One-Time Password</span>
                      <span className="text-2xl font-mono font-bold tracking-widest">{assignedDriver.otp}</span>
                    </div>
                  )}
                </div>
                <button
                  onClick={handleNewRide}
                  className="w-full bg-blue-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all hover:scale-[1.02]"
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