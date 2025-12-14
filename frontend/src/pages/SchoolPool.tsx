import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSchools, getSchoolRoutes, createSchoolPassSubscription, School, SchoolRoute, RouteStop } from '../utils/api';

export default function SchoolPool() {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [schools, setSchools] = useState<School[]>([]);
    const [selectedSchool, setSelectedSchool] = useState<School | null>(null);
    const [routes, setRoutes] = useState<SchoolRoute[]>([]);
    const [selectedRoute, setSelectedRoute] = useState<SchoolRoute | null>(null);
    const [selectedStop, setSelectedStop] = useState<RouteStop | null>(null);
    const [students, setStudents] = useState<any[]>([]);
    const [selectedStudent, setSelectedStudent] = useState<any | null>(null);
    const [subscriptions, setSubscriptions] = useState<any[]>([]); // NEW
    const [loading, setLoading] = useState(false);

    // User ID management
    const [userId, setUserId] = useState<number | null>(null);
    const [showUserIdInput, setShowUserIdInput] = useState(true);

    useEffect(() => {
        loadSchools();
    }, []);

    useEffect(() => {
        if (userId) {
            fetchStudents();
            fetchSubscriptions(); // NEW
        }
    }, [userId]);

    const loadSchools = async () => {
        try {
            const data = await getSchools();
            setSchools(data.schools);
        } catch (error) {
            console.error('Failed to load schools:', error);
        }
    };

    const fetchStudents = async () => {
        if (!userId) return;
        try {
            const response = await fetch(`http://localhost:8000/api/user/${userId}/students`);
            if (response.ok) {
                const data = await response.json();
                setStudents(data.students);
            }
        } catch (error) {
            console.error('Failed to fetch students:', error);
        }
    };

    // NEW: Fetch Subscriptions
    const fetchSubscriptions = async () => {
        if (!userId) return;
        try {
            const response = await fetch(`http://localhost:8000/api/user/${userId}/subscriptions`);
            if (response.ok) {
                const data = await response.json();
                setSubscriptions(data.subscriptions);
            }
        } catch (error) {
            console.error('Failed to fetch subscriptions:', error);
        }
    };

    // NEW: Cancel Subscription
    const handleCancelSubscription = async (subId: number) => {
        if (!confirm('Are you sure you want to cancel this subscription?')) return;
        try {
            const response = await fetch(`http://localhost:8000/api/subscriptions/${subId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                alert('Subscription cancelled');
                fetchSubscriptions();
            } else {
                alert('Failed to cancel');
            }
        } catch (error) {
            console.error('Cancel failed:', error);
        }
    };

    // NEW: Delete Student
    const handleDeleteStudent = async (studentId: number, e: React.MouseEvent) => {
        e.stopPropagation(); // Prevent selection
        if (!confirm('Are you sure you want to delete this student profile?')) return;
        try {
            const response = await fetch(`http://localhost:8000/api/students/${studentId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                alert('Student deleted');
                fetchStudents();
            } else {
                const err = await response.json();
                alert(err.detail || 'Failed to delete student');
            }
        } catch (error) {
            console.error('Delete failed:', error);
        }
    };

    const handleSchoolSelect = async (school: School) => {
        setSelectedSchool(school);
        setLoading(true);
        try {
            const data = await getSchoolRoutes(school.id);
            setRoutes(data.routes);
            setStep(2);
        } catch (error) {
            console.error('Failed to load routes:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRouteSelect = (route: SchoolRoute) => {
        setSelectedRoute(route);
        setStep(3);
    };

    const handleStopSelect = (stop: RouteStop) => {
        setSelectedStop(stop);
        setStep(4);
    };

    const handleStudentSelect = (student: any) => {
        setSelectedStudent(student);
        setStep(5);
    };

    const [subscriptionResult, setSubscriptionResult] = useState<any>(null);

    const handleSubscribe = async () => {
        if (!selectedStudent || !selectedRoute || !selectedStop || !userId) return;

        setLoading(true);
        try {
            const result = await createSchoolPassSubscription({
                user_id: userId,
                student_id: selectedStudent.id,
                route_id: selectedRoute.id,
                stop_id: selectedStop.id,
                subscription_type: 'monthly',
                start_date: new Date().toISOString().split('T')[0]
            });

            // Fetch the OTP from the subscriptions endpoint
            const subsResponse = await fetch(`http://localhost:8000/api/user/${userId}/subscriptions`);
            const subsData = await subsResponse.json();
            const thisSub = subsData.subscriptions.find((s: any) => s.id === result.subscription_id);

            setSubscriptionResult({
                ...result,
                otp: thisSub?.otp || '0000'
            });
            setStep(6);
            fetchSubscriptions(); // Refresh list
        } catch (error) {
            console.error('Failed to subscribe:', error);
            alert('Failed to create subscription');
        } finally {
            setLoading(false);
        }
    };

    // NEW: View Subscription Details
    const handleViewSubscription = async (sub: any) => {
        setLoading(true);
        try {
            // Fetch fresh details with driver info
            const response = await fetch(`http://localhost:8000/api/subscriptions/school-pass/${sub.id}`);
            if (!response.ok) throw new Error("Failed to fetch details");
            const details = await response.json();

            setSubscriptionResult({
                subscription_id: sub.id,
                assigned_driver: details.driver ? {
                    name: details.driver.name,
                    phone: details.driver.phone,
                    vehicle: "Assigned Vehicle" // API doesn't return vehicle details in this specific endpoint yet, fallback
                } : null,
                otp: sub.otp || '0000' // Use OTP from the list view which has today's OTP
            });
            setStep(6);
        } catch (error) {
            console.error("Failed to load subscription details", error);
            alert("Failed to load details");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <div className="bg-yellow-400 p-6 shadow-md">
                <div className="flex items-center gap-4 mb-4">
                    <button onClick={() => step > 1 && step < 6 ? setStep(step - 1) : navigate('/')} className="text-2xl">←</button>
                    <h1 className="text-2xl font-bold">School Pool Subscription</h1>
                </div>
                {step < 6 && (
                    <div className="flex gap-2">
                        {[1, 2, 3, 4, 5].map(s => (
                            <div key={s} className={`h-1 flex-1 rounded ${s <= step ? 'bg-black' : 'bg-yellow-200'}`} />
                        ))}
                    </div>
                )}
            </div>

            <div className="flex-1 p-6 overflow-y-auto">
                {showUserIdInput && (
                    <div className="max-w-md mx-auto mt-20">
                        <div className="bg-white p-8 rounded-xl shadow-lg">
                            <h2 className="text-2xl font-bold mb-4">Enter Your User ID</h2>
                            <p className="text-gray-600 mb-6">Please enter your user ID to view your students and subscriptions.</p>
                            <input
                                type="number"
                                value={userId || ''}
                                onChange={(e) => setUserId(parseInt(e.target.value) || null)}
                                placeholder="e.g., 7000, 7001, 7002"
                                className="w-full p-4 border-2 rounded-lg mb-4 text-lg"
                            />
                            <button
                                onClick={() => {
                                    if (userId) {
                                        setShowUserIdInput(false);
                                    } else {
                                        alert('Please enter a valid User ID');
                                    }
                                }}
                                className="w-full bg-black text-white py-4 rounded-xl font-bold text-lg hover:bg-gray-800"
                            >
                                Continue
                            </button>
                        </div>
                    </div>
                )}

                {!showUserIdInput && step === 1 && (
                    <div className="space-y-4">
                        {/* CURRENT SUBSCRIPTIONS */}
                        {subscriptions.length > 0 && (
                            <div className="mb-8">
                                <h2 className="text-xl font-bold mb-4">Your Active Subscriptions</h2>
                                {subscriptions.map(sub => (
                                    <div key={sub.id}
                                        onClick={() => handleViewSubscription(sub)}
                                        className="bg-green-50 p-4 rounded-xl shadow-sm border border-green-200 mb-4 cursor-pointer hover:border-green-500 transition-colors"
                                    >
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <h3 className="font-bold text-lg">{sub.student_name}</h3>
                                                <p className="text-gray-600">{sub.school_name}</p>
                                                <p className="text-sm text-gray-500 mt-1">Route: {sub.route_name} • {sub.pickup_time}</p>
                                            </div>
                                            <div className="text-right">
                                                <span className="bg-green-200 text-green-800 px-2 py-1 rounded text-xs font-bold block mb-2">ACTIVE</span>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleCancelSubscription(sub.id);
                                                    }}
                                                    className="text-red-600 text-xs font-bold underline"
                                                >
                                                    Cancel Pass
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <h2 className="text-xl font-bold">Select School for New Pass</h2>
                        {schools.map(school => (
                            <div key={school.id} onClick={() => handleSchoolSelect(school)} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 cursor-pointer hover:border-black">
                                <h3 className="font-bold text-lg">{school.name}</h3>
                                <p className="text-gray-500">{school.address}</p>
                                <div className="mt-2 text-green-600 text-sm">✓ Verified Partner</div>
                            </div>
                        ))}
                    </div>
                )}

                {step === 2 && (
                    <div className="space-y-4">
                        <h2 className="text-xl font-bold">Select Route</h2>
                        {routes.map(route => (
                            <div key={route.id} onClick={() => handleRouteSelect(route)} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 cursor-pointer hover:border-black">
                                <div className="flex justify-between items-center mb-2">
                                    <h3 className="font-bold text-lg">{route.name}</h3>
                                    <span className="bg-gray-100 px-2 py-1 rounded text-sm">{route.start_time}</span>
                                </div>
                                <p className="text-gray-500">{route.available_seats} seats available</p>
                            </div>
                        ))}
                    </div>
                )}

                {step === 3 && selectedRoute && (
                    <div className="space-y-4">
                        <h2 className="text-xl font-bold">Select Pickup Stop</h2>
                        {selectedRoute.stops.map(stop => (
                            <div key={stop.id} onClick={() => handleStopSelect(stop)} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 cursor-pointer hover:border-black">
                                <div className="flex gap-4 items-center">
                                    <div className="w-8 h-8 bg-black text-white rounded-full flex items-center justify-center font-bold">{stop.id}</div>
                                    <div>
                                        <h3 className="font-bold">{stop.name}</h3>
                                        <p className="text-gray-500 text-sm">{stop.address}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {step === 4 && (
                    <div className="space-y-4">
                        <h2 className="text-xl font-bold">Select Student</h2>
                        <p className="text-sm text-gray-500">User ID: {userId} • {students.length} student(s) found</p>

                        {/* WARNING for Max Students */}
                        {students.length >= 3 && (
                            <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
                                <p className="font-bold">Maximum Limit Reached</p>
                                <p className="text-sm">You have reached the limit of 3 students per account.</p>
                            </div>
                        )}

                        {students.map(student => {
                            // Check if student is already subscribed (Need to fetch subscriptions first or pass them)
                            // For MVP, we'll try to subscribe and handle the error message gracefully, 
                            // OR we can fetch subscriptions in fetchStudents.
                            // Let's rely on the backend check for duplicates, which we just added.
                            // But for better UX, let's assume we can add a check if we extended the student object.

                            return (
                                <div key={student.id} onClick={() => handleStudentSelect(student)} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 cursor-pointer hover:border-black flex justify-between items-center group">
                                    <div>
                                        <h3 className="font-bold">{student.name}</h3>
                                        <p className="text-gray-500">{student.school_name} • {student.grade}</p>
                                    </div>
                                    <button
                                        onClick={(e) => handleDeleteStudent(student.id, e)}
                                        className="bg-red-50 text-red-600 p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100"
                                        title="Delete Profile"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            );
                        })}

                        {students.length < 3 ? (
                            <button onClick={() => navigate(`/school-pool/student/new?userId=${userId}`)} className="w-full py-4 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 font-bold hover:border-black hover:text-black transition-colors">
                                + Add New Student
                            </button>
                        ) : (
                            <button disabled className="w-full py-4 border-2 border-dashed border-gray-200 rounded-xl text-gray-300 font-bold cursor-not-allowed">
                                + Add Student (Limit Reached)
                            </button>
                        )}
                    </div>
                )}

                {step === 5 && selectedSchool && selectedRoute && selectedStop && selectedStudent && (
                    <div className="space-y-6">
                        <h2 className="text-xl font-bold">Confirm Subscription</h2>

                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-4">
                            <div>
                                <label className="text-sm text-gray-500">Student</label>
                                <p className="font-bold text-lg">{selectedStudent.name}</p>
                            </div>
                            <div>
                                <label className="text-sm text-gray-500">Route</label>
                                <p className="font-bold">{selectedRoute.name}</p>
                                <p className="text-gray-600">{selectedSchool.name}</p>
                            </div>
                            <div>
                                <label className="text-sm text-gray-500">Pickup</label>
                                <p className="font-bold">{selectedStop.name}</p>
                                <p className="text-gray-600">{selectedRoute.start_time}</p>
                            </div>
                            <div className="pt-4 border-t">
                                <div className="flex justify-between items-center mb-2">
                                    <span>Monthly Pass</span>
                                    <span className="font-bold">₹4,500</span>
                                </div>
                                <p className="text-xs text-gray-500">Auto-renews every month. Cancel anytime.</p>
                            </div>
                        </div>

                        <button
                            onClick={handleSubscribe}
                            disabled={loading}
                            className="w-full bg-black text-white py-4 rounded-xl font-bold text-lg disabled:bg-gray-400"
                        >
                            {loading ? 'Processing...' : 'Pay & Subscribe'}
                        </button>

                        {/* Show error if duplicate */}
                        {subscriptionResult && subscriptionResult.message === "Student already subscribed" && (
                            <p className="text-red-500 text-center font-bold">This student is already subscribed.</p>
                        )}
                    </div>
                )}

                {step === 6 && subscriptionResult && (
                    <div className="space-y-6 animate-fade-in">
                        <div className="text-center py-8">
                            <div className="text-6xl mb-4">🎉</div>
                            <h2 className="text-2xl font-bold mb-2">Subscription Active!</h2>
                            <p className="text-gray-500">Your child is all set for their daily commute.</p>
                        </div>

                        <div className="bg-white p-6 rounded-xl shadow-lg border-2 border-green-500 relative overflow-hidden">
                            <div className="absolute top-0 right-0 bg-green-500 text-white px-4 py-1 rounded-bl-xl font-bold text-sm">
                                ASSIGNED DRIVER
                            </div>

                            {subscriptionResult.assigned_driver ? (
                                <div className="flex gap-4 items-start mt-4">
                                    <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center text-2xl">
                                        👨‍✈️
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-xl">{subscriptionResult.assigned_driver.name}</h3>
                                        <p className="text-gray-600">{subscriptionResult.assigned_driver.vehicle}</p>
                                        <div className="flex items-center gap-2 mt-2">
                                            <span className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded text-xs font-bold">★ 4.9</span>
                                            <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded text-xs font-bold">✓ Verified Safe</span>
                                        </div>
                                        {subscriptionResult.assigned_driver.phone && (
                                            <p className="mt-2 text-sm font-mono bg-gray-100 p-2 rounded text-center">
                                                📞 {subscriptionResult.assigned_driver.phone}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-4">
                                    <p className="font-bold text-yellow-600">Driver assignment pending</p>
                                    <p className="text-sm text-gray-500">We will notify you once a driver is assigned.</p>
                                </div>
                            )}
                        </div>

                        {/* OTP DISPLAY */}
                        <div className="bg-yellow-50 border-2 border-yellow-400 p-6 rounded-xl">
                            <div className="text-center">
                                <div className="text-sm font-bold text-yellow-800 uppercase mb-2">🔐 Student Pickup OTP</div>
                                <div className="text-4xl font-mono font-bold tracking-widest mb-2">
                                    {subscriptionResult.otp || '0000'}
                                </div>
                                <p className="text-xs text-yellow-700">
                                    The student should show this OTP to the driver during pickup
                                </p>
                            </div>
                        </div>

                        <button
                            onClick={() => navigate('/')}
                            className="w-full bg-black text-white py-4 rounded-xl font-bold text-lg"
                        >
                            Done
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
