import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../utils/api';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        
        try {
            // Use JSON endpoint to avoid form-data complexity
            const response = await api.post('/api/login/json', { email, password });
            await login(response.data.access_token);
            navigate('/ride');
        } catch (err: any) {
            setError(err.message || 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoogleSignIn = async (credentialResponse: any) => {
        setError('');
        setIsLoading(true);
        
        try {
            // Send ID token to backend for verification and user creation
            const response = await api.post('/api/auth/google', {
                id_token: credentialResponse.credential
            });
            
            await login(response.data.access_token);
            navigate('/ride');
        } catch (err: any) {
            setError(err.message || 'Google Sign-In failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 px-4">
            <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full">
                <h2 className="text-3xl font-bold mb-2 text-center text-gray-800">Welcome Back</h2>
                <p className="text-center text-gray-600 mb-6">Sign in to your VELO account</p>
                
                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
                        {error}
                    </div>
                )}
                
                {/* Google Sign-In Button */}
                <div className="mb-6">
                    <button
                        type="button"
                        onClick={() => {
                            // Note: This requires @react-oauth/google setup in main.tsx
                            // For now, this is a placeholder
                            setError('Google Sign-In requires additional setup. Use email/password for now.');
                        }}
                        className="w-full flex items-center justify-center gap-3 px-4 py-2.5 border-2 border-gray-300 rounded-lg hover:bg-gray-50 transition text-gray-700 font-medium"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        Sign in with Google
                    </button>
                    <p className="text-center text-xs text-gray-500 mt-2">Coming soon - Setup required</p>
                </div>
                
                <div className="relative mb-6">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-white text-gray-500">Or continue with email</span>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-gray-700 font-medium mb-2">Email Address</label>
                        <input
                            type="email"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition"
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div className="mb-6">
                        <label className="block text-gray-700 font-medium mb-2">Password</label>
                        <input
                            type="password"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                        <p className="text-xs text-gray-500 mt-1">🔒 Min 8 chars, 1 uppercase, 1 number, 1 special char</p>
                    </div>
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-black text-white py-2.5 rounded-lg hover:bg-gray-800 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-gray-600 text-sm">
                        Don't have an account?{' '}
                        <Link to="/signup" className="text-black font-semibold hover:underline">
                            Sign up
                        </Link>
                    </p>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-xs text-gray-500 text-center">
                        🔐 Your login is secure. We never store passwords.
                    </p>
                </div>
            </div>
        </div>
    );
}
