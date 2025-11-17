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
  
  // NEW: OTP verification states
  const [enteredOTP, setEnteredOTP] = useState<string>('');
  const [showOTPInput, setShowOTPInput] = useState(false);
  const [otpError, setOtpError] = useState<string>('');
  
  const isAvailableRef = useRef(isAvailable);
  const driverIdRef = useRef(driverId);
  const isRegisteredRef = useRef(isRegistered);
  
  useEffect(() => {
    isAvailableRef.current = isAvailable;
  }, [isAvailable]);
  
  useEffect(() => {
    driverIdRef.current = driverId;
  }, [driverId]);
  
  useEffect(() => {
    isRegisteredRef.current = isRegistered;
  }, [isRegistered]);

  const mapCenter: [number, number] = [12.9716, 77.5946];

  // Poll for driver status
  useEffect(() => {
    if (!isRegistered || !driverId) return;

    const pollInterval = setInterval(async () => {
      try {
        const numericId = parseInt(driverId.replace('DRIVER-', '')) || parseInt(driverId);
        if (numericId) {
          const driverStatus = await getDriverStatus(numericId);
          if (driverStatus) {
            setStatus(driverStatus);
            if (status === null) {
              setIsAvailable(driverStatus.available || false);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll driver status:', error);
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [isRegistered, driverId, status]);

  // Poll for ride assignments
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
              console.log('🎉 New ride assigned!', data);
              setCurrentRide(data);
              setIsAvailable(false);
              setShowOTPInput(true);
              
              await fetch(`http://localhost:8000/api/driver/${numericId}/accept-ride/${data.match_id}`, {
                method: 'POST'
              });
              alert(`🚨 New Ride Assigned!\nRide ID: ${data.ride_id}\nUser ID: ${data.user_id}\nAsk user for OTP to start the ride!`);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll for ride assignments:', error);
      }
    }, 2000);

    return () => clearInterval(pollRideInterval);
  }, [isRegistered, driverId, isAvailable, currentRide]);

  // Poll for current active ride
  useEffect(() => {
    if (!isRegistered || !driverId || isAvailable) return;

    const pollCurrentRideInterval = setInterval(async () => {
      try {
        const numericId = parseInt(driverId.replace('DRIVER-', '')) || parseInt(driverId);
        if (numericId) {
          const response = await fetch(`http://localhost:8000/api/driver/${numericId}/current-ride`);
          if (response.ok) {
            const data = await response.json();
            if (data.has_ride) {
              if (!currentRide || currentRide.ride_id !== data.ride_id) {
                setCurrentRide(data);
              }
              // If ride is in_progress, hide OTP input
              if (data.status === 'in_progress') {
                setShowOTPInput(false);
              }
            } else {
              if (currentRide) {
                setCurrentRide(null);
                setIsAvailable(true);
                setShowOTPInput(false);
                setEnteredOTP('');
                setOtpError('');
              }
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll for current ride:', error);
      }
    }, 2000);

    return () => clearInterval(pollCurrentRideInterval);
  }, [isRegistered, driverId, isAvailable, currentRide]);

  // Cleanup on unmount
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (isRegisteredRef.current && driverIdRef.current && isAvailableRef.current) {
        const fullDriverId = driverIdRef.current.startsWith('DRIVER-') 
          ? driverIdRef.current 
          : `DRIVER-${driverIdRef.current}`;
        
        fetch(`http://localhost:8000/driver/set-availability?driver_id=${encodeURIComponent(fullDriverId)}&is_available=false`, {
          method: 'POST',
          keepalive: true,
        }).catch(() => {});
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      
      if (isRegistered && driverId && isAvailable) {
        const fullDriverId = driverId.startsWith('DRIVER-') ? driverId : `DRIVER-${driverId}`;
        fetch(`http://localhost:8000/driver/set-availability?driver_id=${encodeURIComponent(fullDriverId)}&is_available=false`, {
          method: 'POST',
          keepalive: true,
        }).catch(() => {});
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
      
      await setDriverAvailability(fullDriverId, newAvailability);
      setIsAvailable(newAvailability);
      
      console.log(`✅ Driver ${newAvailability ? 'online' : 'offline'}`);
    } catch (error: any) {
      console.error('❌ Failed to update availability:', error);
      alert(`Failed to update availability: ${error.message}`);
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

  const handleVerifyOTP = async () => {
    if (!currentRide || !enteredOTP || enteredOTP.length !== 4) {
      setOtpError('Please enter a valid 4-digit OTP');
      return;
    }

    setLoading(true);
    setOtpError('');
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/ride/${currentRide.ride_id}/verify-otp?otp=${enteredOTP}`,
        { method: 'POST' }
      );
      
      const data = await response.json();
      
      if (data.verified) {
        // OTP verified - start the ride
        const numericId = parseInt(driverId.replace('DRIVER-', '')) || parseInt(driverId);
        const startResponse = await fetch(
          `http://localhost:8000/api/driver/${numericId}/start-ride/${currentRide.ride_id}`,
          { method: 'POST' }
        );
        
        if (startResponse.ok) {
          alert('✅ OTP Verified! Ride Started!');
          setShowOTPInput(false);
          setEnteredOTP('');
          setOtpError('');
        } else {
          setOtpError('Failed to start ride. Please try again.');
        }
      } else {
        setOtpError('❌ Invalid OTP. Please check with the user.');
      }
    } catch (error: any) {
      console.error('Failed to verify OTP:', error);
      setOtpError('Failed to verify OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-green-600 to-green-800 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl"><img src="/0796f710-7ecb-4a40-8176-2eba9ee3c5cd.png" alt="VELO" className="w-11 h-11" /></span>
              <div>
                <h1 className="text-3xl font-bold">VELO Captain</h1>
                <p className="text-sm text-green-200">Drive and earn</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {isRegistered && (
                <div className="flex items-center gap-2 bg-white/20 px-4 py-2 rounded-lg">
                  <div className={`w-3 h-3 rounded-full ${
                    isAvailable ? 'bg-green-400 animate-pulse' : 
                    currentRide ? 'bg-yellow-400 animate-pulse' : 
                    'bg-gray-400'
                  }`}></div>
                  <span className="font-semibold">
                    {isAvailable ? '🟢 Online' : currentRide ? '🟡 On Ride' : '🔴 Offline'}
                  </span>
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

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-96 bg-white shadow-lg p-6 overflow-y-auto">
          {!isRegistered ? (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-6">Driver Registration</h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Driver ID
                    </label>
                    <input
                      type="text"
                      value={driverId}
                      onChange={(e) => setDriverId(e.target.value)}
                      placeholder="e.g., 9000 or DRIVER-9000"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Driver Name
                    </label>
                    <input
                      type="text"
                      value={driverName}
                      onChange={(e) => setDriverName(e.target.value)}
                      placeholder="e.g., John Doe"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>

                  <button
                    onClick={handleRegister}
                    disabled={loading}
                    className="w-full bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? 'Registering...' : '🚀 Register as Driver'}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">Driver Dashboard</h2>
                <div className="text-sm text-gray-600 mb-6">
                  <div>ID: {driverId}</div>
                  <div>Name: {driverName}</div>
                </div>
              </div>

              {/* Availability Toggle */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <span className="font-semibold text-gray-700">Availability</span>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    isAvailable ? 'bg-green-100 text-green-800' : 
                    currentRide ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {isAvailable ? 'Available' : currentRide ? 'On Ride' : 'Unavailable'}
                  </span>
                </div>
                <button
                  onClick={handleToggleAvailability}
                  disabled={loading || currentRide}
                  className={`w-full px-6 py-3 rounded-lg font-semibold transition-colors ${
                    isAvailable
                      ? 'bg-red-600 text-white hover:bg-red-700'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  } disabled:bg-gray-400 disabled:cursor-not-allowed`}
                  title={currentRide ? 'Complete your current ride first' : ''}
                >
                  {loading ? 'Updating...' : 
                   currentRide ? '⏸️ On Ride (Complete to toggle)' :
                   isAvailable ? '🔴 Go Offline' : '🟢 Go Online'}
                </button>
              </div>

              {/* Current Location */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-700 mb-2">Current Location</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Lat: {currentLocation.lat.toFixed(4)}</div>
                  <div>Lng: {currentLocation.lng.toFixed(4)}</div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Click on the map to update your location
                </p>
              </div>

              {/* Current Ride with OTP Input */}
              {currentRide && (
                <div className={`rounded-lg p-4 border-2 ${
                  showOTPInput ? 'bg-yellow-50 border-yellow-400' : 'bg-green-50 border-green-400'
                }`}>
                  <h3 className="font-semibold text-gray-700 mb-3">
                    {showOTPInput ? '🔐 Enter OTP to Start' : '🚨 Active Ride'}
                  </h3>
                  
                  <div className="text-sm text-gray-600 space-y-2 mb-4">
                    <div><span className="font-semibold">Ride ID:</span> {currentRide.ride_id}</div>
                    <div><span className="font-semibold">User ID:</span> {currentRide.user_id}</div>
                    <div><span className="font-semibold">Status:</span> {currentRide.status || 'accepted'}</div>
                    <div className="pt-2 border-t">
                      <div className="font-semibold mb-1">📍 Pickup:</div>
                      <div className="text-xs">{currentRide.pickup_location}</div>
                    </div>
                    <div>
                      <div className="font-semibold mb-1">🎯 Dropoff:</div>
                      <div className="text-xs">{currentRide.dropoff_location}</div>
                    </div>
                  </div>

                  {/* OTP Input Section */}
                  {showOTPInput && (
                    <div className="bg-white rounded-lg p-4 mb-4">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Enter OTP from User
                      </label>
                      <input
                        type="text"
                        maxLength={4}
                        value={enteredOTP}
                        onChange={(e) => {
                          const value = e.target.value.replace(/\D/g, '');
                          setEnteredOTP(value);
                          setOtpError('');
                        }}
                        placeholder="4-digit OTP"
                        className="w-full px-4 py-3 text-center text-2xl font-bold tracking-widest border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                      {otpError && (
                        <p className="text-xs text-red-600 mt-2">{otpError}</p>
                      )}
                      <button
                        onClick={handleVerifyOTP}
                        disabled={loading || enteredOTP.length !== 4}
                        className="w-full mt-3 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                      >
                        {loading ? 'Verifying...' : '✅ Verify & Start Ride'}
                      </button>
                    </div>
                  )}

                  {/* Complete Ride Button (only show after OTP verified) */}
                  {!showOTPInput && (
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
                            alert(`✅ Ride ${currentRide.ride_id} completed!\nYou are now available for new rides.`);
                            setCurrentRide(null);
                            setIsAvailable(true);
                            await setDriverAvailability(
                              driverId.startsWith('DRIVER-') ? driverId : `DRIVER-${driverId}`,
                              true
                            );
                          } else {
                            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                            alert(`Failed to complete ride: ${errorData.detail || 'Please try again.'}`);
                          }
                        } catch (error: any) {
                          alert(`Failed to complete ride: ${error.message}`);
                        } finally {
                          setLoading(false);
                        }
                      }}
                      disabled={loading}
                      className="w-full bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      {loading ? 'Completing...' : '🏁 Complete Ride'}
                    </button>
                  )}
                </div>
              )}

              <button
                onClick={() => {
                  setIsRegistered(false);
                  setIsAvailable(false);
                  setStatus(null);
                }}
                className="w-full bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700 transition-colors"
              >
                Logout
              </button>
            </div>
          )}
        </div>

        {/* Map */}
        <div className="flex-1 relative">
          {isRegistered && (
            <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3">
              <div className="text-xs text-gray-600 mb-1">Click to update location:</div>
              <div className="font-bold text-lg text-green-600">
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