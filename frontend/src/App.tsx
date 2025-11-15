import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import Ride from './pages/Ride'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow p-4">
        <div className="container mx-auto flex justify-between">
          <Link to="/" className="text-xl font-bold">
            Velo
          </Link>

          <nav className="space-x-4">
            <Link to="/" className="hover:underline">Home</Link>
            <Link to="/ride" className="hover:underline">Ride</Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto p-4">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/ride" element={<Ride />} />
        </Routes>
      </main>
    </div>
  )
}
