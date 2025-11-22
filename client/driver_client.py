import requests
from fastapi import FastAPI
import uvicorn
from typing import Optional
import json
import asyncio

class VeloDriverClient:
    def __init__(self, dispatch_url: str = "http://localhost:8000", 
                 driver_id: str = None, driver_name: str = None,
                 driver_port: int = 9000):
        self.dispatch_url = dispatch_url
        self.driver_id = driver_id or f"DRIVER-{driver_port}"
        self.driver_name = driver_name or f"Driver {driver_port}"
        self.driver_port = driver_port
        self.current_location = {"lat": 0.0, "lng": 0.0}
        self.is_available = True
        self.current_ride = None
        self.rides_completed = 0
        self.pending_ride = None  # NEW: Store pending ride offer
        
        # Create FastAPI app for this driver
        self.app = FastAPI(title=f"VELO Driver {self.driver_id}")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup routes for receiving ride assignments"""
        
        @self.app.post("/ride/assigned")
        async def receive_ride_assignment(assignment: dict):
            """Receive ride assignment from dispatch server"""
            print(f"\n{'='*60}")
            print(f"🚨 New Ride Offer!")
            print(f"{'='*60}")
            print(f"   Ride ID: {assignment.get('ride_id')}")
            print(f"   User ID: {assignment.get('user_id')}")
            print(f"   Pickup: {assignment.get('pickup_location')}")
            print(f"   Dropoff: {assignment.get('dropoff_location')}")
            print(f"{'='*60}")
            
            # Store pending ride instead of auto-accepting
            self.pending_ride = assignment
            
            print(f"\n⏳ Waiting for driver to accept or decline...")
            print(f"   Use commands: 'accept' or 'decline'")
            print(f"{'='*60}\n")
            
            return {"message": "Ride offer received", "status": "pending_acceptance"}
        
        @self.app.get("/status")
        async def get_status():
            """Health check and status endpoint"""
            return {
                "driver_id": self.driver_id,
                "driver_name": self.driver_name,
                "port": self.driver_port,
                "location": self.current_location,
                "is_available": self.is_available,
                "current_ride": self.current_ride,
                "pending_ride": self.pending_ride,
                "rides_completed": self.rides_completed
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
            
            print(f"\n🚀 Registering driver with VELO dispatch server...")
            print(f"   Driver ID: {self.driver_id}")
            print(f"   Name: {self.driver_name}")
            print(f"   Port: {self.driver_port}")
            print(f"   Location: {self.current_location}")
            
            response = requests.post(
                f"{self.dispatch_url}/driver/register",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Registration successful! Status: {result.get('status')}")
            return result
            
        except requests.RequestException as e:
            error_msg = f"Failed to register driver: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def check_server_status(self) -> dict:
        """Check driver status on server"""
        try:
            numeric_id = int(self.driver_id.replace("DRIVER-", ""))
            
            response = requests.get(
                f"{self.dispatch_url}/api/drivers/{numeric_id}",
                timeout=5
            )
            
            if response.ok:
                return response.json()
            return None
            
        except Exception as e:
            print(f"⚠️ Could not check server status: {e}")
            return None
    
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
            print(f"⚠️ Failed to update location: {e}")
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
            print(f"⚠️ Failed to set availability: {e}")
            return {"error": f"Failed to set availability: {e}"}
    
    def update_ride_status(self, ride_id: int, status: str) -> dict:
        """Update ride status (accepted, in_progress, completed, etc.)"""
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
            print(f"⚠️ Failed to update ride status: {e}")
            return {"error": f"Failed to update ride status: {e}"}
    
    def accept_ride(self) -> dict:
        """Accept the pending ride offer"""
        if not self.pending_ride:
            return {"error": "No pending ride to accept"}
        
        ride_id = self.pending_ride.get('ride_id')
        print(f"\n✅ Accepting ride {ride_id}...")
        
        # Update ride status to accepted
        self.update_ride_status(ride_id, "accepted")
        
        # Move pending ride to current ride
        self.current_ride = self.pending_ride
        self.pending_ride = None
        self.is_available = False
        
        print(f"🚗 Ride accepted! You are now unavailable.")
        print(f"   Pickup: {self.current_ride.get('pickup_location')}")
        print(f"   Dropoff: {self.current_ride.get('dropoff_location')}")
        
        return {"message": "Ride accepted", "ride_id": ride_id}
    
    def decline_ride(self) -> dict:
        """Decline the pending ride offer"""
        if not self.pending_ride:
            return {"error": "No pending ride to decline"}
        
        ride_id = self.pending_ride.get('ride_id')
        print(f"\n❌ Declining ride {ride_id}...")
        
        # Update ride status back to pending so it can be reassigned
        self.update_ride_status(ride_id, "pending")
        
        # Clear pending ride
        self.pending_ride = None
        
        print(f"🔄 Ride declined. Ride will be offered to another driver.")
        print(f"   You remain available for new rides.")
        
        return {"message": "Ride declined", "ride_id": ride_id}
    
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
        self.rides_completed += 1
        self.set_availability(True)
        
        print(f"✅ Ride completed! Total rides: {self.rides_completed}")
        
        return result
    
    def run(self):
        """Start the driver client server"""
        # First register with dispatch server
        self.register()
        
        print(f"\n{'='*60}")
        print(f"🚀 VELO Driver Client Started")
        print(f"{'='*60}")
        print(f"   Driver ID: {self.driver_id}")
        print(f"   Driver Name: {self.driver_name}")
        print(f"   Port: {self.driver_port}")
        print(f"   Connected to: {self.dispatch_url}")
        print(f"   Location: {self.current_location}")
        print(f"   Status: {'✅ Available' if self.is_available else '🔴 Unavailable'}")
        print(f"{'='*60}")
        print(f"\n⏳ Waiting for ride assignments...")
        print(f"   (Use interactive mode to accept/decline rides)\n")
        
        # Start heartbeat task
        @self.app.on_event("startup")
        async def start_heartbeat():
            asyncio.create_task(self.heartbeat_loop())
            
        uvicorn.run(self.app, host="0.0.0.0", port=self.driver_port, log_level="warning")

    async def heartbeat_loop(self):
        """Send heartbeat every 10 seconds"""
        print("💓 Heartbeat loop started")
        while True:
            try:
                await asyncio.sleep(10)
                if self.is_available:
                    try:
                        requests.post(
                            f"{self.dispatch_url}/driver/heartbeat",
                            params={"driver_id": self.driver_id},
                            timeout=5
                        )
                    except Exception as e:
                        print(f"⚠️ Heartbeat failed: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Heartbeat loop error: {e}")
                await asyncio.sleep(10)


def interactive_mode(driver: VeloDriverClient):
    """Interactive mode for testing driver actions"""
    print("\n" + "="*50)
    print("🚗 VELO Driver Client - Interactive Mode")
    print("="*50)
    
    # Register first
    driver.register()
    
    while True:
        print("\nOptions:")
        print("1. Update location")
        print("2. Toggle availability")
        print("3. Accept pending ride")
        print("4. Decline pending ride")
        print("5. Start current ride")
        print("6. Complete current ride")
        print("7. View current status")
        print("8. Check server status")
        print("9. Re-register driver")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-9): ").strip()
        
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
            result = driver.accept_ride()
            print(f"\n{result}")
            
        elif choice == "4":
            result = driver.decline_ride()
            print(f"\n{result}")
            
        elif choice == "5":
            result = driver.start_ride()
            print(f"\n{result}")
            
        elif choice == "6":
            result = driver.complete_ride()
            print(f"\n{result}")
            
        elif choice == "7":
            print(f"\n📊 Driver Status:")
            print(f"   ID: {driver.driver_id}")
            print(f"   Name: {driver.driver_name}")
            print(f"   Location: {driver.current_location}")
            print(f"   Available: {driver.is_available}")
            print(f"   Pending Ride: {driver.pending_ride}")
            print(f"   Current Ride: {driver.current_ride}")
            print(f"   Rides Completed: {driver.rides_completed}")
            
        elif choice == "8":
            status = driver.check_server_status()
            print(f"\n📊 Server Status: {status}")
            
        elif choice == "9":
            result = driver.register()
            print(f"\n{result}")
            
        elif choice == "0":
            print("\n👋 Goodbye!")
            break


def main():
    """Main function to run driver client"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VELO Driver Client')
    parser.add_argument('--port', type=int, default=9000, help='Driver port (default: 9000)')
    parser.add_argument('--driver-id', type=str, help='Driver ID (default: DRIVER-<port>)')
    parser.add_argument('--name', type=str, help='Driver name')
    parser.add_argument('--dispatch', type=str, default='http://localhost:8000', 
                       help='Dispatch server URL')
    parser.add_argument('--lat', type=float, default=12.9716, 
                       help='Initial latitude (default: Bangalore)')
    parser.add_argument('--lng', type=float, default=77.5946, 
                       help='Initial longitude (default: Bangalore)')
    parser.add_argument('--interactive', action='store_true', 
                       help='Run in interactive mode (recommended for manual acceptance)')
    
    args = parser.parse_args()
    
    driver = VeloDriverClient(
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