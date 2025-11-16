# 🎨 Frontend Guide - Mini Uber

## Overview

The frontend now has **3 main pages**:

1. **Home Page** (`/`) - For users to request rides
2. **Driver Page** (`/driver`) - For drivers to register and go online
3. **Rides Page** (`/ride`) - To view all ride requests

## Features

### ✅ User Features (Home Page)
- **Online Status Indicator** - Shows "🟢 User Online" in the header
- **Map Interface** - Click to select pickup and dropoff locations
- **Ride Request** - Create ride requests with visual feedback
- **Driver Assignment** - See when a driver is assigned to your ride
- **Real-time Driver Map** - See available drivers on the map

### ✅ Driver Features (Driver Page)
- **Driver Registration** - Register with Driver ID and Name
- **Online/Offline Toggle** - Mark yourself as available or unavailable
- **Location Update** - Click on map to update your location
- **Online Status Indicator** - Shows "🟢 Online" or "🔴 Offline" in header
- **Status Dashboard** - View your current status and location
- **Real-time Status Updates** - Automatically polls for status changes

## How to Use

### For Users:
1. Open the app (usually `http://localhost:5173`)
2. You'll see "🟢 User Online" in the header
3. Click on the map to select pickup location (green marker)
4. Click again to select dropoff location (red marker)
5. Click "Request Ride" button
6. Wait for driver assignment
7. You'll see a notification when a driver is assigned

### For Drivers:
1. Click "🚗 Driver Login" button from the home page
2. Enter your Driver ID (e.g., `9000` or `DRIVER-9000`)
3. Enter your Name (e.g., `John Doe`)
4. Click "🚀 Register as Driver"
5. Once registered, click "🟢 Go Online" to mark yourself as available
6. Click on the map to update your location
7. You'll see "🟢 Online" status in the header when available
8. When a ride is assigned, you'll see it in the dashboard (coming soon)

## Technical Details

### API Endpoints Used:
- `POST /driver/register` - Register a driver
- `POST /driver/set-availability` - Set driver availability
- `POST /driver/update-location` - Update driver location
- `GET /api/drivers/{driver_id}` - Get driver status
- `GET /api/drivers/available` - Get all available drivers
- `POST /api/ride-request` - Create a ride request

### Status Indicators:
- **🟢 Green** - Online/Available
- **🔴 Red** - Offline/Unavailable
- **Pulsing animation** - Active/Real-time status

## Notes

- The frontend communicates directly with the backend API
- No need to run `driver_client.py` or `user_client.py` in terminal anymore
- All functionality is available through the web interface
- Status updates happen automatically via polling (every 2 seconds)

