import { useNavigate } from 'react-router-dom';

export default function AboutUs() {
    const navigate = useNavigate();

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
                    About VELO Cabs
                </h1>
                <p className="text-xl text-gray-600 mb-12">Reimagining urban mobility, one ride at a time.</p>

                {/* Founder's Message */}
                <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20 mb-8">
                    <div className="flex items-start gap-6 mb-6">
                        <div>
                            <h2 className="text-2xl font-bold mb-2">A Message from Our Founder</h2>
                            <p className="text-gray-500 text-sm">Building trust, one journey at a time</p>
                        </div>
                    </div>
                    <div className="text-gray-700 space-y-4 leading-relaxed">
                        <p className="text-lg">
                            "When I started VELO Cabs, I had one simple question: <span className="font-semibold italic">What if getting around your city felt as safe and reliable as having a trusted friend pick you up?</span>"
                        </p>
                        <p>
                            As a parent myself, I know the anxiety of ensuring your child gets to school safely. As a commuter, I've experienced the frustration of unreliable rides and hidden fees. These aren't just business problems—they're personal ones.
                        </p>
                        <p>
                            That's why we built VELO differently. Every driver is verified. Every ride is tracked. Every price is transparent. Our School Pool Pass isn't just a feature—it's a promise to parents that their children are in safe hands.
                        </p>
                        <p>
                            We're not trying to be the biggest ride-sharing platform. We're trying to be the most trusted one. Because at the end of the day, we're not just moving people from point A to point B—we're taking care of someone's parent, child, or friend.
                        </p>
                        <p className="font-semibold pt-4">
                            Thank you for trusting us with your journeys.
                        </p>
                        <p className="text-gray-500 italic">
                            — The VELO Team
                        </p>
                    </div>
                </div>

                {/* Our Story */}
                <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20 mb-8">
                    <h2 className="text-3xl font-bold mb-6">Our Story</h2>
                    <p className="text-gray-700 leading-relaxed mb-4">
                        VELO Cabs was born from a simple belief: getting around your city should be safe, reliable, and stress-free. We're reimagining urban mobility by putting people first—whether you're commuting to work, heading out for the evening, or ensuring your child gets to school safely.
                    </p>
                    <p className="text-gray-700 leading-relaxed">
                        We're more than just rides—we're your partner in safe, convenient transportation.
                    </p>
                </div>

                {/* What We Do */}
                <div className="grid md:grid-cols-2 gap-6 mb-8">
                    <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20">
                        <div className="text-4xl mb-4"></div>
                        <h3 className="text-2xl font-bold mb-4">For Riders</h3>
                        <ul className="space-y-3 text-gray-700">
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Quick, affordable rides whenever you need them</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Real-time tracking so you always know where your ride is</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>Transparent pricing with no hidden fees</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-green-500 mt-1">✓</span>
                                <span>24/7 customer support</span>
                            </li>
                        </ul>
                    </div>

                    <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-8 rounded-3xl shadow-xl border border-yellow-200">
                        <div className="text-4xl mb-4"></div>
                        <h3 className="text-2xl font-bold mb-4">School Pool Pass</h3>
                        <p className="text-gray-700 mb-4">
                            Designed specifically for parents who want peace of mind.
                        </p>
                        <ul className="space-y-3 text-gray-700">
                            <li className="flex items-start gap-3">
                                <span className="text-orange-500 mt-1">★</span>
                                <span>Every driver verified and background-checked</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-orange-500 mt-1">★</span>
                                <span>Routes optimized for safety</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-orange-500 mt-1">★</span>
                                <span>Real-time updates on your child's journey</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-orange-500 mt-1">★</span>
                                <span>OTP verification for secure pickups</span>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Our Values */}
                <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20 mb-8">
                    <h2 className="text-3xl font-bold mb-8 text-center">Our Values</h2>
                    <div className="grid md:grid-cols-2 gap-8">
                        <div>
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <span className="text-2xl"></span> Safety First
                            </h3>
                            <p className="text-gray-700">
                                Every driver undergoes rigorous verification. Every ride is tracked. Your safety isn't just a feature—it's our foundation.
                            </p>
                        </div>
                        <div>
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <span className="text-2xl"></span> Trust & Transparency
                            </h3>
                            <p className="text-gray-700">
                                No surge pricing surprises. No hidden fees. What you see is what you pay.
                            </p>
                        </div>
                        <div>
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <span className="text-2xl"></span> Community Focused
                            </h3>
                            <p className="text-gray-700">
                                We're not just a service; we're part of your community. From school runs to late-night rides home, we're here for you.
                            </p>
                        </div>
                        <div>
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <span className="text-2xl"></span> Innovation with Purpose
                            </h3>
                            <p className="text-gray-700">
                                We use technology to make transportation better, not just faster. Real-time tracking, OTP verification, and smart routing—all designed to give you confidence.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Why VELO */}
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-8 rounded-3xl shadow-xl mb-8">
                    <h2 className="text-3xl font-bold mb-4">Why VELO?</h2>
                    <p className="text-lg leading-relaxed">
                        Because you deserve better than just "getting from A to B." You deserve reliability. Safety. Peace of mind. Whether it's your daily commute or your child's ride to school, we're committed to making every journey count.
                    </p>
                </div>

                {/* CTA */}
                <div className="text-center bg-white/80 backdrop-blur-lg p-12 rounded-3xl shadow-xl border border-white/20">
                    <h2 className="text-3xl font-bold mb-4">Ready to Experience the Difference?</h2>
                    <p className="text-gray-600 mb-8 text-lg">Join thousands of riders who trust VELO for their daily journeys.</p>
                    <button
                        onClick={() => navigate('/login')}
                        className="bg-black text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-gray-800 transition-all hover:scale-105 shadow-lg"
                    >
                        Get Started Today
                    </button>
                </div>
            </div>

            {/* Footer */}
            <footer className="bg-black text-white py-8 px-6 text-center">
                <p className="text-gray-400">© 2025 VELO Cabs. Making every journey matter.</p>
            </footer>
        </div>
    );
}
