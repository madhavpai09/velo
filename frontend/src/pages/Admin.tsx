import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAllDrivers, verifyDriver, unverifyDriver, type AdminDriver, type AdminDriversResponse } from '../utils/api';

interface AdminUser {
    id: number;
    email: string;
    full_name: string;
    phone_number: string;
    total_rides: number;
    completed_rides: number;
    active_subscriptions: number;
    created_at: string;
}

export default function Admin() {
    const navigate = useNavigate();
    const [drivers, setDrivers] = useState<AdminDriver[]>([]);
    const [filteredDrivers, setFilteredDrivers] = useState<AdminDriver[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterStatus, setFilterStatus] = useState<'all' | 'verified' | 'unverified'>('all');
    const [stats, setStats] = useState({ total: 0, verified: 0, unverified: 0, online: 0 });
    const [processingId, setProcessingId] = useState<number | null>(null);
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
    const [activeTab, setActiveTab] = useState<'drivers' | 'users'>('drivers');
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [filteredUsers, setFilteredUsers] = useState<AdminUser[]>([]);
    const [userSearchQuery, setUserSearchQuery] = useState('');

    useEffect(() => {
        fetchDrivers();
        fetchUsers();

        // Auto-refresh every 3 seconds for real-time updates
        const interval = setInterval(() => {
            fetchDrivers(false); // Don't show loading spinner on auto-refresh
            if (activeTab === 'users') {
                fetchUsers(false);
            }
        }, 3000);

        return () => clearInterval(interval);
    }, [activeTab]);

    useEffect(() => {
        applyFilters();
    }, [searchQuery, filterStatus, drivers]);

    useEffect(() => {
        applyUserFilters();
    }, [userSearchQuery, users]);

    const fetchDrivers = async (showLoading = true) => {
        if (showLoading) {
            setLoading(true);
        }
        try {
            const data: AdminDriversResponse = await getAllDrivers();
            setDrivers(data.drivers);
            const onlineCount = data.drivers.filter(d => d.available).length;
            setStats({
                total: data.total_drivers,
                verified: data.verified_drivers,
                unverified: data.total_drivers - data.verified_drivers,
                online: onlineCount
            });
            setLastUpdate(new Date());
        } catch (error) {
            console.error('Failed to fetch drivers:', error);
        } finally {
            if (showLoading) {
                setLoading(false);
            }
        }
    };

    const applyFilters = () => {
        let filtered = [...drivers];

        // Apply search filter
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(d =>
                d.driver_id.toString().includes(query) ||
                d.name.toLowerCase().includes(query) ||
                d.phone_number?.toLowerCase().includes(query) ||
                d.vehicle_details?.toLowerCase().includes(query)
            );
        }

        // Apply status filter
        if (filterStatus === 'verified') {
            filtered = filtered.filter(d => d.is_verified_safe);
        } else if (filterStatus === 'unverified') {
            filtered = filtered.filter(d => !d.is_verified_safe);
        }

        setFilteredDrivers(filtered);
    };

    const fetchUsers = async (showLoading = true) => {
        if (showLoading) {
            setLoading(true);
        }
        try {
            const response = await fetch('http://localhost:8000/api/admin/users');
            const data = await response.json();
            setUsers(data.users);
            setLastUpdate(new Date());
        } catch (error) {
            console.error('Failed to fetch users:', error);
        } finally {
            if (showLoading) {
                setLoading(false);
            }
        }
    };

    const applyUserFilters = () => {
        let filtered = [...users];

        if (userSearchQuery) {
            const query = userSearchQuery.toLowerCase();
            filtered = filtered.filter(u =>
                u.id.toString().includes(query) ||
                u.full_name.toLowerCase().includes(query) ||
                u.email.toLowerCase().includes(query) ||
                u.phone_number?.toLowerCase().includes(query)
            );
        }

        setFilteredUsers(filtered);
    };

    const handleVerify = async (driverId: number) => {
        setProcessingId(driverId);
        try {
            await verifyDriver(driverId);
            await fetchDrivers();
        } catch (error) {
            console.error('Failed to verify driver:', error);
            alert('Failed to verify driver');
        } finally {
            setProcessingId(null);
        }
    };

    const handleUnverify = async (driverId: number) => {
        setProcessingId(driverId);
        try {
            await unverifyDriver(driverId);
            await fetchDrivers();
        } catch (error) {
            console.error('Failed to unverify driver:', error);
            alert('Failed to unverify driver');
        } finally {
            setProcessingId(null);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
            {/* Header */}
            <header className="bg-black/50 backdrop-blur-md border-b border-gray-700 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/')}
                            className="text-2xl font-bold tracking-tight hover:text-gray-300 transition-colors"
                        >
                            VELO Cabs
                        </button>
                        <span className="px-3 py-1 bg-purple-600 text-white text-xs font-bold rounded-full">
                            ADMIN
                        </span>
                        <span className="px-3 py-1 bg-red-600 text-white text-xs font-bold rounded-full flex items-center gap-1 animate-pulse">
                            <span className="w-2 h-2 bg-white rounded-full"></span>
                            LIVE
                        </span>
                    </div>
                    <button
                        onClick={() => navigate('/')}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                    >
                        ← Back to Home
                    </button>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Page Title */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold mb-2">Admin Dashboard</h1>
                    <div className="flex items-center gap-4">
                        <p className="text-gray-400">Manage drivers and users</p>
                        <span className="text-xs text-gray-500">
                            Last updated: {lastUpdate.toLocaleTimeString()}
                        </span>
                    </div>

                    {/* Tab Switcher */}
                    <div className="flex gap-4 mt-6">
                        <button
                            onClick={() => setActiveTab('drivers')}
                            className={`px-6 py-3 rounded-lg font-semibold transition-all ${activeTab === 'drivers'
                                ? 'bg-purple-600 text-white'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                }`}
                        >
                            Drivers
                        </button>
                        <button
                            onClick={() => setActiveTab('users')}
                            className={`px-6 py-3 rounded-lg font-semibold transition-all ${activeTab === 'users'
                                ? 'bg-purple-600 text-white'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                }`}
                        >
                            Users
                        </button>
                    </div>
                </div>

                {/* Statistics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-2xl p-6 shadow-xl">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-blue-200 text-sm font-medium mb-1">Total Drivers</p>
                                <p className="text-4xl font-bold">{stats.total}</p>
                            </div>
                            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                                <span className="text-3xl">🚗</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-cyan-600 to-cyan-800 rounded-2xl p-6 shadow-xl">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-cyan-200 text-sm font-medium mb-1">Online Now</p>
                                <p className="text-4xl font-bold">{stats.online}</p>
                            </div>
                            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                                <span className="text-3xl">🟢</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-green-600 to-green-800 rounded-2xl p-6 shadow-xl">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-green-200 text-sm font-medium mb-1">Verified Safe</p>
                                <p className="text-4xl font-bold">{stats.verified}</p>
                            </div>
                            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                                <span className="text-3xl">✅</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-orange-600 to-orange-800 rounded-2xl p-6 shadow-xl">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-orange-200 text-sm font-medium mb-1">Pending Verification</p>
                                <p className="text-4xl font-bold">{stats.unverified}</p>
                            </div>
                            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                                <span className="text-3xl">⏳</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Conditional Content Based on Active Tab */}
                {activeTab === 'drivers' && (
                    <>
                        {/* Search and Filters */}
                        <div className="bg-gray-800/50 backdrop-blur-md rounded-2xl p-6 mb-6 border border-gray-700">
                            <div className="flex flex-col md:flex-row gap-4">
                                <div className="flex-1">
                                    <input
                                        type="text"
                                        placeholder="Search by Driver ID, Name, Phone, or Vehicle..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    />
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setFilterStatus('all')}
                                        className={`px-6 py-3 rounded-lg font-semibold transition-all ${filterStatus === 'all'
                                            ? 'bg-purple-600 text-white'
                                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                            }`}
                                    >
                                        All
                                    </button>
                                    <button
                                        onClick={() => setFilterStatus('verified')}
                                        className={`px-6 py-3 rounded-lg font-semibold transition-all ${filterStatus === 'verified'
                                            ? 'bg-green-600 text-white'
                                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                            }`}
                                    >
                                        Verified
                                    </button>
                                    <button
                                        onClick={() => setFilterStatus('unverified')}
                                        className={`px-6 py-3 rounded-lg font-semibold transition-all ${filterStatus === 'unverified'
                                            ? 'bg-orange-600 text-white'
                                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                            }`}
                                    >
                                        Unverified
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Drivers Table */}
                        <div className="bg-gray-800/50 backdrop-blur-md rounded-2xl overflow-hidden border border-gray-700">
                            {loading ? (
                                <div className="flex items-center justify-center py-20">
                                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
                                </div>
                            ) : filteredDrivers.length === 0 ? (
                                <div className="text-center py-20">
                                    <p className="text-gray-400 text-lg">No drivers found</p>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead className="bg-gray-900/80">
                                            <tr>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                                    Driver ID
                                                </th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                                    Name
                                                </th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                                    Phone
                                                </th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                                    Vehicle
                                                </th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                                    Rating
                                                </th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                                    Availability
                                                </th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                                    Status
                                                </th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                                    Routes
                                                </th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                                    Actions
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-700">
                                            {filteredDrivers.map((driver) => (
                                                <tr
                                                    key={driver.driver_id}
                                                    className="hover:bg-gray-700/30 transition-colors"
                                                >
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="font-mono font-semibold text-purple-400">
                                                            {driver.driver_id}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="font-medium">{driver.name}</span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="text-gray-300">
                                                            {driver.phone_number || 'N/A'}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className="flex flex-col">
                                                            <span className="text-sm font-medium capitalize">
                                                                {driver.vehicle_type}
                                                            </span>
                                                            <span className="text-xs text-gray-400">
                                                                {driver.vehicle_details || 'No details'}
                                                            </span>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="flex items-center gap-1">
                                                            <span className="text-yellow-400">⭐</span>
                                                            <span className="font-bold text-white">{driver.rating?.toFixed(1) || '5.0'}</span>
                                                            <span className="text-xs text-gray-500">({driver.rating_count || 0})</span>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        {(() => {
                                                            // Handle UTC timestamp from server
                                                            let dateStr = driver.updated_at;
                                                            if (dateStr && !dateStr.endsWith('Z')) {
                                                                dateStr += 'Z';
                                                            }

                                                            const lastHeartbeat = dateStr ? new Date(dateStr) : new Date(0);
                                                            const now = new Date();

                                                            // Debug log (optional, remove in prod)
                                                            // console.log(`Driver ${driver.driver_id}: Last ${lastHeartbeat.toISOString()}, Now ${now.toISOString()}, Diff ${now.getTime() - lastHeartbeat.getTime()}`);

                                                            // Allow 2 minutes timeout for "Online"
                                                            const isOnline = (now.getTime() - lastHeartbeat.getTime()) < 120000;

                                                            if (!isOnline) {
                                                                return (
                                                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gray-600/20 text-gray-400 border border-gray-600/50">
                                                                        ⚫ Offline
                                                                    </span>
                                                                );
                                                            }

                                                            if (driver.available) {
                                                                return (
                                                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-green-600/20 text-green-400 border border-green-600/50">
                                                                        🟢 Online
                                                                    </span>
                                                                );
                                                            } else {
                                                                return (
                                                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-yellow-600/20 text-yellow-400 border border-yellow-600/50">
                                                                        🟡 Busy
                                                                    </span>
                                                                );
                                                            }
                                                        })()}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        {driver.is_verified_safe ? (
                                                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-green-600/20 text-green-400 border border-green-600/50">
                                                                ✓ Verified Safe
                                                            </span>
                                                        ) : (
                                                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-orange-600/20 text-orange-400 border border-orange-600/50">
                                                                ⚠ Not Verified
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-600/20 text-blue-400">
                                                            {driver.assigned_routes} routes
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        {driver.is_verified_safe ? (
                                                            <button
                                                                onClick={() => handleUnverify(driver.driver_id)}
                                                                disabled={processingId === driver.driver_id}
                                                                className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-colors text-sm"
                                                            >
                                                                {processingId === driver.driver_id ? 'Processing...' : 'Unverify'}
                                                            </button>
                                                        ) : (
                                                            <button
                                                                onClick={() => handleVerify(driver.driver_id)}
                                                                disabled={processingId === driver.driver_id}
                                                                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-wait text-white rounded-lg font-semibold transition-colors text-sm"
                                                            >
                                                                {processingId === driver.driver_id ? 'Processing...' : 'Verify'}
                                                            </button>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>

                        {/* Results Count */}
                        <div className="mt-4 text-center text-gray-400 text-sm">
                            Showing {filteredDrivers.length} of {drivers.length} drivers
                        </div>
                    </>
                )}

                {/* Users Tab Content */}
                {activeTab === 'users' && (
                    <>
                        {/* User Search */}
                        <div className="bg-gray-800/50 backdrop-blur-md rounded-2xl p-6 mb-6 border border-gray-700">
                            <input
                                type="text"
                                placeholder="Search by User ID, Name, Email, or Phone..."
                                value={userSearchQuery}
                                onChange={(e) => setUserSearchQuery(e.target.value)}
                                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                        </div>

                        {/* Users Table */}
                        <div className="bg-gray-800/50 backdrop-blur-md rounded-2xl overflow-hidden border border-gray-700">
                            {loading ? (
                                <div className="flex items-center justify-center py-20">
                                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
                                </div>
                            ) : filteredUsers.length === 0 ? (
                                <div className="text-center py-20">
                                    <p className="text-gray-400 text-lg">No users found</p>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead className="bg-gray-900/80">
                                            <tr>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">User ID</th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Name</th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Email</th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Phone</th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Rides</th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Completed</th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Subscriptions</th>
                                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Joined</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-700">
                                            {filteredUsers.map((user) => (
                                                <tr key={user.id} className="hover:bg-gray-700/30 transition-colors">
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="font-mono font-semibold text-purple-400">#{user.id}</span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="font-medium">{user.full_name}</span>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className="text-gray-300 text-sm">{user.email}</span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="text-gray-300">{user.phone_number || 'N/A'}</span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-600/20 text-blue-400 border border-blue-600/50">
                                                            {user.total_rides} rides
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-green-600/20 text-green-400 border border-green-600/50">
                                                            {user.completed_rides} ✓
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-yellow-600/20 text-yellow-400 border border-yellow-600/50">
                                                            {user.active_subscriptions} active
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="text-gray-400 text-sm">
                                                            {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>

                        {/* Results Count */}
                        <div className="mt-4 text-center text-gray-400 text-sm">
                            Showing {filteredUsers.length} of {users.length} users
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
