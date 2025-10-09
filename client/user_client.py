import requests
import json
from typing import Optional

class MiniUberClient:
    """
    Updated client that works with YOUR existing server
    Can run on different ports: 7000, 7001, 7002, etc.
    """
    def __init__(self, base_url: str = "http://localhost:8000", user_id: int = None, client_port: int = 7000):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.user_id = user_id or client_port  # Use port as user_id if not provided
        self.client_port = client_port
        
    def ping(self) -> dict:
        """Test ping endpoint - YOUR EXISTING ENDPOINT"""
        try:
            response = requests.post(
                f"{self.api_url}/ping",
                json={"data": "ping"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Ping failed: {e}"}
    
    def create_ride_request(self, source_location: str, dest_location: str, user_id: int = None) -> dict:
        """
        Create a new ride request - YOUR EXISTING ENDPOINT
        Now enhanced to automatically assign drivers!
        """
        try:
            # Use instance user_id if not provided
            uid = user_id or self.user_id
            
            payload = {
                "source_location": source_location,
                "dest_location": dest_location,
                "user_id": uid
            }
            
            print(f"\n🚗 Creating ride request...")
            print(f"📍 From: {source_location}")
            print(f"📍 To: {dest_location}")
            print(f"👤 User ID: {uid}")
            print(f"🔌 Client Port: {self.client_port}")
            
            response = requests.post(
                f"{self.api_url}/ride-request",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Check if driver was assigned
            if result.get("status") == "success":
                if "driver" in result:
                    print(f"\n✅ Ride created and driver assigned!")
                    print(f"   Ride ID: {result.get('ride_id')}")
                    print(f"   Driver: {result['driver'].get('name')} (ID: {result['driver'].get('id')})")
                    print(f"   Driver Location: {result['driver'].get('location')}")
                else:
                    print(f"\n✅ Ride created but no drivers available yet")
                    print(f"   Ride ID: {result.get('ride_id')}")
                    print(f"   Status: Waiting for driver...")
            
            return result
            
        except requests.RequestException as e:
            error_msg = f"Failed to create ride request: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def get_ride_requests(self) -> dict:
        """Get all ride requests - YOUR EXISTING ENDPOINT"""
        try:
            response = requests.get(
                f"{self.api_url}/ride-requests",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Failed to fetch ride requests: {e}"}
    
    def get_ride_request(self, ride_id: int) -> dict:
        """Get a specific ride request - YOUR EXISTING ENDPOINT"""
        try:
            response = requests.get(
                f"{self.api_url}/ride-request/{ride_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Failed to fetch ride request: {e}"}
    
    # NEW METHODS for multi-client features
    
    def get_available_drivers(self) -> dict:
        """Get list of available drivers - NEW ENDPOINT"""
        try:
            response = requests.get(
                f"{self.api_url}/drivers/available",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Failed to fetch drivers: {e}"}
    
    def get_all_drivers(self) -> dict:
        """Get all registered drivers - NEW ENDPOINT"""
        try:
            response = requests.get(
                f"{self.api_url}/drivers",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Failed to fetch drivers: {e}"}
    
    def get_ride_assignment(self, ride_assignment_id: str) -> dict:
        """Get ride assignment details - NEW ENDPOINT"""
        try:
            response = requests.get(
                f"{self.api_url}/ride-assignment/{ride_assignment_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Failed to fetch ride assignment: {e}"}


def interactive_mode(client: MiniUberClient):
    """Interactive mode for testing"""
    print("\n" + "="*60)
    print(f"🚕 Mini Uber User Client - Port {client.client_port}")
    print(f"👤 User ID: {client.user_id}")
    print("="*60)
    
    while True:
        print("\n📋 Menu:")
        print("1. Request a ride")
        print("2. View all my ride requests")
        print("3. View specific ride request")
        print("4. View available drivers")
        print("5. View all drivers")
        print("6. Test ping")
        print("7. Exit")
        
        choice = input("\n👉 Enter choice (1-7): ").strip()
        
        if choice == "1":
            source = input("📍 Enter pickup location: ").strip()
            dest = input("📍 Enter dropoff location: ").strip()
            result = client.create_ride_request(source, dest)
            print(f"\n{json.dumps(result, indent=2)}")
            
        elif choice == "2":
            result = client.get_ride_requests()
            print(f"\n{json.dumps(result, indent=2)}")
            
        elif choice == "3":
            ride_id = int(input("🔢 Enter ride ID: "))
            result = client.get_ride_request(ride_id)
            print(f"\n{json.dumps(result, indent=2)}")
            
        elif choice == "4":
            result = client.get_available_drivers()
            print(f"\n{json.dumps(result, indent=2)}")
            
        elif choice == "5":
            result = client.get_all_drivers()
            print(f"\n{json.dumps(result, indent=2)}")
            
        elif choice == "6":
            result = client.ping()
            print(f"\n{json.dumps(result, indent=2)}")
            
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")


def main():
    """Demo usage - can specify port and user_id"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mini Uber User Client')
    parser.add_argument('--port', type=int, default=7000, help='Client port (default: 7000)')
    parser.add_argument('--user-id', type=int, help='User ID (default: port number)')
    parser.add_argument('--server', type=str, default='http://localhost:8000', 
                       help='Server URL (default: http://localhost:8000)')
    parser.add_argument('--interactive', action='store_true', 
                       help='Run in interactive mode')
    
    args = parser.parse_args()
    
    # Create client
    client = MiniUberClient(
        base_url=args.server,
        user_id=args.user_id,
        client_port=args.port
    )
    
    if args.interactive:
        # Run interactive mode
        interactive_mode(client)
    else:
        # Run demo
        print(f"=== Mini Uber Client Demo (Port {args.port}) ===")
        
        # Test ping
        print("\n=== Testing Ping ===")
        ping_result = client.ping()
        print(f"Ping result: {ping_result}")
        
        # Check available drivers
        print("\n=== Checking Available Drivers ===")
        drivers = client.get_available_drivers()
        print(f"Available drivers: {drivers}")
        
        # Test ride request creation
        print("\n=== Testing Ride Request Creation ===")
        ride_result = client.create_ride_request(
            source_location="123 Main St, Chennai",
            dest_location="456 Park Ave, Chennai"
        )
        
        # Test getting all ride requests
        print("\n=== Getting All Ride Requests ===")
        all_rides = client.get_ride_requests()
        print(f"All rides: {all_rides}")


if __name__ == "__main__":
    main()