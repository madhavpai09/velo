import { useNavigate } from 'react-router-dom';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Logo and Title */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-4 mb-6">
            <img src="/0796f710-7ecb-4a40-8176-2eba9ee3c5cd.png" alt="VELO" className="w-20 h-20" />
            <h1 className="text-6xl font-bold text-white">VELO</h1>
          </div>
          <p className="text-2xl text-white/90">Your Ride, Your Way</p>
        </div>

        {/* Role Selection Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* User Card */}
          <div 
            onClick={() => navigate('/user')}
            className="bg-white rounded-2xl p-8 shadow-2xl cursor-pointer transform transition-all hover:scale-105 hover:shadow-3xl"
          >
            <div className="text-center">
              <div className="text-6xl mb-4">🚗</div>
              <h2 className="text-3xl font-bold text-gray-800 mb-3">I'm a Rider</h2>
              <p className="text-gray-600 mb-6">
                Book a ride to your destination quickly and safely
              </p>
              <div className="space-y-2 text-left text-sm text-gray-500">
                <div>✓ Real-time driver tracking</div>
                <div>✓ Multiple payment options</div>
                <div>✓ Safe and secure rides</div>
              </div>
              <button className="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                Request a Ride
              </button>
            </div>
          </div>

          {/* Driver Card */}
          <div 
            onClick={() => navigate('/driver')}
            className="bg-white rounded-2xl p-8 shadow-2xl cursor-pointer transform transition-all hover:scale-105 hover:shadow-3xl"
          >
            <div className="text-center">
              <div className="text-6xl mb-4">🚕</div>
              <h2 className="text-3xl font-bold text-gray-800 mb-3">I'm a Driver</h2>
              <p className="text-gray-600 mb-6">
                Drive and earn money on your own schedule
              </p>
              <div className="space-y-2 text-left text-sm text-gray-500">
                <div>✓ Flexible working hours</div>
                <div>✓ Instant ride notifications</div>
                <div>✓ Easy earnings tracking</div>
              </div>
              <button className="mt-6 w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors">
                Start Driving
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-white/80">
          <p className="text-sm">Powered by VELO • Safe, Fast, Reliable</p>
        </div>
      </div>
    </div>
  );
}