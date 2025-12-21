import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './shared/ProtectedRoute';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Home from './pages/Home';
import Ride from './pages/Ride';
import Driver from './pages/Driver';
import AboutUs from './pages/AboutUs';
import HelpCenter from './pages/HelpCenter';
import SchoolPool from './pages/SchoolPool';
import StudentProfile from './pages/StudentProfile';
import SubscriptionSetup from './pages/SubscriptionSetup';
import Safety from './pages/Safety';
import Admin from './pages/Admin';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Public Pages */}
          <Route path="/driver" element={<Driver />} />
          <Route path="/safety" element={<Safety />} />
          <Route path="/help" element={<HelpCenter />} />
          <Route path="/about" element={<AboutUs />} />
          <Route path="/admin" element={<Admin />} />

          {/* Protected Routes */}
          <Route path="/home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
          <Route path="/ride" element={<ProtectedRoute><Ride /></ProtectedRoute>} />
          <Route path="/school-pool" element={<ProtectedRoute><SchoolPool /></ProtectedRoute>} />
          <Route path="/school-pool/student/new" element={<ProtectedRoute><StudentProfile /></ProtectedRoute>} />
          <Route path="/school-pool/subscription/new" element={<ProtectedRoute><SubscriptionSetup /></ProtectedRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}