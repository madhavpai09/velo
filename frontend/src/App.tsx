import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
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
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/user" element={<Home />} />
        <Route path="/ride" element={<Ride />} />
        <Route path="/driver" element={<Driver />} />
        <Route path="/safety" element={<Safety />} />
        <Route path="/help" element={<HelpCenter />} />
        <Route path="/school-pool" element={<SchoolPool />} />
        <Route path="/school-pool/student/new" element={<StudentProfile />} />
        <Route path="/school-pool/subscription/new" element={<SubscriptionSetup />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </BrowserRouter>
  );
}