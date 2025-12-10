import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function StudentProfile() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    // Get userId from URL params if available
    const urlParams = new URLSearchParams(window.location.search);
    const userIdFromUrl = urlParams.get('userId');

    const [formData, setFormData] = useState({
        userId: userIdFromUrl || '',
        name: '',
        school_name: '',
        school_address: '',
        home_address: '',
        grade: ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/student/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: parseInt(formData.userId),
                    name: formData.name,
                    school_name: formData.school_name,
                    school_address: formData.school_address,
                    home_address: formData.home_address,
                    grade: formData.grade
                })
            });

            if (response.ok) {
                alert('Student profile created!');
                navigate('/school-pool');
            } else {
                alert('Failed to create profile');
            }
        } catch (error) {
            console.error(error);
            alert('Error creating profile');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <div className="bg-white p-6 shadow-sm flex items-center gap-4">
                <button onClick={() => navigate('/school-pool')} className="text-2xl">←</button>
                <h1 className="text-xl font-bold">Add Student Profile</h1>
            </div>

            <div className="p-6">
                <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Parent/User ID</label>
                        <input
                            required
                            type="number"
                            value={formData.userId}
                            onChange={e => setFormData({ ...formData, userId: e.target.value })}
                            className="w-full p-3 border rounded-lg"
                            placeholder="e.g. 7000, 7001, 7002"
                        />
                        <p className="text-xs text-gray-500 mt-1">Enter the parent's user ID to link this student</p>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Student Name</label>
                        <input
                            required
                            type="text"
                            value={formData.name}
                            onChange={e => setFormData({ ...formData, name: e.target.value })}
                            className="w-full p-3 border rounded-lg"
                            placeholder="e.g. Rahul"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Grade/Class</label>
                        <input
                            type="text"
                            value={formData.grade}
                            onChange={e => setFormData({ ...formData, grade: e.target.value })}
                            className="w-full p-3 border rounded-lg"
                            placeholder="e.g. 5th Standard"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">School Name</label>
                        <input
                            required
                            type="text"
                            value={formData.school_name}
                            onChange={e => setFormData({ ...formData, school_name: e.target.value })}
                            className="w-full p-3 border rounded-lg"
                            placeholder="e.g. National Public School"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">School Address</label>
                        <input
                            required
                            type="text"
                            value={formData.school_address}
                            onChange={e => setFormData({ ...formData, school_address: e.target.value })}
                            className="w-full p-3 border rounded-lg"
                            placeholder="Full address"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Home Address</label>
                        <input
                            required
                            type="text"
                            value={formData.home_address}
                            onChange={e => setFormData({ ...formData, home_address: e.target.value })}
                            className="w-full p-3 border rounded-lg"
                            placeholder="Full address"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-black text-white py-4 rounded-xl font-bold text-lg mt-6"
                    >
                        {loading ? 'Saving...' : 'Save Profile'}
                    </button>
                </form>
            </div>
        </div>
    );
}
