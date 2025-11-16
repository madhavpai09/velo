import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAllRideRequests } from '../utils/api';

interface RideData {
  id: number;
  source_location: string;
  dest_location: string;
  user_id: number;
  status: string;
  created_at: string;
}

export default function Ride() {
  const navigate = useNavigate();
  const [rides, setRides] = useState<RideData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRides();
    const interval = setInterval(fetchRides, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchRides = async () => {
    try {
      const data = await getAllRideRequests();
      setRides(data);
    } catch (error) {
      console.error('Failed to fetch rides:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'matched': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button 
                onClick={() => navigate('/user')}
                className="text-2xl hover:scale-110 transition-transform"
              >
                ←
              </button>
              <div>
                <h1 className="text-3xl font-bold">All Rides</h1>
                <p className="text-sm text-blue-200">View and track rides</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/user')}
                className="bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
              >
                New Ride
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

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        {loading ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">⏳</div>
            <p className="text-gray-600">Loading rides...</p>
          </div>
        ) : rides.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">🚗</div>
            <p className="text-gray-600 mb-4">No rides yet</p>
            <button
              onClick={() => navigate('/user')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700"
            >
              Request Your First Ride
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {rides.map((ride) => (
              <div 
                key={ride.id}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-lg font-bold text-gray-800">
                    Ride #{ride.id}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(ride.status)}`}>
                    {ride.status}
                  </span>
                </div>

                <div className="space-y-3 text-sm">
                  <div>
                    <div className="text-gray-500 text-xs mb-1">📍 Pickup</div>
                    <div className="font-mono text-gray-800">{ride.source_location}</div>
                  </div>

                  <div>
                    <div className="text-gray-500 text-xs mb-1">🎯 Dropoff</div>
                    <div className="font-mono text-gray-800">{ride.dest_location}</div>
                  </div>

                  <div className="pt-3 border-t flex items-center justify-between text-xs text-gray-500">
                    <span>User: {ride.user_id}</span>
                    <span>{new Date(ride.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}