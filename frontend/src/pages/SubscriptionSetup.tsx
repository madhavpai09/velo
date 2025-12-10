import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SubscriptionSetup() {
    const navigate = useNavigate();
    const [students, setStudents] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [assignedDriver, setAssignedDriver] = useState<any>(null);
    const [formData, setFormData] = useState({
        student_id: '',
        start_date: '',
        end_date: '',
        pickup_time: '07:30',
        drop_time: '15:30',
        days: [] as string[]
    });

    const userId = 7000;

    useEffect(() => {
        fetchStudents();
    }, []);

    const fetchStudents = async () => {
        try {
            const response = await fetch(`http://localhost:8000/api/user/${userId}/students`);
            if (response.ok) {
                const data = await response.json();
                setStudents(data.students);
                if (data.students.length > 0) {
                    setFormData(prev => ({ ...prev, student_id: data.students[0].id }));
                }
            }
        } catch (error) {
            console.error('Failed to fetch students:', error);
        }
    };

    const handleDayToggle = (day: string) => {
        setFormData(prev => {
            const days = prev.days.includes(day)
                ? prev.days.filter(d => d !== day)
                : [...prev.days, day];
            return { ...prev, days };
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/subscription/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    student_id: parseInt(formData.student_id),
                    start_date: new Date(formData.start_date).toISOString(),
                    end_date: new Date(formData.end_date).toISOString(),
                    days: formData.days,
                    pickup_time: formData.pickup_time,
                    drop_time: formData.drop_time
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.driver_id) {
                    setAssignedDriver({
                        id: data.driver_id,
                        name: data.driver_name
                    });
                } else {
                    alert('Subscription created! Driver will be assigned shortly.');
                    navigate('/school-pool');
                }
            } else {
                alert('Failed to create subscription');
            }
        } catch (error) {
            console.error(error);
            alert('Error creating subscription');
        } finally {
            setLoading(false);
        }
    };

    if (assignedDriver) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
                <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full text-center">
                    <div className="text-6xl mb-4">🎉</div>
                    <h2 className="text-2xl font-bold mb-2">Subscription Active!</h2>
                    <p className="text-gray-600 mb-6">Your child's rides are scheduled.</p>

                    <div className="bg-green-50 p-4 rounded-lg border border-green-200 mb-6">
                        <div className="text-sm text-green-800 font-bold uppercase mb-1">Assigned Driver</div>
                        <div className="text-xl font-bold">{assignedDriver.name}</div>
                        <div className="text-sm text-gray-600">ID: {assignedDriver.id}</div>
                    </div>

                    <button
                        onClick={() => navigate('/school-pool')}
                        className="w-full bg-black text-white py-3 rounded-lg font-bold"
                    >
                        Done
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <div className="bg-white p-6 shadow-sm flex items-center gap-4">
                <button onClick={() => navigate('/school-pool')} className="text-2xl">←</button>
                <h1 className="text-xl font-bold">New Monthly Pass</h1>
            </div>

            <div className="p-6">
                <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm space-y-6">

                    {/* Student Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Select Student</label>
                        <select
                            value={formData.student_id}
                            onChange={e => setFormData({ ...formData, student_id: e.target.value })}
                            className="w-full p-3 border rounded-lg bg-white"
                        >
                            {students.map(s => (
                                <option key={s.id} value={s.id}>{s.name} ({s.school_name})</option>
                            ))}
                        </select>
                    </div>

                    {/* Date Range */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                            <input
                                type="date"
                                required
                                value={formData.start_date}
                                onChange={e => setFormData({ ...formData, start_date: e.target.value })}
                                className="w-full p-3 border rounded-lg"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                            <input
                                type="date"
                                required
                                value={formData.end_date}
                                onChange={e => setFormData({ ...formData, end_date: e.target.value })}
                                className="w-full p-3 border rounded-lg"
                            />
                        </div>
                    </div>

                    {/* Days Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Select Days</label>
                        <div className="flex flex-wrap gap-2">
                            {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map(day => (
                                <button
                                    key={day}
                                    type="button"
                                    onClick={() => handleDayToggle(day)}
                                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${formData.days.includes(day)
                                        ? 'bg-black text-white'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                >
                                    {day}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Time Selection */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Pickup Time (Home)</label>
                            <input
                                type="time"
                                required
                                value={formData.pickup_time}
                                onChange={e => setFormData({ ...formData, pickup_time: e.target.value })}
                                className="w-full p-3 border rounded-lg"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Drop Time (School)</label>
                            <input
                                type="time"
                                required
                                value={formData.drop_time}
                                onChange={e => setFormData({ ...formData, drop_time: e.target.value })}
                                className="w-full p-3 border rounded-lg"
                            />
                        </div>
                    </div>

                    {/* Summary & Price */}
                    <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-yellow-800 font-medium">Monthly Estimate</span>
                            <span className="text-2xl font-bold">₹3,500</span>
                        </div>
                        <p className="text-xs text-yellow-700">Includes safe driver verification and real-time tracking.</p>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || formData.days.length === 0}
                        className="w-full bg-black text-white py-4 rounded-xl font-bold text-lg disabled:bg-gray-300"
                    >
                        {loading ? 'Processing...' : 'Subscribe & Pay'}
                    </button>
                </form>
            </div>
        </div>
    );
}
