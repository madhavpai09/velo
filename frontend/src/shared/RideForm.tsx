interface AssignedDriver {
  driver_id: number;
  driver_name: string;
  driver_location: string;
  pickup_location: string;
  dropoff_location: string;
}

interface RideFormProps {
  pickupLocation: { lat: number; lng: number } | null;
  dropoffLocation: { lat: number; lng: number } | null;
  onRequestRide: () => void;
  loading: boolean;
  rideId: number | null;
  drivers: Array<{ driver_id: number; lat: number; lng: number }>;
  selectionMode: 'pickup' | 'dropoff';
  onSelectionModeChange: (mode: 'pickup' | 'dropoff') => void;
  waitingForDriver?: boolean;
  assignedDriver?: AssignedDriver | null;
  onNewRide?: () => void;
}

export default function RideForm({
  pickupLocation,
  dropoffLocation,
  onRequestRide,
  loading,
  rideId,
  drivers,
  selectionMode,
  onSelectionModeChange,
  waitingForDriver = false,
  assignedDriver = null,
  onNewRide
}: RideFormProps) {
  const canRequestRide = pickupLocation && dropoffLocation && !loading && !assignedDriver;

  return (
    <div className="h-full flex flex-col bg-white shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
        <h2 className="text-2xl font-bold mb-2">Request a Ride</h2>
        <p className="text-sm text-blue-100">Click on map to set locations</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Driver Assigned View */}
        {assignedDriver ? (
          <div className="space-y-4">
            <div className="bg-green-100 border-2 border-green-400 rounded-lg p-6 text-center">
              <div className="text-6xl mb-4">✅</div>
              <div className="text-2xl font-bold text-green-800 mb-2">
                Driver Assigned!
              </div>
              <div className="bg-white rounded-lg p-4 mb-4">
                <div className="text-3xl mb-2">🚗</div>
                <div className="text-xl font-bold text-gray-800">
                  {assignedDriver.driver_name}
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  ID: {assignedDriver.driver_id}
                </div>
              </div>
              
              <div className="text-left space-y-2 mb-4">
                <div className="bg-green-50 p-3 rounded">
                  <div className="text-xs text-gray-600">Pickup</div>
                  <div className="font-mono text-sm">{assignedDriver.pickup_location}</div>
                </div>
                <div className="bg-red-50 p-3 rounded">
                  <div className="text-xs text-gray-600">Dropoff</div>
                  <div className="font-mono text-sm">{assignedDriver.dropoff_location}</div>
                </div>
              </div>

              {onNewRide && (
                <button
                  onClick={onNewRide}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700"
                >
                  Request Another Ride
                </button>
              )}
            </div>
          </div>
        ) : (
          <>
            {/* Selection Mode Buttons */}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <button
                onClick={() => onSelectionModeChange('pickup')}
                disabled={waitingForDriver}
                className={`py-3 px-4 rounded-lg font-semibold transition-all ${
                  selectionMode === 'pickup'
                    ? 'bg-green-500 text-white shadow-lg scale-105'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                } ${waitingForDriver ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                📍 Pickup
              </button>
              <button
                onClick={() => onSelectionModeChange('dropoff')}
                disabled={waitingForDriver}
                className={`py-3 px-4 rounded-lg font-semibold transition-all ${
                  selectionMode === 'dropoff'
                    ? 'bg-red-500 text-white shadow-lg scale-105'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                } ${waitingForDriver ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                🎯 Dropoff
              </button>
            </div>

            {/* Instruction */}
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 flex items-center gap-2">
                <span className="text-lg">💡</span>
                <span>
                  Click the <span className="font-bold">{selectionMode}</span> button above, 
                  then click on the map to set location
                </span>
              </p>
            </div>

            {/* Location Cards */}
            <div className="space-y-4 mb-6">
              <div className={`p-4 rounded-lg border-2 transition-all ${
                pickupLocation 
                  ? 'bg-green-50 border-green-300' 
                  : 'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-gray-700">Pickup Location</span>
                  {pickupLocation && <span className="text-green-600 text-xl">✓</span>}
                </div>
                <div className="text-sm text-gray-600 font-mono">
                  {pickupLocation 
                    ? `${pickupLocation.lat.toFixed(6)}, ${pickupLocation.lng.toFixed(6)}`
                    : 'Not selected'
                  }
                </div>
              </div>

              <div className={`p-4 rounded-lg border-2 transition-all ${
                dropoffLocation 
                  ? 'bg-red-50 border-red-300' 
                  : 'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-gray-700">Dropoff Location</span>
                  {dropoffLocation && <span className="text-red-600 text-xl">✓</span>}
                </div>
                <div className="text-sm text-gray-600 font-mono">
                  {dropoffLocation 
                    ? `${dropoffLocation.lat.toFixed(6)}, ${dropoffLocation.lng.toFixed(6)}`
                    : 'Not selected'
                  }
                </div>
              </div>
            </div>

            {/* Request Button */}
            <button
              onClick={onRequestRide}
              disabled={!canRequestRide || waitingForDriver}
              className={`w-full py-4 rounded-lg font-bold text-lg transition-all ${
                canRequestRide && !waitingForDriver
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⏳</span>
                  Requesting...
                </span>
              ) : waitingForDriver ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-pulse">🔍</span>
                  Waiting for Driver...
                </span>
              ) : (
                '🚗 Request Ride'
              )}
            </button>

            {/* Waiting Status */}
            {waitingForDriver && rideId && (
              <div className="mt-6 p-4 bg-yellow-100 border-2 border-yellow-400 rounded-lg animate-pulse">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl animate-spin">⏳</span>
                  <span className="font-bold text-yellow-800 text-lg">Finding Driver...</span>
                </div>
                <div className="text-sm text-yellow-700 mb-1">
                  <span className="font-semibold">Ride ID:</span> {rideId}
                </div>
                <div className="text-xs text-yellow-600">
                  Checking for available drivers...
                </div>
              </div>
            )}

            {/* Available Drivers */}
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-lg">Available Drivers</h3>
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                  {drivers.length}
                </span>
              </div>

              {drivers.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <div className="text-4xl mb-2">🚗</div>
                  <p className="text-sm">No drivers available</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {drivers.map((driver) => (
                    <div 
                      key={driver.driver_id}
                      className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                    >
                      <span className="text-2xl">🚗</span>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-800">
                          Driver {driver.driver_id}
                        </div>
                        <div className="text-xs text-gray-500 font-mono">
                          {driver.lat.toFixed(4)}, {driver.lng.toFixed(4)}
                        </div>
                      </div>
                      <span className="text-xs text-green-600 font-semibold">
                        ● Online
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}