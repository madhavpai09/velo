import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

export default function Safety() {
    const navigate = useNavigate();
    const [openFaq, setOpenFaq] = useState<number | null>(null);

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
            <header className="bg-black text-white py-4 px-6 md:px-16 flex justify-between items-center">
                <div className="text-2xl font-normal tracking-tight cursor-pointer" onClick={() => navigate('/')}>
                    VELO Cabs
                </div>
                <button onClick={() => navigate('/')} className="text-sm hover:text-gray-300">
                    ← Back to Home
                </button>
            </header>

            <div className="max-w-5xl mx-auto px-6 py-16">
                <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-black to-black bg-clip-text text-transparent">
                    Your Safety is Our Priority
                </h1>
                <p className="text-xl text-gray-600 mb-12">Every ride, every time. Here's how we keep you safe.</p>

                {/* Safety Promise */}
                <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white p-8 rounded-3xl shadow-xl mb-8">
                    <h2 className="text-3xl font-bold mb-4">Our Safety Promise</h2>
                    <p className="text-lg leading-relaxed">
                        At VELO Cabs, safety isn't just a feature—it's the foundation of everything we do. From the moment you request a ride to when you reach your destination, we've built multiple layers of protection to ensure your journey is secure and worry-free.
                    </p>
                </div>

                {/* Safety Features Grid */}
                <div className="grid md:grid-cols-2 gap-6 mb-8">
                    <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20">
                        <div className="text-4xl mb-4"></div>
                        <h3 className="text-2xl font-bold mb-4">Driver Verification</h3>
                        <ul className="space-y-3 text-gray-700">
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Comprehensive background checks for all drivers</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Valid driver's license and vehicle registration verification</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Regular safety training and updates</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Continuous monitoring and rating system</span>
                            </li>
                        </ul>
                    </div>

                    <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20">
                        <div className="text-4xl mb-4"></div>
                        <h3 className="text-2xl font-bold mb-4">Real-Time Tracking</h3>
                        <ul className="space-y-3 text-gray-700">
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>GPS tracking for every ride</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Share your trip details with family and friends</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Live location updates throughout your journey</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Route deviation alerts</span>
                            </li>
                        </ul>
                    </div>

                    <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20">
                        <div className="text-4xl mb-4"></div>
                        <h3 className="text-2xl font-bold mb-4">OTP Verification</h3>
                        <ul className="space-y-3 text-gray-700">
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Unique 4-digit OTP for every ride</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Verify your driver before starting the trip</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Prevents unauthorized pickups</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Extra security for School Pool Pass rides</span>
                            </li>
                        </ul>
                    </div>

                    <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20">
                        <div className="text-4xl mb-4"></div>
                        <h3 className="text-2xl font-bold mb-4">24/7 Support</h3>
                        <ul className="space-y-3 text-gray-700">
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Round-the-clock customer support</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Emergency assistance button in the app</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Dedicated safety team monitoring all rides</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Quick response to safety concerns</span>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* School Pool Safety */}
                <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-8 rounded-3xl shadow-xl border border-yellow-200 mb-8">
                    <h2 className="text-3xl font-bold mb-6">School Pool Pass: Extra Safety for Your Children</h2>
                    <p className="text-gray-700 mb-6">
                        When it comes to your children, we go above and beyond. Our School Pool Pass includes additional safety measures:
                    </p>
                    <div className="grid md:grid-cols-2 gap-4">
                        <div className="flex items-start gap-3">
                            <span className="text-orange-500 mt-1">★</span>
                            <span className="text-gray-700">Enhanced background checks for school drivers</span>
                        </div>
                        <div className="flex items-start gap-3">
                            <span className="text-orange-500 mt-1">★</span>
                            <span className="text-gray-700">Mandatory safety training certification</span>
                        </div>
                        <div className="flex items-start gap-3">
                            <span className="text-orange-500 mt-1">★</span>
                            <span className="text-gray-700">Parent notification for pickup and drop-off</span>
                        </div>
                        <div className="flex items-start gap-3">
                            <span className="text-orange-500 mt-1">★</span>
                            <span className="text-gray-700">Fixed routes and schedules</span>
                        </div>
                        <div className="flex items-start gap-3">
                            <span className="text-orange-500 mt-1">★</span>
                            <span className="text-gray-700">Maximum 3 students per driver for focused attention</span>
                        </div>
                        <div className="flex items-start gap-3">
                            <span className="text-orange-500 mt-1">★</span>
                            <span className="text-gray-700">Real-time location sharing with parents</span>
                        </div>
                    </div>
                </div>

                {/* Safety Tips */}
                <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20 mb-8">
                    <h2 className="text-3xl font-bold mb-6">Safety Tips for Riders</h2>
                    <div className="space-y-4 text-gray-700">
                        <div className="flex items-start gap-4">
                            <span className="text-2xl font-bold text-gray-300">1</span>
                            <div>
                                <h4 className="font-bold mb-1">Verify Your Driver</h4>
                                <p>Always check the driver's photo, name, and vehicle details before getting in. Match the OTP with your driver.</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-4">
                            <span className="text-2xl font-bold text-gray-300">2</span>
                            <div>
                                <h4 className="font-bold mb-1">Share Your Trip</h4>
                                <p>Use the trip sharing feature to let family or friends track your journey in real-time.</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-4">
                            <span className="text-2xl font-bold text-gray-300">3</span>
                            <div>
                                <h4 className="font-bold mb-1">Sit in the Back</h4>
                                <p>For solo rides, sitting in the back seat provides more personal space and safety.</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-4">
                            <span className="text-2xl font-bold text-gray-300">4</span>
                            <div>
                                <h4 className="font-bold mb-1">Trust Your Instincts</h4>
                                <p>If something doesn't feel right, don't hesitate to end the ride and contact our support team.</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-4">
                            <span className="text-2xl font-bold text-gray-300">5</span>
                            <div>
                                <h4 className="font-bold mb-1">Keep Personal Information Private</h4>
                                <p>Avoid sharing unnecessary personal details during your ride.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Emergency Contact */}
                <div className="bg-red-50 p-8 rounded-3xl shadow-xl border border-red-200 text-center">
                    <h2 className="text-2xl font-bold mb-4 text-red-800">In Case of Emergency</h2>
                    <p className="text-gray-700 mb-6">
                        If you feel unsafe at any time during your ride, use the emergency button in the app or contact us immediately.
                    </p>
                    <div className="flex flex-col md:flex-row gap-4 justify-center">
                        <div className="bg-white p-4 rounded-xl">
                            <p className="text-sm text-gray-500 mb-1">Emergency Helpline</p>
                            <p className="text-2xl font-bold text-red-600">Available 24/7</p>
                        </div>
                        <div className="bg-white p-4 rounded-xl">
                            <p className="text-sm text-gray-500 mb-1">Local Emergency</p>
                            <p className="text-2xl font-bold text-red-600">100 / 112</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="bg-black text-white py-8 px-6 text-center">
                <p className="text-gray-400">© 2025 VELO Cabs. Your safety is our commitment.</p>
            </footer>
        </div>
    );
}
