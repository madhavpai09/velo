import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

export default function HelpCenter() {
    const navigate = useNavigate();
    const [openFaq, setOpenFaq] = useState<number | null>(null);

    const faqs = [
        {
            question: "How do I book a ride?",
            answer: "Simply log in to your account, select your pickup and drop-off locations on the map, choose your ride type, and tap 'Request Ride'. A nearby driver will be assigned to you within seconds."
        },
        {
            question: "What is the School Pool Pass?",
            answer: "School Pool Pass is our premium service for parents who want safe, reliable transportation for their children to and from school. All drivers are specially verified, routes are optimized for safety, and parents receive real-time updates."
        },
        {
            question: "How does OTP verification work?",
            answer: "When a driver accepts your ride, you'll receive a unique 4-digit OTP. Before starting the ride, verify this OTP with your driver to ensure you're getting into the correct vehicle. This adds an extra layer of security."
        },
        {
            question: "Can I track my ride in real-time?",
            answer: "Yes! Once your ride is confirmed, you can track your driver's location in real-time on the map. You can also share your trip details with family and friends for added safety."
        },
        {
            question: "How is the fare calculated?",
            answer: "Our fares are transparent and calculated based on distance and ride type. You'll see the estimated fare before confirming your ride. We don't have surge pricing—what you see is what you pay."
        },
        {
            question: "What if I need to cancel my ride?",
            answer: "You can cancel your ride anytime before the driver arrives. Simply tap the 'Cancel Request' button. If the driver has already arrived, cancellation fees may apply."
        },
        {
            question: "How do I add a student for School Pool Pass?",
            answer: "Go to the School Pool section, click 'Add Student', fill in your child's details and school information, then select a route and subscription plan. A verified driver will be assigned to your child's route."
        },
        {
            question: "What payment methods do you accept?",
            answer: "We accept all major payment methods including credit/debit cards, UPI, and digital wallets. Payment is processed securely through our app."
        },
        {
            question: "How do I rate my driver?",
            answer: "After your ride is completed, you'll be prompted to rate your driver on a scale of 1-5 stars. You can also leave optional comments to help us maintain service quality."
        },
        {
            question: "What should I do if I left something in the vehicle?",
            answer: "Contact our support team immediately with your ride details. We'll help you connect with your driver to retrieve your lost item."
        }
    ];

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
                    Help Center
                </h1>
                <p className="text-xl text-gray-600 mb-12">We're here to help. Find answers to common questions below.</p>

                {/* Quick Contact */}
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-8 rounded-3xl shadow-xl mb-8">
                    <h2 className="text-2xl font-bold mb-4">Need Immediate Assistance?</h2>
                    <p className="mb-6">Our support team is available 24/7 to help you with any questions or concerns.</p>
                    <div className="grid md:grid-cols-3 gap-4">
                        <div className="bg-white/20 backdrop-blur-sm p-4 rounded-xl">
                            <p className="text-sm mb-2">Call Us</p>
                            <p className="text-xl font-bold">+91 9019126856</p>
                            <p className="text-xs mt-1 opacity-80">Available 24/7</p>
                        </div>
                        <div className="bg-white/20 backdrop-blur-sm p-4 rounded-xl">
                            <p className="text-sm mb-2">Email Support</p>
                            <p className="text-xl font-bold">support@velocabs.com</p>
                            <p className="text-xs mt-1 opacity-80">Response within 24 hours</p>
                        </div>
                        <div className="bg-white/20 backdrop-blur-sm p-4 rounded-xl">
                            <p className="text-sm mb-2">In-App Chat</p>
                            <p className="text-xl font-bold">Live Support</p>
                            <p className="text-xs mt-1 opacity-80">Instant responses</p>
                        </div>
                    </div>
                </div>

                {/* FAQ Section */}
                <div className="mb-8">
                    <h2 className="text-3xl font-bold mb-6">Frequently Asked Questions</h2>
                    <div className="space-y-4">
                        {faqs.map((faq, index) => (
                            <div key={index} className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-lg border border-white/20 overflow-hidden">
                                <button
                                    onClick={() => setOpenFaq(openFaq === index ? null : index)}
                                    className="w-full p-6 text-left flex justify-between items-center hover:bg-gray-50 transition-colors"
                                >
                                    <span className="font-bold text-lg pr-4">{faq.question}</span>
                                    <span className="text-2xl text-gray-400 flex-shrink-0">
                                        {openFaq === index ? '−' : '+'}
                                    </span>
                                </button>
                                {openFaq === index && (
                                    <div className="px-6 pb-6 text-gray-700 leading-relaxed">
                                        {faq.answer}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>


                {/* For Drivers */}
                <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-8 rounded-3xl shadow-xl border border-gray-200 mb-8">
                    <h2 className="text-2xl font-bold mb-4">Are You a Driver?</h2>
                    <p className="text-gray-700 mb-6">
                        Looking for information about driving with VELO? We have a dedicated support center for our driver partners.
                    </p>
                    <button
                        onClick={() => navigate('/driver')}
                        className="bg-black text-white px-6 py-3 rounded-xl font-bold hover:bg-gray-800 transition-colors"
                    >
                        Visit Driver Support
                    </button>
                </div>

                {/* Still Need Help */}
                <div className="text-center bg-white/80 backdrop-blur-lg p-12 rounded-3xl shadow-xl border border-white/20">
                    <h2 className="text-3xl font-bold mb-4">Still Need Help?</h2>
                    <p className="text-gray-600 mb-8 text-lg">Can't find what you're looking for? Our support team is ready to assist you.</p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <button className="bg-black text-white px-8 py-4 rounded-xl font-bold hover:bg-gray-800 transition-all hover:scale-105 shadow-lg">
                            Contact Support
                        </button>
                        <button
                            onClick={() => navigate('/safety')}
                            className="bg-white text-black border-2 border-black px-8 py-4 rounded-xl font-bold hover:bg-gray-50 transition-all hover:scale-105"
                        >
                            Safety Center
                        </button>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="bg-black text-white py-8 px-6 text-center">
                <p className="text-gray-400">© 2025 VELO Cabs. Here to help, 24/7.</p>
            </footer>
        </div>
    );
}
