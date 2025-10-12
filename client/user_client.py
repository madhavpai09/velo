import requests
from fastapi import FastAPI
import uvicorn
import json
import sys
import signal

class MiniUberClient:
    """User client that stays online waiting for ride assignment"""
    
    def __init__(self, base_url: str = "http://localhost:8000", user_id: int = None, client_port: int = 7000):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.user_id = user_id or client_port
        self.client_port = client_port
        self.ride_assigned = False
        self.current_ride = None
        
        # Create FastAPI app for receiving notifications
        self.app = FastAPI(title=f"User Client {self.user_id}")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup routes for receiving ride assignments"""
        
        @self.app.post("/ride/assigned")
        async def receive_ride_assignment(assignment: dict):
            """Receive ride assignment from notifier"""
            print("\n" + "="*60)
            print("🎉 RIDE ASSIGNED!")
            print("="*60)
            print(f"   Ride ID: {assignment.get('ride_id')}")
            print(f"   Driver ID: {assignment.get('driver_id')}")
            print(f"   Driver Name: {assignment.get('driver_name', 'Unknown')}")
            print(f"   Driver Location: {assignment.get('driver_location')}")
            print(f"   Pickup: {assignment.get('pickup_location')}")
            print(f"   Dropoff: {assignment.get('dropoff_location')}")
            print("="*60)
            
            self.current_ride = assignment
            self.ride_assigned = True
            
            # Terminate after receiving assignment
            print("\n✅ Ride assignment received. Client will terminate in 2 seconds...")
            
            # Schedule shutdown
            import asyncio
            asyncio.create_task(self.shutdown_after_delay(2))
            
            return {"message": "Ride assignment received", "status": "accepted"}
        
        @self.app.get("/status")
        async def get_status():
            """Health check endpoint"""
            return {
                "user_id": self.user_id,
                "port": self.client_port,
                "ride_assigned": self.ride_assigned,
                "current_ride": self.current_ride
            }
    
    async def shutdown_after_delay(self, delay: int):
        """Shutdown server after delay"""
        import asyncio
        await asyncio.sleep(delay)
        print("\n👋 Shutting down user client...")
        # Exit the process
        import os
        os._exit(0)
    
    def create_ride_request(self, source_location: str, dest_location: str) -> dict:
        """Create a new ride request"""
        try:
            payload = {
                "source_location": source_location,
                "dest_location": dest_location,
                "user_id": self.user_id
            }
            
            print(f"\n🚗 Creating ride request...")
            print(f"📍 From: {source_location}")
            print(f"📍 To: {dest_location}")
            print(f"👤 User ID: {self.user_id}")
            
            response = requests.post(
                f"{self.api_url}/ride-request",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("message"):
                print(f"\n✅ {result.get('message')}")
                if result.get("data", {}).get("id"):
                    print(f"   Ride Request ID: {result['data']['id']}")
            
            return result
            
        except requests.RequestException as e:
            error_msg = f"Failed to create ride request: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def run(self, source_location: str, dest_location: str):
        """Create ride request and stay online waiting for assignment"""
        
        print("\n" + "="*60)
        print(f"🚕 Mini Uber User Client Started")
        print("="*60)
        print(f"   User ID: {self.user_id}")
        print(f"   Port: {self.client_port}")
        print(f"   Server: {self.base_url}")
        print("="*60)
        
        # Create ride request
        result = self.create_ride_request(source_location, dest_location)
        
        if "error" in result:
            print("\n❌ Failed to create ride request. Exiting...")
            return
        
        # Start server and wait for assignment
        print("\n⏳ Waiting for driver assignment...")
        print("   (Listening on port {})".format(self.client_port))
        print("   (Will auto-terminate once ride is assigned)")
        print("\n" + "="*60 + "\n")
        
        # Run the FastAPI server - blocks here until ride assigned
        uvicorn.run(self.app, host="0.0.0.0", port=self.client_port, log_level="error")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mini Uber User Client')
    parser.add_argument('--port', type=int, default=7000, help='Client port (default: 7000)')
    parser.add_argument('--user-id', type=int, help='User ID (default: port number)')
    parser.add_argument('--server', type=str, default='http://localhost:8000', 
                       help='Server URL')
    parser.add_argument('--from', dest='source', type=str, 
                       default='123 Main St, Chennai',
                       help='Pickup location')
    parser.add_argument('--to', dest='dest', type=str,
                       default='456 Park Ave, Chennai',
                       help='Dropoff location')
    
    args = parser.parse_args()
    
    # Create client
    client = MiniUberClient(
        base_url=args.server,
        user_id=args.user_id,
        client_port=args.port
    )
    
    # Run client (will terminate after ride assignment)
    client.run(args.source, args.dest)


if __name__ == "__main__":
    main()