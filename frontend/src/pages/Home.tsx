import React from 'react'
import MapView from '../shared/MapView'


export default function Home() {
return (
<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
<div className="md:col-span-2">
<MapView />
</div>
<aside className="bg-white p-4 rounded shadow">
<h2 className="text-lg font-semibold">Welcome to Velo</h2>
<p className="mt-2 text-gray-600">Use the Ride page to request a ride.</p>
</aside>
</div>
)
}