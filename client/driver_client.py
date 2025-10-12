import requests
from fastapi import FastAPI
import uvicorn
from typing import Optional
import json

class MiniUberDriverClient:
    def __init__(self, dispatch_url: str = "http://localhost:8000", 
                 driver_id: str = None, driver_name: str = None,
                 driver_port: int = 8001):
        self.dispatch_url = dispatch_url
        self.driver_id = driver_id or f"DRIVER-{driver_port}"
        self.driver_name = driver_name or f"Driver {driver_port}"
        self.driver_port = driver_port
        self.current_location = {"lat": 0.0, "lng": 0.0}
        self.is_available = True
        self.current_ride = None
        
        # Create FastAPI app for this driver
        self.app = FastAPI(title=f"Driver Client {self.driver_id}")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup routes for receiving ride assignments"""
        
        @self.app.post("/ride/assigned")
        async def receive_ride_assignment(assignment: dict):
            """Receive ride assignment from dispatch server"""
            print(f"\n{'='*60}")
            print(f"🚨 New Ride Assigned!")
            print(f"{'='*60}")
            print(f"   Ride ID: {assignment.get('ride_id')}")
            print(f"   User ID: {assignment.get('user_id')}")
            print(f"   Pickup: {assignment.get('pickup_location')}")
            print(f"   Dropoff: {assignment.get('dropoff_location')}")
            print(f"{'='*60}")
            
            self.current_ride = assignment
            self.is_available = False
            
            # Auto-accept the ride
            ride_id = assignment.get('ride_id')
            print(f"\n✅ Auto-accepting ride {ride_id}...")
            self.update_ride_status(ride_id, "accepted")
            
            # Auto-start the ride after 2 seconds
            print(f"🚗 Auto-starting ride in 2 seconds...")
            import asyncio
            await asyncio.sleep(2)
            self.update_ride_status(ride_id, "in_progress")
            
            # Auto-complete the ride after 5 seconds
            print(f"⏳ Ride will complete in 5 seconds...")
            await asyncio.sleep(5)
            print(f"\n🏁 Completing ride {ride_id}...")
            self.update_ride_status(ride_id, "completed")
            
            # Reset state and become available again
            self.current_ride = None
            self.is_available = True
            result = self.set_availability(True)
            print(f"✅ Driver is now available for next ride!")
            print(f"{'='*60}\n")
            
            return {"message": "Ride assignment received", "status": "accepted"}
        
        @self.app.get("/status")
        async def get_status():
            """Health check and status endpoint"""
            return {
                "driver_id": self.driver_id,
                "driver_name": self.driver_name,
                "port": self.driver_port,
                "location": self.current_location,
                "is_available": self.is_available,
                "current_ride": self.current_ride
            }
        
        @self.app.post("/location/update")
        async def update_location_endpoint(location: dict):
            """External endpoint to update driver location"""
            self.current_location = location
            self.update_location(location)
            return {"message": "Location updated", "location": location}
    
    def register(self) -> dict:
        """Register driver with dispatch server"""
        try:
            payload = {
                "driver_id": self.driver_id,
                "name": self.driver_name,
                "port": self.driver_port,
                "location": self.current_location,
                "is_available": self.is_available
            }
            
            print(f"\n🚀 Registering driver with dispatch server...")
            print(f"   Driver ID: {self.driver_id}")
            print(f"   Name: {self.driver_name}")
            print(f"   Port: {self.driver_port}")
            
            response = requests.post(
                f"{self.dispatch_url}/driver/register",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Registration successful!")
            return result
            
        except requests.RequestException as e:
            error_msg = f"Failed to register driver: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def update_location(self, location: dict) -> dict:
        """Update driver location on dispatch server"""
        try:
            self.current_location = location
            
            response = requests.post(
                f"{self.dispatch_url}/driver/update-location",
                params={"driver_id": self.driver_id},
                json=location,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            return {"error": f"Failed to update location: {e}"}
    
    def set_availability(self, is_available: bool) -> dict:
        """Set driver availability"""
        try:
            self.is_available = is_available
            
            response = requests.post(
                f"{self.dispatch_url}/driver/set-availability",
                params={
                    "driver_id": self.driver_id,
                    "is_available": is_available
                },
                timeout=10
            )
            response.raise_for_status()
            
            status = "available" if is_available else "unavailable"
            print(f"📊 Driver status changed to: {status}")
            return response.json()
            
        except requests.RequestException as e:
            return {"error": f"Failed to set availability: {e}"}
    
    def update_ride_status(self, ride_id: str, status: str) -> dict:
        """Update ride status (accepted, started, completed, etc.)"""
        try:
            response = requests.post(
                f"{self.dispatch_url}/ride/{ride_id}/update-status",
                params={"status": status},
                timeout=10
            )
            response.raise_for_status()
            
            print(f"📊 Ride {ride_id} status updated to: {status}")
            
            return response.json()
            
        except requests.RequestException as e:
            print(f"⚠️  Failed to update ride status: {e}")
            return {"error": f"Failed to update ride status: {e}"}
    
    def start_ride(self) -> dict:
        """Start the current ride"""
        if not self.current_ride:
            return {"error": "No active ride"}
        
        ride_id = self.current_ride.get('ride_id')
        print(f"\n🚗 Starting ride {ride_id}...")
        return self.update_ride_status(ride_id, "in_progress")
    
    def complete_ride(self) -> dict:
        """Complete the current ride"""
        if not self.current_ride:
            return {"error": "No active ride"}
        
        ride_id = self.current_ride.get('ride_id')
        print(f"\n🏁 Completing ride {ride_id}...")
        result = self.update_ride_status(ride_id, "completed")
        
        # Reset state
        self.current_ride = None
        self.set_availability(True)
        
        return result
    
    def run(self):
        """Start the driver client server"""
        # First register with dispatch server
        self.register()
        
        print(f"\n{'='*60}")
        print(f"🚀 Driver Client Started")
        print(f"{'='*60}")
        print(f"   Driver ID: {self.driver_id}")
        print(f"   Driver Name: {self.driver_name}")
        print(f"   Port: {self.driver_port}")
        print(f"   Connected to: {self.dispatch_url}")
        print(f"   Location: {self.current_location}")
        print(f"   Status: {'✅ Available' if self.is_available else '🔴 Unavailable'}")
        print(f"{'='*60}")
        print(f"\n⏳ Waiting for ride assignments...")
        print(f"   (Will auto-complete rides after 5 seconds)\n")
        
        uvicorn.run(self.app, host="0.0.0.0", port=self.driver_port)


def interactive_mode(driver: MiniUberDriverClient):
    """Interactive mode for testing driver actions"""
    print("\n" + "="*50)
    print("🚗 Mini Uber Driver Client - Interactive Mode")
    print("="*50)
    
    # Register first
    driver.register()
    
    while True:
        print("\nOptions:")
        print("1. Update location")
        print("2. Toggle availability")
        print("3. Start current ride")
        print("4. Complete current ride")
        print("5. View current status")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            lat = float(input("  Enter latitude: "))
            lng = float(input("  Enter longitude: "))
            result = driver.update_location({"lat": lat, "lng": lng})
            print(f"\n{result}")
            
        elif choice == "2":
            driver.is_available = not driver.is_available
            result = driver.set_availability(driver.is_available)
            print(f"\n{result}")
            
        elif choice == "3":
            result = driver.start_ride()
            print(f"\n{result}")
            
        elif choice == "4":
            result = driver.complete_ride()
            print(f"\n{result}")
            
        elif choice == "5":
            print(f"\n📊 Driver Status:")
            print(f"   ID: {driver.driver_id}")
            print(f"   Name: {driver.driver_name}")
            print(f"   Location: {driver.current_location}")
            print(f"   Available: {driver.is_available}")
            print(f"   Current Ride: {driver.current_ride}")
            
        elif choice == "6":
            print("\n👋 Goodbye!")
            break


def main():
    """Main function to run driver client"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mini Uber Driver Client')
    parser.add_argument('--port', type=int, default=8001, help='Driver port (default: 8001)')
    parser.add_argument('--driver-id', type=str, help='Driver ID (default: DRIVER-<port>)')
    parser.add_argument('--name', type=str, help='Driver name')
    parser.add_argument('--dispatch', type=str, default='http://localhost:8000', 
                       help='Dispatch server URL')
    parser.add_argument('--lat', type=float, default=13.0827, 
                       help='Initial latitude (default: Chennai)')
    parser.add_argument('--lng', type=float, default=80.2707, 
                       help='Initial longitude (default: Chennai)')
    parser.add_argument('--interactive', action='store_true', 
                       help='Run in interactive mode (no server)')
    
    args = parser.parse_args()
    
    driver = MiniUberDriverClient(
        dispatch_url=args.dispatch,
        driver_id=args.driver_id,
        driver_name=args.name,
        driver_port=args.port
    )
    
    # Set initial location
    driver.current_location = {"lat": args.lat, "lng": args.lng}
    
    if args.interactive:
        interactive_mode(driver)
    else:
        # Run as server
        driver.run()


if __name__ == "__main__":
    main()