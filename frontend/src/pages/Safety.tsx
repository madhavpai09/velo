import { useNavigate } from 'react-router-dom';

export default function Safety() {
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

            <div className="max-w-4xl mx-auto px-6 py-16">
                <h1 className="text-5xl font-bold mb-8 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    Safety
                </h1>
                <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20">
                    <p className="text-gray-600 text-lg mb-4">Enter your content here</p>
                    <p className="text-gray-500">This page is under construction. Add safety guidelines, features, and protocols here.</p>
                </div>
            </div>
        </div>
    );
}
