import React, { useState } from 'react'
import api from '../utils/api'


export default function RideForm() {
const [pickup, setPickup] = useState('')
const [drop, setDrop] = useState('')
const [loading, setLoading] = useState(false)
const [result, setResult] = useState<any>(null)


async function submit(e: React.FormEvent) {
e.preventDefault()
setLoading(true)
try {
const res = await api.post('/rides', { pickup, drop })
setResult(res.data)
} catch (err) {
setResult({ error: 'Failed to request ride' })
} finally {
setLoading(false)
}
}


return (
<form onSubmit={submit} className="space-y-3">
<div>
<label className="block">Pickup</label>
<input
className="border rounded p-2 w-full"
value={pickup}
onChange={(e) => setPickup(e.target.value)}
/>
</div>


<div>
<label className="block">Drop</label>
<input
className="border rounded p-2 w-full"
value={drop}
onChange={(e) => setDrop(e.target.value)}
/>
</div>


<button className="bg-blue-600 text-white px-4 py-2 rounded">
{loading ? 'Requesting...' : 'Request Ride'}
</button>


{result && (
<pre className="bg-gray-100 mt-3 p-2 rounded text-sm">
{JSON.stringify(result, null, 2)}
</pre>
)}
</form>
)}