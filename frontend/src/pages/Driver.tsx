import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import MapView from '../shared/MapView';
import {
  registerDriver,
  setDriverAvailability,
  updateDriverLocation,
  getDriverStatus,
  DriverStatus
} from '../utils/api';

export default function Driver() {
  const navigate = useNavigate();
  const [driverId, setDriverId] = useState<string>('');
  const [driverName, setDriverName] = useState<string>('');
  const [isRegistered, setIsRegistered] = useState(false);
  const [isAvailable, setIsAvailable] = useState(false);
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number }>({ lat: 12.9716, lng: 77.5946 });
  const [currentRide, setCurrentRide] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<DriverStatus | null>(null);
  const [otpInput, setOtpInput] = useState('');
  const isAvailableRef = useRef(isAvailable);
  const driverIdRef = useRef(driverId);
  const isRegisteredRef = useRef(isRegistered);

  // Keep refs in sync
  useEffect(() => {
    isAvailableRef.current = isAvailable;
  }, [isAvailable]);

  useEffect(() => {
    driverIdRef.current = driverId;
  }, [driverId]);

  useEffect(() => {
    isRegisteredRef.current = isRegistered;
  }, [isRegistered]);

  // Bangalore, India coordinates
  const mapCenter: [number, number] = [12.9716, 77.5946];

  // Poll for driver status when registered (read-only, don't change availability)
  useEffect(() => {
    if (!isRegistered || !driverId) return;

    const pollInterval = setInterval(async () => {
      try {
        const numericId = parseInt(driverId.replace('DRIVER-', '')) || parseInt(driverId);
        if (numericId) {
          const driverStatus = await getDriverStatus(numericId);
          if (driverStatus) {
            setStatus(driverStatus);
            // Don't automatically update isAvailable - only user can toggle it
            // Only sync if status is null (initial load)
            if (status === null) {
              setIsAvailable(driverStatus.available || false);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll driver status:', error);
      }
    }, 3000); // Poll every 3 seconds (read-only)

    return () => clearInterval(pollInterval);
  }, [isRegistered, driverId, status]);

  // Send heartbeat every 10 seconds when registered
  useEffect(() => {
    if (!isRegistered || !driverId) return;

    const heartbeatInterval = setInterval(async () => {
      try {
        const fullDriverId = driverId.startsWith('DRIVER-') ? driverId : `DRIVER-${driverId}`;
        await fetch(`http://localhost:8000/driver/heartbeat?driver_id=${encodeURIComponent(fullDriverId)}`, {
          method: 'POST'
        });
      } catch (error) {
        console.error('Heartbeat failed:', error);
      }
    }, 10000);

    return () => clearInterval(heartbeatInterval);
  }, [isRegistered, driverId]);

  // Poll for ride assignments when driver is online and available
  useEffect(() => {
    if (!isRegistered || !driverId || !isAvailable) return;

    const pollRideInterval = setInterval(async () => {
      try {
        const numericId = parseInt(driverId.replace('DRIVER-', '')) || parseInt(driverId);
        if (numericId) {
          const response = await fetch(`http://localhost:8000/api/driver/${numericId}/pending-ride`);
          if (response.ok) {
            const data = await response.json();
            if (data.has_ride && !currentRide) {
              console.log('🎉 New ride offered!', data);
              setCurrentRide(data);
              // Don't auto-accept anymore
              // setIsAvailable(false); // Driver is now on a ride
              // Auto-accept the ride
              // await fetch(`http://localhost:8000/api/driver/${numericId}/accept-ride/${data.match_id}`, {
              //   method: 'POST'
              // });
              // alert(`🚨 New Ride Assigned!\nRide ID: ${data.ride_id}\nUser ID: ${data.user_id}\nPickup: ${data.pickup_location}\nDropoff: ${data.dropoff_location}`);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll for ride assignments:', error);
      }
    }, 2000); // Poll every 2 seconds for ride assignments

    return () => clearInterval(pollRideInterval);
  }, [isRegistered, driverId, isAvailable, currentRide]);

  // Poll for current active ride when driver is on a ride
  useEffect(() => {
    if (!isRegistered || !driverId) return;

    const pollCurrentRideInterval = setInterval(async () => {
      try {
        const numericId = parseInt(driverId.replace('DRIVER-', '')) || parseInt(driverId);
        if (numericId) {
          const response = await fetch(`http://localhost:8000/api/driver/${numericId}/current-ride`);
          if (response.ok) {
            const data = await response.json();
            if (data.has_ride) {
              // Update current ride info
              if (!currentRide || currentRide.ride_id !== data.ride_id || currentRide.status !== data.status) {
                setCurrentRide(data);
                if (data.status === 'accepted' || data.status === 'in_progress') {
                  setIsAvailable(false);
                }
              }
            } else {
              // No active ride - driver should be available if they were on a ride
              if (currentRide && (currentRide.status === 'accepted' || currentRide.status === 'in_progress')) {
                setCurrentRide(null);
                setIsAvailable(true);
              }
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll for current ride:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollCurrentRideInterval);
  }, [isRegistered, driverId, currentRide]);

  // Mark driver as offline when component unmounts (user closes page) or page unloads
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Mark driver as offline when page is closing
      if (isRegisteredRef.current && driverIdRef.current && isAvailableRef.current) {
        const fullDriverId = driverIdRef.current.startsWith('DRIVER-')
          ? driverIdRef.current
          : `DRIVER-${driverIdRef.current}`;

        // Use fetch with keepalive for reliable cleanup on page close
        // keepalive ensures the request completes even if page is closing
        fetch(`http://localhost:8000/driver/set-availability?driver_id=${encodeURIComponent(fullDriverId)}&is_available=false`, {
          method: 'POST',
          keepalive: true,
        }).catch(() => {
          // Silently fail - page is closing anyway
        });
      }
    };

    const handleVisibilityChange = () => {
      // Mark driver as offline when tab becomes hidden (optional)
      if (document.hidden && isRegisteredRef.current && driverIdRef.current && isAvailableRef.current) {
        // You can choose to mark offline when tab is hidden, or only on page close
        // For now, we'll only mark offline on page close
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      // Cleanup: mark driver as offline when component unmounts
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);

      if (isRegistered && driverId && isAvailable) {
        const fullDriverId = driverId.startsWith('DRIVER-') ? driverId : `DRIVER-${driverId}`;
        // Try to set availability to false (may not complete if page is closing)
        fetch(`http://localhost:8000/driver/set-availability?driver_id=${encodeURIComponent(fullDriverId)}&is_available=false`, {
          method: 'POST',
          keepalive: true, // Keep request alive even if page is closing
        }).catch(() => {
          // Silently fail - page is closing anyway
        });
      }
    };
  }, [isRegistered, driverId, isAvailable]);

  const handleRegister = async () => {
    if (!driverId || !driverName) {
      alert('Please enter Driver ID and Name');
      return;
    }

    setLoading(true);
    try {
      const result = await registerDriver(
        driverId.startsWith('DRIVER-') ? driverId : `DRIVER-${driverId}`,
        driverName,
        currentLocation
      );

      setIsRegistered(true);
      setIsAvailable(true);
      console.log('✅ Driver registered:', result);
    } catch (error: any) {
      console.error('❌ Failed to register driver:', error);
      alert(`Failed to register: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAvailability = async () => {
    if (!isRegistered) return;

    setLoading(true);
    try {
      const newAvailability = !isAvailable;
      const fullDriverId = driverId.startsWith('DRIVER-') ? driverId : `DRIVER-${driverId}`;

      // Update backend first
      await setDriverAvailability(fullDriverId, newAvailability);

      // Only update local state if backend update succeeds
      setIsAvailable(newAvailability);

      console.log(`✅ Driver ${newAvailability ? 'online' : 'offline'}`);
    } catch (error: any) {
      console.error('❌ Failed to update availability:', error);
      alert(`Failed to update availability: ${error.message}`);
      // Don't update local state if backend update failed
    } finally {
      setLoading(false);
    }
  };

  const handleLocationSelect = (lat: number, lng: number) => {
    setCurrentLocation({ lat, lng });
    if (isRegistered) {
      updateDriverLocation(
        driverId.startsWith('DRIVER-') ? driverId : `DRIVER-${driverId}`,
        { lat, lng }
      ).catch(err => console.error('Failed to update location:', err));
    }
  };

  const handleAcceptRide = async () => {
    if (!currentRide || !currentRide.match_id) return;
    setLoading(true);
    try {
      const numericId = parseInt(driverId.replace('DRIVER-', '')) || parseInt(driverId);
      const response = await fetch(
        `http://localhost:8000/api/driver/${numericId}/accept-ride/${currentRide.match_id}`,
        { method: 'POST' }
      );
      if (response.ok) {
        const data = await response.json();
        setCurrentRide({ ...currentRide, status: 'accepted' });
        setIsAvailable(false);
        alert(`✅ Ride Accepted! Go to pickup location.`);
      }
    } catch (error) {
      console.error('Failed to accept ride:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!currentRide || !currentRide.ride_id || !otpInput) return;
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/ride/${currentRide.ride_id}/verify-otp?otp=${otpInput}`,
        { method: 'POST' }
      );
      if (response.ok) {
        setCurrentRide({ ...currentRide, status: 'in_progress' });
        alert(`✅ OTP Verified! Ride Started.`);
      } else {
        alert('❌ Invalid OTP. Please try again.');
      }
    } catch (error) {
      console.error('Failed to verify OTP:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col font-sans">
      {/* Header */}
      <header className="bg-black text-white px-6 py-4 flex justify-between items-center z-30">
        <div className="flex items-center gap-4">
          <div className="text-2xl font-normal tracking-tight cursor-pointer" onClick={() => navigate('/')}>VELO</div>
          <div className="text-sm font-medium bg-gray-800 px-3 py-1 rounded-full">Driver</div>
        </div>
        <div className="flex items-center gap-4">
          {isRegistered && (
            <div className={`w-3 h-3 rounded-full ${isAvailable ? 'bg-green-500' : 'bg-red-500'}`}></div>
          )}
          <button onClick={() => navigate('/')} className="text-sm hover:text-gray-300">Exit</button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Sidebar - Driver Controls */}
        <div className="w-full md:w-[400px] bg-white shadow-2xl z-20 flex flex-col h-full overflow-y-auto absolute md:relative">
          {!isRegistered ? (
            <div className="p-8 flex flex-col h-full justify-center">
              <h2 className="text-3xl font-bold mb-2">Welcome back</h2>
              <p className="text-gray-500 mb-8">Sign in to start driving</p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Driver ID</label>
                  <input
                    type="text"
                    value={driverId}
                    onChange={(e) => setDriverId(e.target.value)}
                    placeholder="e.g., 9000"
                    className="w-full bg-gray-100 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                  <input
                    type="text"
                    value={driverName}
                    onChange={(e) => setDriverName(e.target.value)}
                    placeholder="e.g., John Doe"
                    className="w-full bg-gray-100 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
                  />
                </div>

                <button
                  onClick={handleRegister}
                  disabled={loading}
                  className="w-full bg-black text-white py-4 rounded-lg font-medium text-lg hover:bg-gray-800 disabled:bg-gray-400 transition-colors"
                >
                  {loading ? 'Signing in...' : 'Continue'}
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col h-full">
              {/* Status Header */}
              <div className="p-6 bg-black text-white">
                <h2 className="text-2xl font-bold mb-1">Hello, {driverName}</h2>
                <p className="text-gray-400 text-sm">ID: {driverId}</p>
              </div>

              {/* Action Area */}
              <div className="p-6 flex-1 flex flex-col gap-6">
                {currentRide ? (
                  <div className="bg-white border-2 border-black rounded-xl p-6 shadow-lg animate-slide-up">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-xl font-bold">
                          {currentRide.status === 'offered' ? 'New Trip Request' :
                            currentRide.status === 'accepted' ? 'Go to Pickup' :
                              'Trip in Progress'}
                        </h3>
                        <p className="text-gray-500">VELO • 4 min away</p>
                      </div>
                      <div className="bg-black text-white px-3 py-1 rounded text-sm font-bold">
                        ₹100
                      </div>
                    </div>

                    <div className="space-y-4 mb-6">
                      <div className="flex gap-3">
                        <div className="mt-1">📍</div>
                        <div>
                          <div className="text-xs text-gray-500">PICKUP</div>
                          <div className="font-medium">{currentRide.pickup_location}</div>
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <div className="mt-1">🏁</div>
                        <div>
                          <div className="text-xs text-gray-500">DROPOFF</div>
                          <div className="font-medium">{currentRide.dropoff_location}</div>
                        </div>
                      </div>
                    </div>

                    {currentRide.status === 'offered' && (
                      <div className="flex gap-4">
                        <button
                          onClick={() => setCurrentRide(null)} // Reject locally for now
                          className="flex-1 bg-gray-200 text-black py-4 rounded-lg font-bold text-lg hover:bg-gray-300 transition-colors"
                        >
                          Decline
                        </button>
                        <button
                          onClick={handleAcceptRide}
                          disabled={loading}
                          className="flex-1 bg-black text-white py-4 rounded-lg font-bold text-lg hover:bg-gray-800 transition-colors"
                        >
                          {loading ? 'Accepting...' : 'Accept'}
                        </button>
                      </div>
                    )}

                    {currentRide.status === 'accepted' && (
                      <div className="space-y-4">
                        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                          <p className="text-sm text-yellow-800 font-medium mb-2">Ask rider for OTP to start trip</p>
                          <input
                            type="text"
                            value={otpInput}
                            onChange={(e) => setOtpInput(e.target.value)}
                            placeholder="Enter 4-digit OTP"
                            maxLength={4}
                            className="w-full p-3 border border-gray-300 rounded text-center text-2xl tracking-widest font-mono"
                          />
                        </div>
                        <button
                          onClick={handleVerifyOTP}
                          disabled={loading || otpInput.length !== 4}
                          className="w-full bg-black text-white py-4 rounded-lg font-bold text-lg hover:bg-gray-800 disabled:bg-gray-400 transition-colors"
                        >
                          {loading ? 'Verifying...' : 'Start Trip'}
                        </button>
                      </div>
                    )}

                    {currentRide.status === 'in_progress' && (
                      <button
                        onClick={async () => {
                          if (!currentRide || !currentRide.ride_id) return;
                          setLoading(true);
                          try {
                            const numericId = parseInt(driverId.replace('DRIVER-', '')) || parseInt(driverId);
                            const response = await fetch(
                              `http://localhost:8000/api/driver/${numericId}/complete-ride/${currentRide.ride_id}`,
                              { method: 'POST' }
                            );
                            if (response.ok) {
                              alert(`✅ Trip completed!`);
                              setCurrentRide(null);
                              setIsAvailable(true);
                              setOtpInput('');
                              await setDriverAvailability(
                                driverId.startsWith('DRIVER-') ? driverId : `DRIVER-${driverId}`,
                                true
                              );
                            }
                          } catch (error) {
                            console.error('Failed to complete ride:', error);
                          } finally {
                            setLoading(false);
                          }
                        }}
                        disabled={loading}
                        className="w-full bg-black text-white py-4 rounded-lg font-bold text-lg hover:bg-gray-800 transition-colors"
                      >
                        {loading ? 'Completing...' : 'Complete Trip'}
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col justify-center items-center text-center space-y-6">
                    <div className={`w-32 h-32 rounded-full flex items-center justify-center cursor-pointer transition-all ${isAvailable
                        ? 'bg-blue-600 hover:bg-blue-700 shadow-[0_0_0_8px_rgba(37,99,235,0.2)]'
                        : 'bg-black hover:bg-gray-800'
                      }`}
                      onClick={handleToggleAvailability}
                    >
                      <span className="text-white font-bold text-xl">
                        {isAvailable ? 'GO OFFLINE' : 'GO ONLINE'}
                      </span>
                    </div>
                    <p className="text-gray-500">
                      {isAvailable ? 'You are online. Finding trips...' : 'You are offline'}
                    </p>
                  </div>
                )}

                {/* Stats (Mock) */}
                <div className="grid grid-cols-3 gap-4 border-t pt-6">
                  <div className="text-center">
                    <div className="text-xl font-bold">₹345</div>
                    <div className="text-xs text-gray-500">EARNINGS</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold">09</div>
                    <div className="text-xs text-gray-500">TRIPS</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold">4.86</div>
                    <div className="text-xs text-gray-500">RATING</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Map */}
        <div className="flex-1 relative h-full">
          {isRegistered && (
            <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3">
              <div className="text-xs text-gray-600 mb-1">Click to update location:</div>
              <div className="font-bold text-sm">
                📍 Your Location
              </div>
            </div>
          )}

          <MapView
            center={mapCenter}
            zoom={13}
            onLocationSelect={isRegistered ? handleLocationSelect : undefined}
            pickupMarker={null}
            dropoffMarker={null}
            drivers={[]}
            driverLocation={isRegistered ? currentLocation : null}
          />
        </div>
      </div>
    </div>
  );
}

