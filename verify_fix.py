import sys
import os
import datetime
from unittest.mock import MagicMock

# Add serverapp to path so imports work
current_dir = os.getcwd()
serverapp_dir = os.path.join(current_dir, "serverapp")
sys.path.insert(0, serverapp_dir)

# Mock the database imports essentially, or let them fail gracefully if we want to unit test
# But since the file imports them at top level, we have to mock them BEFORE import
sys.modules["sqlalchemy"] = MagicMock()
sys.modules["sqlalchemy.orm"] = MagicMock()
sys.modules["sqlalchemy.orm"].Session = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi"].Depends = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["database"] = MagicMock()
sys.modules["database.connections"] = MagicMock()
sys.modules["database.models"] = MagicMock()

# Mock the specific objects matched
sys.modules["database.models"].Base = MagicMock()
sys.modules["database.models"].RideRequest = MagicMock()

# Now we can import server_matcher
# It will try to use SessionLocal etc, so we need to ensure they exist on the mock
sys.modules["database.connections"].SessionLocal = MagicMock()
sys.modules["database.connections"].engine = MagicMock()

import server_matcher

def test_offline_logic():
    print("🧪 Verifying is_driver_online logic...")
    
    # Mock a driver object
    driver = MagicMock()
    driver.driver_id = 999
    driver.available = True
    
    # CASE 1: Driver has OLD heartbeat (60s ago)
    # ------------------------------------------
    driver.updated_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
    
    # Mock DB session to return this driver
    db_session = MagicMock()
    db_session.query.return_value.filter.return_value.first.return_value = driver
    
    # Mock requests.get to fail (simulate no python client port open)
    server_matcher.requests.get = MagicMock(side_effect=Exception("Connection refused"))
    
    # Run the function
    result = server_matcher.is_driver_online(999, db=db_session)
    
    print(f"   Driver with 60s old heartbeat: Online={result}")
    
    if result is False:
        print("   ✅ PASS: Stale driver correctly marked offline")
    else:
        print("   ❌ FAIL: Stale driver marked online")
        
    # CASE 2: Driver has FRESH heartbeat (10s ago)
    # ------------------------------------------
    driver.updated_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
    
    result_fresh = server_matcher.is_driver_online(999, db=db_session)
    print(f"   Driver with 10s old heartbeat: Online={result_fresh}")
    
    if result_fresh is True:
        print("   ✅ PASS: Fresh driver correctly marked online")
    else:
        print("   ❌ FAIL: Fresh driver marked offline")

if __name__ == "__main__":
    try:
        test_offline_logic()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
