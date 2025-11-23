import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Home from './pages/Home';
import Ride from './pages/Ride';
import Driver from './pages/Driver';
import AboutUs from './pages/AboutUs';
import HelpCenter from './pages/HelpCenter';
import Safety from './pages/Safety';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/user" element={<Home />} />
        <Route path="/ride" element={<Ride />} />
        <Route path="/driver" element={<Driver />} />
        <Route path="/about" element={<AboutUs />} />
        <Route path="/help" element={<HelpCenter />} />
        <Route path="/safety" element={<Safety />} />
      </Routes>
    </BrowserRouter>
  );
}