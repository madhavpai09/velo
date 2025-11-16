import { formatLocationForDisplay } from '../utils/locationUtils';

interface RideFormProps {
  pickupLocation: { lat: number; lng: number } | null;
  dropoffLocation: { lat: number; lng: number } | null;
  pickupAddress?: string;
  dropoffAddress?: string;
  onRequestRide: () => void;
  loading: boolean;
  rideId: number | null;
  drivers: any[];
  selectionMode: 'pickup' | 'dropoff';
  onSelectionModeChange: (mode: 'pickup' | 'dropoff') => void;
  waitingForDriver: boolean;
  assignedDriver: any;
  onNewRide: () => void;
}

export default function RideForm({
  pickupLocation,
  dropoffLocation,
  pickupAddress = '',
  dropoffAddress = '',
  onRequestRide,
  loading,
  rideId,
  drivers,
  selectionMode,
  onSelectionModeChange,
  waitingForDriver,
  assignedDriver,
  onNewRide
}: RideFormProps) {
  return (
    <div className="bg-white shadow-lg p-6 overflow-y-auto">
      {/* Assigned Driver Display */}
      {assignedDriver ? (
        <div className="space-y-4">
          <div className="bg-green-50 rounded-lg p-4 border-2 border-green-400">
            <h3 className="font-semibold text-gray-700 mb-3 text-center">✅ Driver Assigned!</h3>
            
            <div className="text-center mb-4">
              <div className="text-4xl mb-2">🚗</div>
              <div className="text-xl font-bold text-gray-800">{assignedDriver.driver_name}</div>
              <div className="text-sm text-gray-600">ID: {assignedDriver.driver_id}</div>
            </div>

            <div className="space-y-3 text-sm">
              <div className="bg-white p-3 rounded">
                <div className="font-semibold text-gray-700 mb-1">📍 Pickup:</div>
                <div className="text-gray-600">{assignedDriver.pickup_location}</div>
              </div>

              <div className="bg-white p-3 rounded">
                <div className="font-semibold text-gray-700 mb-1">🎯 Dropoff:</div>
                <div className="text-gray-600">{assignedDriver.dropoff_location}</div>
              </div>

              {assignedDriver.ride_id && (
                <div className="bg-white p-3 rounded">
                  <div className="font-semibold text-gray-700 mb-1">Ride ID:</div>
                  <div className="text-gray-600">{assignedDriver.ride_id}</div>
                </div>
              )}

              {assignedDriver.status && (
                <div className="bg-white p-3 rounded">
                  <div className="font-semibold text-gray-700 mb-1">Status:</div>
                  <div className="text-gray-600 capitalize">{assignedDriver.status.replace('_', ' ')}</div>
                </div>
              )}
            </div>

            <button
              onClick={onNewRide}
              className="w-full mt-4 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Request Another Ride
            </button>
          </div>
        </div>
      ) : waitingForDriver ? (
        /* Waiting for Driver */
        <div className="space-y-4">
          <div className="bg-blue-50 rounded-lg p-6 border-2 border-blue-400">
            <div className="text-center">
              <div className="text-6xl mb-3 animate-pulse">📡</div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">Finding Drivers...</h3>
              <p className="text-sm text-gray-600 mb-4">
                Broadcasting to nearby drivers. First to accept will be assigned!
              </p>
              
              <div className="bg-white p-4 rounded-lg space-y-2 text-sm text-left">
                <div>
                  <span className="font-semibold text-gray-700">📍 Pickup:</span>
                  <div className="text-gray-600 mt-1">{pickupAddress || 'Selected location'}</div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">🎯 Dropoff:</span>
                  <div className="text-gray-600 mt-1">{dropoffAddress || 'Selected location'}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Request Ride Form */
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Request a Ride</h2>
            <p className="text-sm text-gray-600">Click on map to set locations</p>
          </div>

          {/* Location Selection Toggles */}
          <div className="flex gap-2">
            <button
              onClick={() => onSelectionModeChange('pickup')}
              className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-colors ${
                selectionMode === 'pickup'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              📍 Set Pickup
            </button>
            <button
              onClick={() => onSelectionModeChange('dropoff')}
              className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-colors ${
                selectionMode === 'dropoff'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🎯 Set Dropoff
            </button>
          </div>

          {/* Selected Locations */}
          <div className="space-y-3">
            <div className={`p-4 rounded-lg border-2 ${
              pickupLocation ? 'bg-green-50 border-green-300' : 'bg-gray-50 border-gray-200'
            }`}>
              <div className="font-semibold text-gray-700 mb-1">📍 Pickup Location</div>
              {pickupLocation ? (
                <div className="text-sm text-gray-600">
                  <div className="font-medium">{pickupAddress || 'Getting address...'}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {pickupLocation.lat.toFixed(4)}, {pickupLocation.lng.toFixed(4)}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500">Click on map to select</div>
              )}
            </div>

            <div className={`p-4 rounded-lg border-2 ${
              dropoffLocation ? 'bg-red-50 border-red-300' : 'bg-gray-50 border-gray-200'
            }`}>
              <div className="font-semibold text-gray-700 mb-1">🎯 Dropoff Location</div>
              {dropoffLocation ? (
                <div className="text-sm text-gray-600">
                  <div className="font-medium">{dropoffAddress || 'Getting address...'}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {dropoffLocation.lat.toFixed(4)}, {dropoffLocation.lng.toFixed(4)}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500">Click on map to select</div>
              )}
            </div>
          </div>

          {/* Available Drivers Info */}
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-700">Available Drivers</span>
              <span className="text-2xl font-bold text-blue-600">{drivers.length}</span>
            </div>
          </div>

          {/* Request Ride Button */}
          <button
            onClick={onRequestRide}
            disabled={!pickupLocation || !dropoffLocation || loading}
            className="w-full bg-blue-600 text-white px-6 py-4 rounded-lg font-semibold text-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Creating Ride...' : '🚗 Request Ride'}
          </button>

          {(!pickupLocation || !dropoffLocation) && (
            <p className="text-xs text-center text-gray-500">
              Please select both pickup and dropoff locations
            </p>
          )}
        </div>
      )}
    </div>
  );
}