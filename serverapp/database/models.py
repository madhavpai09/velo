"""
Fixed Database Models
All missing columns added, proper types defined
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric
from datetime import datetime
from .connections import Base

class RideRequest(Base):
    """Ride request model with all required fields"""
    __tablename__ = "ride_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    source_location = Column(String, nullable=False)
    dest_location = Column(String, nullable=False)
    status = Column(String, default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ride_type = Column(String, default="auto")  # NEW: auto, school_pool, moto
    fare = Column(Integer, nullable=True)  # NEW: Fare amount in rupees

class DriverInfo(Base):
    """Driver information model"""
    __tablename__ = "driver_info"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, nullable=False, unique=True, index=True)
    available = Column(Boolean, default=True, index=True)
    current_location = Column(String)
    vehicle_type = Column(String, default="auto")  # NEW: auto, moto
    phone_number = Column(String, nullable=True)   # NEW: Driver phone
    vehicle_details = Column(String, nullable=True) # NEW: e.g. "Toyota Etios - KA05..."
    is_verified_safe = Column(Boolean, default=False) # NEW: For school pool pass
    penalty_count = Column(Integer, default=0)     # NEW: For rejecting priority rides
    rating = Column(Numeric(3, 2), default=5.00)   # NEW: Average rating (e.g., 4.85)
    rating_count = Column(Integer, default=0)      # NEW: Total number of ratings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DriverRating(Base):
    """Individual driver ratings"""
    __tablename__ = "driver_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    ride_id = Column(Integer, nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MatchedRide(Base):
    """
    Matched ride model - connects users with drivers
    FIXED: Added all missing columns (otp, ride_id, created_at)
    """
    __tablename__ = "matched_rides"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    driver_id = Column(Integer, nullable=False, index=True)
    ride_id = Column(Integer, nullable=True, index=True)  # FIX: Added for direct ride lookup
    otp = Column(String, nullable=True)  # FIX: Added for user-driver verification
    status = Column(String, default="pending_notification", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # FIX: Added for stale detection
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# NEW: School Pool Pass Models

class StudentProfile(Base):
    """Student profile for school rides"""
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    school_name = Column(String, nullable=False)
    school_address = Column(String, nullable=False)
    home_address = Column(String, nullable=False)
    grade = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Subscription(Base):
    """Monthly subscription for school rides"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    driver_id = Column(Integer, nullable=True) # NEW: Assigned driver
    status = Column(String, default="active")  # active, inactive, expired
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SubscriptionSchedule(Base):
    """Weekly schedule for subscriptions"""
    __tablename__ = "subscription_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, nullable=False, index=True)
    day_of_week = Column(String, nullable=False)  # monday, tuesday, etc.
    pickup_time = Column(String, nullable=False)  # HH:MM
    ride_type = Column(String, nullable=False)  # pickup (home->school) or drop (school->home)

# NEW: Enhanced School Pool Pass Models

class School(Base):
    """School information"""
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False, index=True)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    contact_phone = Column(String)
    contact_email = Column(String)
    verified = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SchoolRoute(Base):
    """School route with stops"""
    __tablename__ = "school_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, nullable=False, index=True)
    route_name = Column(String, nullable=False)
    route_type = Column(String, nullable=False)  # pickup or dropoff
    start_time = Column(String, nullable=False)  # TIME stored as string
    end_time = Column(String, nullable=False)
    days_of_week = Column(String, nullable=False)  # JSON array as string
    max_capacity = Column(Integer, default=6)
    current_occupancy = Column(Integer, default=0)
    status = Column(String, default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RouteStop(Base):
    """Individual stops on a route"""
    __tablename__ = "route_stops"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, nullable=False, index=True)
    stop_order = Column(Integer, nullable=False)
    stop_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    estimated_arrival_offset = Column(Integer, nullable=False)  # minutes from start
    created_at = Column(DateTime, default=datetime.utcnow)

class SchoolPassSubscription(Base):
    """School Pool Pass subscription"""
    __tablename__ = "school_pass_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    route_id = Column(Integer, nullable=False)
    stop_id = Column(Integer, nullable=False)
    assigned_driver_id = Column(Integer)
    subscription_type = Column(String, nullable=False)  # monthly, quarterly, annual
    start_date = Column(String, nullable=False)  # DATE stored as string
    end_date = Column(String, nullable=False)
    status = Column(String, default="active", index=True)
    payment_status = Column(String, default="pending")
    amount_paid = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DriverRouteAssignment(Base):
    """Driver assignment to routes"""
    __tablename__ = "driver_route_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, nullable=False, index=True)
    route_id = Column(Integer, nullable=False, index=True)
    assignment_date = Column(String, nullable=False)  # DATE stored as string
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class PickupEvent(Base):
    """Pickup/dropoff event log"""
    __tablename__ = "pickup_events"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, index=True)
    driver_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    route_id = Column(Integer, nullable=False)
    stop_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)  # picked_up, dropped_off, absent, etc.
    event_time = Column(DateTime, default=datetime.utcnow)
    location_lat = Column(Numeric(10, 8))
    location_lng = Column(Numeric(11, 8))
    otp_verified = Column(Boolean, default=False)
    notes = Column(String)
    photo_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)