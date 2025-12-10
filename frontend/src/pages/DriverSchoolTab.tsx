import { useState, useEffect } from 'react';
import { getDriverSchoolRoutes, recordPickupEvent, startSchoolRoute } from '../utils/api';

interface Student {
    id: number;
    name: string;
    stop_id: number;
    stop_name: string;
    otp: string;
    status: 'pending' | 'picked_up' | 'dropped_off' | 'absent';
}

interface Route {
    route_id: number;
    route_name: string;
    type: 'pickup' | 'dropoff';
    start_time: string;
    status: string;
    students: Student[];
    stops: any[];
}

export default function DriverSchoolTab({ driverId }: { driverId: number }) {
    const [routes, setRoutes] = useState<Route[]>([]);
    const [activeRoute, setActiveRoute] = useState<Route | null>(null);
    const [loading, setLoading] = useState(false);
    const [otpInput, setOtpInput] = useState('');
    const [verifying, setVerifying] = useState<number | null>(null);

    useEffect(() => {
        fetchRoutes();
    }, [driverId]);

    const fetchRoutes = async () => {
        setLoading(true);
        try {
            const data = await getDriverSchoolRoutes(driverId);
            setRoutes(data.today_routes);
        } catch (error) {
            console.error('Failed to fetch routes:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStartRoute = async (route: Route) => {
        try {
            await startSchoolRoute(driverId, route.route_id);
            setActiveRoute(route);
            // In a real app, this would start navigation
        } catch (error) {
            console.error('Failed to start route:', error);
            alert('Failed to start route');
        }
    };

    const handleVerifyOtp = async (student: Student) => {
        if (otpInput !== student.otp) {
            alert('Invalid OTP');
            return;
        }

        setVerifying(student.id);
        try {
            await recordPickupEvent(driverId, {
                student_id: student.id,
                route_id: activeRoute!.route_id,
                stop_id: student.stop_id,
                event_type: activeRoute!.type === 'pickup' ? 'picked_up' : 'dropped_off',
                otp: otpInput
            });

            // Update local state
            const updatedRoutes = routes.map(r => {
                if (r.route_id === activeRoute!.route_id) {
                    return {
                        ...r,
                        students: r.students.map(s =>
                            s.id === student.id ? { ...s, status: (activeRoute!.type === 'pickup' ? 'picked_up' : 'dropped_off') as const } : s
                        )
                    };
                }
                return r;
            });
            setRoutes(updatedRoutes);
            setActiveRoute(updatedRoutes.find(r => r.route_id === activeRoute!.route_id) || null);
            setOtpInput('');
            alert('Student verified successfully!');
        } catch (error) {
            console.error('Failed to verify:', error);
            alert('Verification failed');
        } finally {
            setVerifying(null);
        }
    };

    const markAbsent = async (student: Student) => {
        if (!confirm(`Mark ${student.name} as absent?`)) return;

        try {
            await recordPickupEvent(driverId, {
                student_id: student.id,
                route_id: activeRoute!.route_id,
                stop_id: student.stop_id,
                event_type: 'absent'
            });

            // Update local state
            const updatedRoutes = routes.map(r => {
                if (r.route_id === activeRoute!.route_id) {
                    return {
                        ...r,
                        students: r.students.map(s =>
                            s.id === student.id ? { ...s, status: 'absent' } : s
                        )
                    };
                }
                return r;
            });
            setRoutes(updatedRoutes as any);
            setActiveRoute(updatedRoutes.find(r => r.route_id === activeRoute!.route_id) || null);
        } catch (error) {
            console.error('Failed to mark absent:', error);
        }
    };

    if (loading) return <div className="p-8 text-center">Loading routes...</div>;

    if (routes.length === 0) {
        return (
            <div className="p-8 text-center bg-white rounded-xl shadow-sm m-4">
                <div className="text-4xl mb-4">🚌</div>
                <h2 className="text-xl font-bold mb-2">No School Routes Today</h2>
                <p className="text-gray-500">You don't have any assigned school routes for today.</p>
            </div>
        );
    }

    if (activeRoute) {
        return (
            <div className="flex flex-col h-full bg-gray-50">
                <div className="bg-yellow-400 p-4 shadow-md flex justify-between items-center">
                    <button onClick={() => setActiveRoute(null)} className="font-bold">← Back</button>
                    <h2 className="font-bold">{activeRoute.route_name}</h2>
                    <div className="w-8"></div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    <div className="bg-black text-white p-4 rounded-xl mb-4">
                        <div className="flex justify-between items-center">
                            <div>
                                <p className="text-gray-400 text-sm">NEXT STOP</p>
                                <h3 className="text-xl font-bold">Indiranagar Metro</h3>
                            </div>
                            <button className="bg-white text-black px-4 py-2 rounded-lg font-bold">
                                Navigate ↗
                            </button>
                        </div>
                    </div>

                    <h3 className="font-bold text-gray-500 uppercase text-sm">Students</h3>

                    {activeRoute.students.map(student => (
                        <div key={student.id} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h4 className="font-bold text-lg">{student.name}</h4>
                                    <p className="text-gray-500 text-sm">{student.stop_name}</p>
                                </div>
                                <span className={`px-2 py-1 rounded text-xs font-bold ${student.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                    student.status === 'absent' ? 'bg-red-100 text-red-800' :
                                        'bg-green-100 text-green-800'
                                    }`}>
                                    {student.status.toUpperCase()}
                                </span>
                            </div>

                            {student.status === 'pending' && (
                                <div className="space-y-3">
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            placeholder="Enter OTP"
                                            className="flex-1 border rounded-lg px-3 py-2 text-center tracking-widest font-mono text-lg"
                                            maxLength={4}
                                            value={otpInput}
                                            onChange={(e) => setOtpInput(e.target.value)}
                                        />
                                        <button
                                            onClick={() => handleVerifyOtp(student)}
                                            disabled={verifying === student.id}
                                            className="bg-black text-white px-4 py-2 rounded-lg font-bold"
                                        >
                                            Verify
                                        </button>
                                    </div>
                                    <button
                                        onClick={() => markAbsent(student)}
                                        className="w-full text-red-600 text-sm font-bold"
                                    >
                                        Mark Absent
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="p-4 space-y-4">
            <h2 className="text-xl font-bold">Today's Routes</h2>
            {routes.map(route => (
                <div key={route.route_id} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="font-bold text-lg">{route.route_name}</h3>
                            <p className="text-gray-500">{route.start_time} • {route.type.toUpperCase()}</p>
                        </div>
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-bold">
                            {route.students.length} Students
                        </span>
                    </div>

                    <div className="flex gap-2">
                        <button
                            onClick={() => handleStartRoute(route)}
                            className="flex-1 bg-black text-white py-3 rounded-lg font-bold"
                        >
                            Start Route
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
}
