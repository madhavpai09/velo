import requests
import json
from typing import Optional

class MiniUberClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def ping(self) -> dict:
        """Test ping endpoint"""
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
    
    def create_ride_request(self, source_location: str, dest_location: str, user_id: int) -> dict:
        """
        Create a new ride request
        This is the main API that PostMan will call
        """
        try:
            payload = {
                "source_location": source_location,
                "dest_location": dest_location,
                "user_id": user_id
            }
            
            print(f"🚗 Creating ride request...")
            print(f"📍 From: {source_location}")
            print(f"📍 To: {dest_location}")
            print(f"👤 User ID: {user_id}")
            
            response = requests.post(
                f"{self.api_url}/ride-request",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Response: {result}")
            return result
            
        except requests.RequestException as e:
            error_msg = f"Failed to create ride request: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def get_ride_requests(self) -> dict:
        """Get all ride requests"""
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
        """Get a specific ride request"""
        try:
            response = requests.get(
                f"{self.api_url}/ride-request/{ride_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Failed to fetch ride request: {e}"}

def main():
    """Demo usage of the client"""
    client = MiniUberClient()
    
    # Test ping
    print("=== Testing Ping ===")
    ping_result = client.ping()
    print(f"Ping result: {ping_result}")
    
    # Test ride request creation
    print("\n=== Testing Ride Request Creation ===")
    ride_result = client.create_ride_request(
        source_location="123 Main St, Chennai",
        dest_location="456 Park Ave, Chennai", 
        user_id=12345
    )
    
    # Test getting all ride requests
    print("\n=== Getting All Ride Requests ===")
    all_rides = client.get_ride_requests()
    print(f"All rides: {all_rides}")

if __name__ == "__main__":
    main()