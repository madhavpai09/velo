
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
  driver_id: number;
  driver_name: string;
  driver_location: string;
  pickup_location: string;
  dropoff_location: string;
}

export default function Home() {
  const navigate = useNavigate();
  const [pickupLocation, setPickupLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [dropoffLocation, setDropoffLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [drivers, setDrivers] = useState<DriverForMap[]>([]);
  const [rideId, setRideId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectionMode, setSelectionMode] = useState<'pickup' | 'dropoff'>('pickup');
  
  // NEW: Track assigned driver
  const [assignedDriver, setAssignedDriver] = useState<AssignedDriver | null>(null);
  const [waitingForDriver, setWaitingForDriver] = useState(false);

  // Bangalore, India coordinates
  const mapCenter: [number, number] = [12.9716, 77.5946];

  // Fetch drivers periodically
  useEffect(() => {
    fetchDrivers();
    const interval = setInterval(fetchDrivers, 5000);
    return () => clearInterval(interval);
  }, []);

  // NEW: Poll for ride status when waiting for driver
  useEffect(() => {
    if (!waitingForDriver || !rideId) return;

    const pollInterval = setInterval(async () => {
      try {
        const rideStatus = await getRideStatus(rideId);
        console.log('📊 Ride status:', rideStatus);

        // Check if ride is matched
        if (rideStatus.status === 'matched' || rideStatus.status === 'accepted') {
          // Stop polling
          setWaitingForDriver(false);
          
          // Simulate driver assignment (in real app, backend would provide this)
          // Find the driver from available drivers list
          const matchedDriver = drivers.find(d => d.driver_id === rideStatus.driver_id);
          
          if (matchedDriver) {
            setAssignedDriver({
              driver_id: matchedDriver.driver_id,
              driver_name: `Driver ${matchedDriver.driver_id}`,
              driver_location: `${matchedDriver.lat},${matchedDriver.lng}`,
              pickup_location: rideStatus.source_location,
              dropoff_location: rideStatus.dest_location,
            });
          }
        }
      } catch (error) {
        console.error('Failed to poll ride status:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [waitingForDriver, rideId, drivers]);

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
        7000
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
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl">🚕</span>
              <div>
                <h1 className="text-3xl font-bold">VELO</h1>
                <p className="text-sm text-blue-200">Your ride, your way</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/ride')}
              className="bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
            >
              View Rides
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Ride Form */}
        <div className="w-96">
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

          {/* Assigned Driver Popup */}
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

