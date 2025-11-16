import { useNavigate } from 'react-router-dom';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-blue-600 to-blue-800 flex items-center justify-center">
      <div className="max-w-4xl w-full px-6">
        {/* Logo */}
        <div className="text-center mb-12 flex flex-col items-center">
  <img
    src="/0796f710-7ecb-4a40-8176-2eba9ee3c5cd.png"
    alt="VELO"
    className="w-40 h-40 mb-0"   // reduced gap
  />

  <p className="text-xl text-blue-100">Your ride, your way</p>
</div>


        {/* Login Options */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* User Login Card */}
          <div 
            onClick={() => navigate('/user')}
            className="bg-white rounded-2xl shadow-2xl p-8 cursor-pointer transform transition-all hover:scale-105 hover:shadow-3xl"
          >
            <div className="text-center">
              <div className="text-6xl mb-4">👤</div>
              <h2 className="text-3xl font-bold text-gray-800 mb-3">I'm a User</h2>
              <p className="text-gray-600 mb-6">
                Request rides and get to your destination quickly
              </p>
              <button className="w-full bg-blue-600 text-white px-6 py-4 rounded-lg font-semibold text-lg hover:bg-blue-700 transition-colors">
                Continue as User →
              </button>
            </div>
          </div>

          {/* Driver Login Card */}
          <div 
            onClick={() => navigate('/driver')}
            className="bg-white rounded-2xl shadow-2xl p-8 cursor-pointer transform transition-all hover:scale-105 hover:shadow-3xl"
          >
            <div className="text-center">
              <div className="text-6xl mb-4">🚗</div>
              <h2 className="text-3xl font-bold text-gray-800 mb-3">I'm a Driver</h2>
              <p className="text-gray-600 mb-6">
                Drive and earn by providing rides to users
              </p>
              <button className="w-full bg-green-600 text-white px-6 py-4 rounded-lg font-semibold text-lg hover:bg-green-700 transition-colors">
                Continue as Driver →
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-white/80 text-sm">
          <p>Choose your role to get started</p>
        </div>
      </div>
    </div>
  );
}

