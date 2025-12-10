import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

export default function Landing() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('ride');

  return (
    <div className="min-h-screen flex flex-col font-sans text-gray-900">
      {/* Header */}
      <header className="bg-black text-white py-4 px-6 md:px-16 flex justify-between items-center">
        <div className="flex items-center gap-8">
          <div className="text-2xl font-normal tracking-tight cursor-pointer" onClick={() => navigate('/')}>VELO Cabs</div>
          <nav className="hidden md:flex gap-6 text-sm font-medium">
            <button onClick={() => navigate('/ride')} className="hover:text-gray-300">Ride</button>
            <button onClick={() => navigate('/driver')} className="hover:text-gray-300">Drive</button>
            <button className="hover:text-gray-300">Business</button>
            <button onClick={() => navigate('/admin')} className="hover:text-gray-300">Admin</button>
            <button className="hover:text-gray-300">About</button>
          </nav>
        </div>
        <div className="flex items-center gap-4 text-sm font-medium">
          <button className="hidden md:block hover:text-gray-300">EN</button>
          <button className="hidden md:block hover:text-gray-300">Help</button>
          <button className="hidden md:block hover:text-gray-300">Log in</button>
          <button className="bg-white text-black px-3 py-1.5 rounded-full hover:bg-gray-200 transition-colors">
            Sign up
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-grow relative bg-[url('https://images.unsplash.com/photo-1557404763-69708cd8b9ce?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80')] bg-cover bg-center">
        <div className="absolute inset-0 bg-black/10"></div> {/* Overlay */}

        <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-16 pt-12 md:pt-20 pb-20">
          <div className="bg-white max-w-lg w-full rounded-lg shadow-xl overflow-hidden">
            {/* Tabs */}
            <div className="flex border-b border-gray-100">
              <button
                className={`flex-1 py-4 text-center font-medium flex flex-col items-center gap-2 ${activeTab === 'ride' ? 'border-b-2 border-black text-black' : 'text-gray-500 hover:text-gray-700'}`}
                onClick={() => setActiveTab('ride')}
              >
                <span className="text-xl"></span>
                <span>Ride</span>
              </button>
              <button
                className={`flex-1 py-4 text-center font-medium flex flex-col items-center gap-2 ${activeTab === 'drive' ? 'border-b-2 border-black text-black' : 'text-gray-500 hover:text-gray-700'}`}
                onClick={() => setActiveTab('drive')}
              >
                <span className="text-xl"></span>
                <span>Drive</span>
              </button>
            </div>

            {/* Tab Content */}
            <div className="p-8">
              {activeTab === 'ride' ? (
                <div className="space-y-6">
                  <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-4">
                    Request a ride now
                  </h1>
                  <div className="space-y-4">
                    <div className="relative">
                      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">📍</div>
                      <input
                        type="text"
                        placeholder="Enter pickup location"
                        className="w-full bg-gray-100 p-3 pl-12 rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
                      />
                    </div>
                    <div className="relative">
                      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🏁</div>
                      <input
                        type="text"
                        placeholder="Enter destination"
                        className="w-full bg-gray-100 p-3 pl-12 rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
                      />
                    </div>
                  </div>
                  <div className="pt-2">
                    <button
                      onClick={() => navigate('/ride')}
                      className="bg-black text-white font-medium py-3 px-6 rounded-lg text-lg hover:bg-gray-800 transition-colors"
                    >
                      Request Now
                    </button>
                    <button
                      className="ml-4 bg-gray-100 text-black font-medium py-3 px-6 rounded-lg text-lg hover:bg-gray-200 transition-colors"
                    >
                      Schedule for later
                    </button>
                  </div>

                  {/* School Pool Promo */}
                  <div
                    onClick={() => setActiveTab('school')}
                    className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-xl cursor-pointer hover:bg-yellow-100 transition-colors flex items-center gap-4"
                  >
                    <div className="text-4xl">🎒</div>
                    <div>
                      <div className="font-bold text-lg">School Pool Pass</div>
                      <div className="text-sm text-gray-600">Safe, priority rides for students. Get started →</div>
                    </div>
                  </div>
                </div>
              ) : activeTab === 'school' ? (
                <div className="space-y-6">
                  <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-4">
                    School Pool Pass
                  </h1>
                  <p className="text-gray-600 text-lg">
                    Safe, reliable, and priority rides for your children.
                  </p>
                  <div className="flex gap-4">
                    <button
                      onClick={() => navigate('/school-pool')}
                      className="bg-black text-white font-medium py-3 px-6 rounded-lg text-lg hover:bg-gray-800 transition-colors"
                    >
                      Get Started
                    </button>
                  </div>
                  <div className="pt-4 border-t border-gray-100 mt-4">
                    <p className="text-sm text-gray-500">Includes verified safe drivers and real-time tracking.</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-4">
                    Ahoy! Captain
                  </h1>
                  <p className="text-gray-600 text-lg">
                    Drive on the platform with the fastest growing network of active riders.
                  </p>
                  <button
                    onClick={() => navigate('/driver')}
                    className="bg-black text-white font-medium py-3 px-6 rounded-lg text-lg hover:bg-gray-800 transition-colors"
                  >
                    Sign up to drive
                  </button>
                  <div className="pt-4 border-t border-gray-100 mt-4">
                    <a href="#" className="text-black underline font-medium">Learn more about driving and delivering</a>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Footer Simple */}
      <footer className="bg-black text-white py-12 px-6 md:px-16">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          <div>
            <h3 className="text-xl mb-4">Velo</h3>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><button onClick={() => navigate('/help')} className="hover:text-white">Visit Help Center</button></li>
            </ul>
          </div>
          <div>
            <h3 className="text-xl mb-4">Company</h3>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><button onClick={() => navigate('/about')} className="hover:text-white">About us</button></li>
              <li><a href="#" className="hover:text-white">Our offerings</a></li>
              <li><a href="#" className="hover:text-white">Investors</a></li>
              <li><a href="#" className="hover:text-white">Blog</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-xl mb-4">Products</h3>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><button onClick={() => navigate('/ride')} className="hover:text-white">Ride</button></li>
              <li><button onClick={() => navigate('/driver')} className="hover:text-white">Drive</button></li>
              <li><button onClick={() => navigate('/school-pool')} className="hover:text-white">School pool pass</button></li>
              <li><a href="#" className="hover:text-white">Velo for Business</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-xl mb-4">Global citizenship</h3>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><button onClick={() => navigate('/safety')} className="hover:text-white">Safety</button></li>
              <li><a href="#" className="hover:text-white">Diversity and Inclusion</a></li>
              <li><a href="#" className="hover:text-white">Sustainability</a></li>
            </ul>
          </div>
        </div>

        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center pt-8 border-t border-gray-800 text-gray-400 text-sm">
          <div className="mb-4 md:mb-0">
            © 2025 Velo Cabs Inc.
          </div>
          <div className="flex gap-6">
            <a href="#" className="hover:text-white">Privacy</a>
            <a href="#" className="hover:text-white">Accessibility</a>
            <a href="#" className="hover:text-white">Terms</a>
          </div>
        </div>
      </footer >
    </div >
  );
}