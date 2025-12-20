from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import random
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import sys
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide, StudentProfile, Subscription, SubscriptionSchedule, DriverRating, User
from models.schemas import RideCreate, DriverCreate, UpdateMatchPayload

# NEW: Schemas for School Pool
class StudentCreate(BaseModel):
    user_id: int
    name: str
    school_name: str
    school_address: str
    home_address: str
    grade: str

class SubscriptionCreate(BaseModel):
    user_id: int
    student_id: int
    start_date: str  # ISO format
    end_date: str    # ISO format
    days: list[str]  # ["monday", "wednesday"]
    pickup_time: str # "08:00"
    drop_time: str   # "15:00"

class RatingCreate(BaseModel):
    driver_id: int
    user_id: int
    ride_id: int
    rating: int
    comment: str = None

# Create tables
Base.metadata.create_all(bind=engine)

# Create app WITHOUT lifespan to avoid issues
app = FastAPI(title="Orchestrator Server")

# Add CORS middleware AFTER app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schema for driver registration
class DriverRegister(BaseModel):
    driver_id: str
    name: str
    port: int
    location: dict
    vehicle_type: str = "auto"
    phone_number: str = None
    vehicle_details: str = None

# Auth Configuration
SECRET_KEY = "supersecretkey" # In prod, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60 # 30 days for easy testing

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class DriverLogin(BaseModel):
    driver_id: int

# Auth Utils
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
def read_root():
    return {"message": "Mini Uber API v3 - WORKING"}

# NEW: Auth Endpoints
@app.post("/api/signup", response_model=Token)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Compatible with OAuth2 standard form
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login/json", response_model=Token)
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    # JSON compatible endpoint for frontend
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.full_name,
        "phone": current_user.phone_number
    }

@app.post("/driver/register")
def register_driver(driver: DriverRegister, db: Session = Depends(get_db)):
    """Register a new driver"""
    try:
        print(f"\n📥 Driver registration: {driver.driver_id}")
        
        raw_id = str(driver.driver_id).strip()
        if raw_id.upper().startswith("DRIVER-"):
            raw_id = raw_id[7:]
        
        numeric_id = int(raw_id)
        lat = float(driver.location.get('lat', 0))
        lng = float(driver.location.get('lng', 0))
        location_str = f"{lat},{lng}"
            
        # FIX: Store port in vehicle_details (Hack to avoid schema change)
        import json
        
        # Create details object
        details_obj = {
            "details": driver.vehicle_details,
            "port": driver.port
        }
        details_json = json.dumps(details_obj)
            
        # Check if driver already exists
        existing = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        
        if existing:
            # Update existing driver
            existing.available = True
            existing.current_location = location_str
            existing.vehicle_type = driver.vehicle_type
            existing.phone_number = driver.phone_number
            existing.vehicle_details = details_json # Store JSON
            print(f"✅ Updated driver {numeric_id} (Port: {driver.port})")
        else:
            # Generate NEW ID if none provided (or 0)
            if numeric_id > 0:
                print(f"   Using requested custom ID: {numeric_id}")
            else:
                max_id = db.query(func.max(DriverInfo.driver_id)).scalar() or 0
                numeric_id = max(8100, max_id + 1)
                print(f"   Auto-assigned ID: {numeric_id}")
            
            new_driver = DriverInfo(
                driver_id=numeric_id,
                available=True,
                current_location=location_str,
                vehicle_type=driver.vehicle_type,
                phone_number=driver.phone_number,
                vehicle_details=details_json # Store JSON
            )
            db.add(new_driver)
            print(f"✅ Created NEW driver {numeric_id} (Port: {driver.port})")
            
        db.commit()
        
        return {
            "message": "Driver registered successfully",
            "driver_id": f"DRIVER-{numeric_id}",
            "numeric_id": numeric_id,
            "vehicle_type": driver.vehicle_type
        }
    except Exception as e:
        with open("error.log", "a") as f:
            f.write(f"Registration error: {str(e)}\n")
        print(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/driver/login")
def login_driver(login: DriverLogin, db: Session = Depends(get_db)):
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == login.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    return {
        "message": "Login successful",
        "driver_id": f"DRIVER-{driver.driver_id}",
        "numeric_id": driver.driver_id,
        "name": f"Driver {driver.driver_id}", # Mock name
        "vehicle_type": driver.vehicle_type,
        "phone_number": driver.phone_number,
        "vehicle_details": driver.vehicle_details
    }

@app.post("/driver/heartbeat")
def driver_heartbeat(driver_id: str, db: Session = Depends(get_db)):
    try:
        numeric_id = int(driver_id.replace("DRIVER-", ""))
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        driver.updated_at = datetime.utcnow()
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/driver/set-availability")
def set_driver_availability(driver_id: str, is_available: bool, db: Session = Depends(get_db)):
    try:
        numeric_id = int(driver_id.replace("DRIVER-", ""))
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        driver.available = is_available
        db.commit()
        print(f"✅ Driver {numeric_id} availability: {is_available}")
        return {"message": "Availability updated", "is_available": is_available}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ride/")
def create_ride(ride: RideCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new = RideRequest(
        user_id=current_user.id, # Use authenticated user ID
        source_location=ride.pickup,
        dest_location=ride.drop,
        status="pending"
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    print(f"✅ Ride {new.id} created for user {current_user.id}")
    return {"message": "ride created", "ride_id": new.id}

@app.post("/api/ride/{ride_id}/cancel")
def cancel_ride(ride_id: int, db: Session = Depends(get_db)):
    """User cancels a ride request"""
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    print(f"🚫 User cancelling ride {ride_id}")
    
    # Check if there is a match in progress
    match = db.query(MatchedRide).filter(MatchedRide.ride_id == ride_id).first()
    if match:
        # If driver was assigned, free them
        if match.status == "accepted" or match.status == "in_progress":
             driver = db.query(DriverInfo).filter(DriverInfo.driver_id == match.driver_id).first()
             if driver:
                 driver.available = True
                 print(f"   🔓 Driver {driver.driver_id} freed")
        
        db.delete(match)
        print(f"   🗑️  Match deleted")
    
    # Mark ride as cancelled
    ride.status = "cancelled"
    db.commit()
    
    return {"message": "Ride cancelled successfully"}

@app.post("/api/ride-request")
def create_ride_request(request: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Frontend endpoint for creating ride requests"""
    try:
        # Accept both formats: {pickup, drop} or {source_location, dest_location}
        source = request.get('source_location') or request.get('pickup')
        dest = request.get('dest_location') or request.get('drop')
        
        # Use AUTHENTICATED user_id
        user_id = current_user.id
        
        if not source or not dest:
            raise HTTPException(status_code=400, detail="Missing location data")
        
        new = RideRequest(
            user_id=user_id,
            source_location=source,
            dest_location=dest,
            status="pending",
            ride_type=request.get('ride_type', 'auto'),
            fare=request.get('fare')
        )
        db.add(new)
        db.commit()
        db.refresh(new)
        print(f"✅ Ride request {new.id} created for user {user_id}")
        
        return {
            "message": "Ride request created successfully",
            "data": {
                "id": new.id,
                "source_location": new.source_location,
                "dest_location": new.dest_location,
                "user_id": new.user_id,
                "status": new.status,
                "created_at": new.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drivers/available")
def get_available_drivers(db: Session = Depends(get_db)):
    """Get all available drivers"""
    drivers = db.query(DriverInfo).filter(DriverInfo.available == True).all()
    return {
        "count": len(drivers),
        "drivers": [
            {
                "driver_id": d.driver_id,
                "location": d.current_location,
                "available": d.available,
                "rating": float(d.rating) if d.rating else 5.0
            }
            for d in drivers
        ]
    }

@app.get("/api/drivers/{driver_id}")
def get_driver_info(driver_id: int, db: Session = Depends(get_db)):
    """Get specific driver info"""
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {
        "driver_id": driver.driver_id,
        "location": driver.current_location,
        "available": driver.available
    }

@app.post("/driver/update-location")
def update_driver_location(driver_id: str, location: dict, db: Session = Depends(get_db)):
    """Update driver location"""
    try:
        numeric_id = int(driver_id.replace("DRIVER-", ""))
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        location_str = f"{location['lat']},{location['lng']}"
        driver.current_location = location_str
        driver.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Location updated", "location": location_str}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update location error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/driver/{driver_id}/pending-ride")
def get_driver_pending_ride(driver_id: int, db: Session = Depends(get_db)):
    """Check if there's a pending ride OFFERED to this driver"""
    db.rollback()  # Fresh snapshot
    
    match = db.query(MatchedRide).filter(
        MatchedRide.driver_id == driver_id,
        MatchedRide.status == "offered"
    ).first()
    
    if not match:
        # DEBUG: Why no match?
        check = db.query(MatchedRide).filter(MatchedRide.driver_id == driver_id).first()
        if check:
            print(f"   🔍 Polling Debug: Driver {driver_id} has match {check.id} but status is '{check.status}' (Wanted 'offered')")
        else:
            # Only print occasionally to avoid spam
            pass 
        return {"has_ride": False}
        
    ride = db.query(RideRequest).filter(RideRequest.id == match.ride_id).first()
    if not ride:
        print(f"   ⚠️ Polling Error: Match {match.id} has no Ride {match.ride_id}")
        return {"has_ride": False}
    
    print(f"   ✅ Driver {driver_id} found OFFERED ride {ride.id}")
    return {
        "has_ride": True,
        "match_id": match.id,
        "ride_id": ride.id,
        "user_id": ride.user_id,
        "pickup_location": ride.source_location,
        "dropoff_location": ride.dest_location,
        "status": "offered",
        "ride_type": ride.ride_type,  # NEW: Return ride type
        "fare": ride.fare  # NEW: Return fare amount
    }

@app.post("/api/driver/{driver_id}/accept-ride/{match_id}")
def accept_ride(driver_id: int, match_id: int, db: Session = Depends(get_db)):
    match = db.query(MatchedRide).filter(MatchedRide.id == match_id).first()
    if not match or match.driver_id != driver_id:
        raise HTTPException(status_code=404, detail="Match not found")
        
    ride = db.query(RideRequest).filter(RideRequest.id == match.ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    otp = str(random.randint(1000, 9999))
    
    # Explicit update to ensure persistence
    rows_match = db.query(MatchedRide).filter(MatchedRide.id == match_id).update({
        "status": "accepted",
        "otp": otp
    })
    
    rows_ride = db.query(RideRequest).filter(RideRequest.id == match.ride_id).update({
        "status": "matched"
    })
    
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if driver:
        driver.available = False
        
    db.commit()
    
    # Re-fetch to confirm
    updated_ride = db.query(RideRequest).filter(RideRequest.id == match.ride_id).first()
    print(f"✅ Driver {driver_id} ACCEPTED ride {updated_ride.id}. Status: {updated_ride.status}. OTP: {otp}")
    return {"status": "accepted", "otp": otp}

@app.post("/api/driver/{driver_id}/decline-ride/{match_id}")
def decline_ride(driver_id: int, match_id: int, db: Session = Depends(get_db)):
    match = db.query(MatchedRide).filter(MatchedRide.id == match_id).first()
    if not match or match.driver_id != driver_id:
        raise HTTPException(status_code=404, detail="Match not found")
        
    # Update match status to declined
    db.query(MatchedRide).filter(MatchedRide.id == match_id).update({
        "status": "declined"
    })
    
    # Reset ride status to pending so it can be matched again
    db.query(RideRequest).filter(RideRequest.id == match.ride_id).update({
        "status": "pending"
    })
    
    db.commit()
    print(f"❌ Driver {driver_id} DECLINED ride {match.ride_id}")
    return {"status": "declined"}

@app.post("/api/ride/{ride_id}/verify-otp")
def verify_otp(ride_id: int, otp: str, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    # Fix: Verify against the ACCEPTED match
    match = db.query(MatchedRide).filter(
        MatchedRide.ride_id == ride_id,
        MatchedRide.status == "accepted"
    ).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if match.otp != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    ride.status = "in_progress"
    match.status = "in_progress"
    db.commit()
    print(f"🚀 Ride {ride_id} STARTED")
    return {"status": "in_progress", "message": "Ride started"}

@app.get("/api/driver/{driver_id}/current-ride")
def get_driver_current_ride(driver_id: int, db: Session = Depends(get_db)):
    match = db.query(MatchedRide).filter(
        MatchedRide.driver_id == driver_id,
        MatchedRide.status.in_(["accepted", "in_progress"])
    ).first()
    
    if not match:
        return {"has_ride": False}
        
    ride = db.query(RideRequest).filter(RideRequest.id == match.ride_id).first()
    if not ride:
        return {"has_ride": False}
        
    return {
        "has_ride": True,
        "ride_id": ride.id,
        "user_id": ride.user_id,
        "pickup_location": ride.source_location,
        "dropoff_location": ride.dest_location,
        "status": match.status,
        "otp": match.otp
    }

@app.get("/api/user/{user_id}/ride-status")
def get_user_ride_status(user_id: int, db: Session = Depends(get_db)):
    db.rollback() # Ensure fresh data
    ride = db.query(RideRequest).filter(
        RideRequest.user_id == user_id
    ).order_by(RideRequest.created_at.desc()).first()
    
    if not ride or ride.status in ["completed", "cancelled"]:
        return {"has_ride": False}
        
    # Fix: Get the LATEST match that is NOT declined
    match = db.query(MatchedRide).filter(
        MatchedRide.ride_id == ride.id,
        MatchedRide.status != "declined"
    ).order_by(MatchedRide.id.desc()).first()
    
    response = {
        "has_ride": True,
        "ride_id": ride.id,
        "status": ride.status,
        "pickup_location": ride.source_location,
        "dropoff_location": ride.dest_location,
    }
    
    if match:
        response["driver_id"] = match.driver_id
        response["otp"] = match.otp
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == match.driver_id).first()
        if driver:
            response["driver_location"] = driver.current_location
            
    return response

@app.post("/api/driver/{driver_id}/complete-ride/{ride_id}")
def complete_ride(driver_id: int, ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    match = db.query(MatchedRide).filter(MatchedRide.ride_id == ride_id).first()
    
    ride.status = "completed"
    if match:
        db.delete(match)
        
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if driver:
        driver.available = True
        
    db.commit()
    print(f"🏁 Ride {ride_id} COMPLETED")
    return {"status": "completed"}

@app.post("/api/rate-driver")
def rate_driver(rating: RatingCreate, db: Session = Depends(get_db)):
    """Rate a driver after a ride"""
    
    # Check if rating already exists
    existing = db.query(DriverRating).filter(
        DriverRating.ride_id == rating.ride_id,
        DriverRating.user_id == rating.user_id
    ).first()
    
    if existing:
        return {"message": "Rating already submitted"}
        
    # Create rating
    new_rating = DriverRating(
        driver_id=rating.driver_id,
        user_id=rating.user_id,
        ride_id=rating.ride_id,
        rating=rating.rating,
        comment=rating.comment
    )
    db.add(new_rating)
    
    # Update driver average rating
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == rating.driver_id).first()
    if driver:
        # Calculate new average
        # (old_avg * old_count + new_rating) / (old_count + 1)
        current_rating = float(driver.rating) if driver.rating else 5.0
        current_count = driver.rating_count if driver.rating_count else 0
        
        new_total = (current_rating * current_count) + rating.rating
        new_count = current_count + 1
        new_avg = new_total / new_count
        
        driver.rating = new_avg
        driver.rating_count = new_count
        
    db.commit()
    print(f"⭐ Driver {rating.driver_id} rated {rating.rating} stars by User {rating.user_id}")
    
    return {"message": "Rating submitted successfully"}

# NEW: Student Profile APIs
@app.post("/api/student/create")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    # Limit to 3 students per user
    count = db.query(StudentProfile).filter(StudentProfile.user_id == student.user_id).count()
    if count >= 3:
        raise HTTPException(status_code=400, detail="Maximum 3 students allowed per user account")

    new_student = StudentProfile(
        user_id=student.user_id,
        name=student.name,
        school_name=student.school_name,
        school_address=student.school_address,
        home_address=student.home_address,
        grade=student.grade
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    print(f"✅ Student profile created: {new_student.name}")
    return {"message": "Student profile created", "id": new_student.id}

@app.get("/api/user/{user_id}/students")
def get_user_students(user_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).all()
    return {"students": students}

# NEW: Subscription APIs
@app.post("/api/subscription/create")
def create_subscription(sub: SubscriptionCreate, db: Session = Depends(get_db)):
    # Check for existing active subscription
    existing = db.query(SchoolPassSubscription).filter(
        SchoolPassSubscription.student_id == sub.student_id,
        SchoolPassSubscription.status == "active"
    ).first()
    
    if existing:
        print(f"⚠️ Student {sub.student_id} already has an active subscription {existing.id}")
        # Return existing subscription info to prevent duplicates
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == existing.assigned_driver_id).first() if existing.assigned_driver_id else None
        return {
            "message": "Student already subscribed", 
            "id": existing.id,
            "driver_id": existing.assigned_driver_id,
            "driver_name": f"Driver {driver.driver_id}" if driver else "Pending Assignment"
        }

    # Find a driver (NEW LOGIC: 1 School, Max 3 Kids)
    # 1. Identify School from Route
    route = db.query(SchoolRoute).filter(SchoolRoute.id == sub.route_id).first()
    if not route:
         raise HTTPException(status_code=404, detail="Route not found")
         
    assigned_driver_id = None
    
    assigned_driver_id = None
    
    # --- DRIVER ASSIGNMENT STRATEGY ---
    # Goal: Max 3 students per driver, Single School per driver
    
    # 1. Look for a driver ALREADY assigned to this school with capacity
    # Get all active subscriptions for this school's routes
    school_subs = db.query(SchoolPassSubscription).join(SchoolRoute).filter(
        SchoolRoute.school_id == route.school_id,
        SchoolPassSubscription.status == "active",
        SchoolPassSubscription.assigned_driver_id != None
    ).all()
    
    # Group by driver to count loads
    driver_loads = {}
    for s in school_subs:
        did = s.assigned_driver_id
        driver_loads[did] = driver_loads.get(did, 0) + 1
        
    # Find a driver with < 3 students
    candidate_driver_id = None
    for did, load in driver_loads.items():
        if load < 3:
            candidate_driver_id = did
            break
            
    # 2. If no existing driver has space, recruit a NEW driver
    if not candidate_driver_id:
        # Find drivers with ZERO active subscriptions (Free agents)
        # We need check all active subscriptions to exclude busy drivers
        busy_driver_ids = db.query(SchoolPassSubscription.assigned_driver_id).filter(
            SchoolPassSubscription.status == "active",
            SchoolPassSubscription.assigned_driver_id != None
        ).distinct().all()
        busy_ids = [r[0] for r in busy_driver_ids]
        
        free_driver = db.query(DriverInfo).filter(
            DriverInfo.is_verified_safe == True,
            DriverInfo.available == True,
            ~DriverInfo.driver_id.in_(busy_ids)
        ).first()
        
        if free_driver:
            candidate_driver_id = free_driver.driver_id
            
    assigned_driver_id = candidate_driver_id
    
    # Create subscription
    new_sub = Subscription(
        user_id=sub.user_id,
        student_id=sub.student_id,
        driver_id=assigned_driver_id, # Assign driver
        start_date=datetime.fromisoformat(sub.start_date.replace('Z', '+00:00')),
        end_date=datetime.fromisoformat(sub.end_date.replace('Z', '+00:00')),
        status="active"
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    
    # Create schedules
    for day in sub.days:
        # Pickup schedule
        pickup = SubscriptionSchedule(
            subscription_id=new_sub.id,
            day_of_week=day,
            pickup_time=sub.pickup_time,
            ride_type="pickup"
        )
        db.add(pickup)
        
        # Drop schedule
        drop = SubscriptionSchedule(
            subscription_id=new_sub.id,
            day_of_week=day,
            pickup_time=sub.drop_time,
            ride_type="drop"
        )
        db.add(drop)
    
    db.commit()
    print(f"✅ Subscription created for student {sub.student_id}. Driver: {assigned_driver_id}")
    
    return {
        "message": "Subscription created", 
        "id": new_sub.id,
        "driver_id": assigned_driver_id,
        "driver_name": f"Driver {assigned_driver_id}" if assigned_driver_id else "Pending Assignment"
    }

@app.delete("/api/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a student profile"""
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Check for active subscriptions
    active_sub = db.query(SchoolPassSubscription).filter(
        SchoolPassSubscription.student_id == student_id, 
        SchoolPassSubscription.status == "active"
    ).first()
    
    if active_sub:
        raise HTTPException(status_code=400, detail="Cannot delete student with active subscription. Cancel subscription first.")
        
    db.delete(student)
    db.commit()
    return {"message": "Student deleted"}

@app.delete("/api/subscriptions/{subscription_id}")
def cancel_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Cancel a subscription"""
    sub = db.query(SchoolPassSubscription).filter(SchoolPassSubscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
        
    
    # Only decrement occupancy if the subscription was active
    if sub.status == "active":
        route = db.query(SchoolRoute).filter(SchoolRoute.id == sub.route_id).first()
        if route and route.current_occupancy > 0:
            route.current_occupancy -= 1
            print(f"📉 Decremented occupancy for route {route.route_name} to {route.current_occupancy}")
            
    sub.status = "cancelled"
    sub.end_date = datetime.utcnow().strftime("%Y-%m-%d") # End immediately
    
    db.commit()
    return {"message": "Subscription cancelled"}

# OLD ENDPOINT - REPLACED BY SCHOOL POOL PASS VERSION BELOW
# @app.get("/api/user/{user_id}/subscriptions")
# def get_user_subscriptions_old(user_id: int, db: Session = Depends(get_db)):
#     subs = db.query(Subscription).filter(Subscription.user_id == user_id).all()
#     result = []
#     for sub in subs:
#         student = db.query(StudentProfile).filter(StudentProfile.id == sub.student_id).first()
#         schedules = db.query(SubscriptionSchedule).filter(SubscriptionSchedule.subscription_id == sub.id).all()
#         result.append({
#             "id": sub.id,
#             "student_name": student.name if student else "Unknown",
#             "status": sub.status,
#             "driver_id": sub.driver_id,
#             "schedules": schedules
#         })
#     return {"subscriptions": result}

# ==================== SCHOOL POOL PASS APIs ====================

from database.models import School, SchoolRoute, RouteStop, SchoolPassSubscription, PickupEvent, DriverRouteAssignment

# Pydantic schemas for School Pool Pass
class SchoolPassSubscriptionCreate(BaseModel):
    user_id: int
    student_id: int
    route_id: int
    stop_id: int
    subscription_type: str  # monthly, quarterly, annual
    start_date: str  # YYYY-MM-DD

@app.get("/api/schools")
def get_schools(db: Session = Depends(get_db)):
    """Get all verified schools"""
    schools = db.query(School).filter(School.verified == True).all()
    return {
        "schools": [
            {
                "id": s.id,
                "name": s.name,
                "address": s.address,
                "city": s.city,
                "latitude": str(s.latitude) if s.latitude else None,
                "longitude": str(s.longitude) if s.longitude else None
            }
            for s in schools
        ]
    }

@app.get("/api/schools/{school_id}/routes")
def get_school_routes(school_id: int, db: Session = Depends(get_db)):
    """Get all routes for a school with stops"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    routes = db.query(SchoolRoute).filter(
        SchoolRoute.school_id == school_id,
        SchoolRoute.status == "active"
    ).all()
    
    result = []
    for route in routes:
        stops = db.query(RouteStop).filter(
            RouteStop.route_id == route.id
        ).order_by(RouteStop.stop_order).all()
        
        result.append({
            "id": route.id,
            "name": route.route_name,
            "type": route.route_type,
            "start_time": route.start_time,
            "capacity": route.max_capacity,
            "available_seats": route.max_capacity - route.current_occupancy,
            "stops": [
                {
                    "id": stop.id,
                    "name": stop.stop_name,
                    "address": stop.address,
                    "latitude": str(stop.latitude),
                    "longitude": str(stop.longitude),
                    "eta_offset": stop.estimated_arrival_offset
                }
                for stop in stops
            ]
        })
    
    return {
        "school": {
            "id": school.id,
            "name": school.name,
            "address": school.address
        },
        "routes": result
    }

@app.post("/api/subscriptions/school-pass")
def create_school_pass_subscription(sub: SchoolPassSubscriptionCreate, db: Session = Depends(get_db)):
    """Create a new School Pool Pass subscription"""
    
    # Verify student exists
    student = db.query(StudentProfile).filter(StudentProfile.id == sub.student_id).first()
    if not student or student.user_id != sub.user_id:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify route exists and has capacity
    route = db.query(SchoolRoute).filter(SchoolRoute.id == sub.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    if route.current_occupancy >= route.max_capacity:
        raise HTTPException(status_code=400, detail="Route is at full capacity")
    
    # Verify stop exists on route
    stop = db.query(RouteStop).filter(
        RouteStop.id == sub.stop_id,
        RouteStop.route_id == sub.route_id
    ).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found on this route")
    
    # Calculate end date based on subscription type
    from datetime import datetime, timedelta
    start_date = datetime.strptime(sub.start_date, "%Y-%m-%d")
    if sub.subscription_type == "monthly":
        end_date = start_date + timedelta(days=30)
        amount = 4500  # ₹150 per ride * 30 days
    elif sub.subscription_type == "quarterly":
        end_date = start_date + timedelta(days=90)
        amount = 12000
    else:  # annual
        end_date = start_date + timedelta(days=365)
        amount = 45000
    
    # Find available safe driver (simple assignment for now)
    available_driver = db.query(DriverInfo).filter(
        DriverInfo.is_verified_safe == True,
        DriverInfo.available == True
    ).first()
    
    # Create subscription
    new_sub = SchoolPassSubscription(
        user_id=sub.user_id,
        student_id=sub.student_id,
        route_id=sub.route_id,
        stop_id=sub.stop_id,
        assigned_driver_id=available_driver.driver_id if available_driver else None,
        subscription_type=sub.subscription_type,
        start_date=sub.start_date,
        end_date=end_date.strftime("%Y-%m-%d"),
        status="active",
        payment_status="paid",
        amount_paid=amount
    )
    db.add(new_sub)
    
    # Update route occupancy
    route.current_occupancy += 1
    
    db.commit()
    db.refresh(new_sub)

    # NEW: Create schedules based on route days
    import json
    try:
        if route.days_of_week:
            days = json.loads(route.days_of_week)
            for day in days:
                # Create schedule for this day
                schedule = SubscriptionSchedule(
                    subscription_id=new_sub.id,
                    day_of_week=day.lower(),
                    pickup_time=route.start_time,
                    ride_type=route.route_type
                )
                db.add(schedule)
            db.commit()
            print(f"✅ Created {len(days)} schedule entries for subscription {new_sub.id}")
    except Exception as e:
        print(f"❌ Failed to create schedules: {e}")
    
    print(f"✅ School Pass subscription created: {new_sub.id} for student {student.name}")
    
    return {
        "subscription_id": new_sub.id,
        "assigned_driver": {
            "driver_id": available_driver.driver_id if available_driver else None,
            "name": f"Driver {available_driver.driver_id}" if available_driver else "Pending",
            "phone": available_driver.phone_number if available_driver else None,
            "vehicle": available_driver.vehicle_details if available_driver else None
        } if available_driver else None,
        "route_details": {
            "route_name": route.route_name,
            "pickup_time": route.start_time,
            "stop_address": stop.address
        },
        "amount": amount,
        "status": "active"
    }

@app.get("/api/subscriptions/school-pass/{subscription_id}")
def get_school_pass_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Get School Pool Pass subscription details"""
    sub = db.query(SchoolPassSubscription).filter(SchoolPassSubscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    student = db.query(StudentProfile).filter(StudentProfile.id == sub.student_id).first()
    route = db.query(SchoolRoute).filter(SchoolRoute.id == sub.route_id).first()
    stop = db.query(RouteStop).filter(RouteStop.id == sub.stop_id).first()
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == sub.assigned_driver_id).first() if sub.assigned_driver_id else None
    
    return {
        "id": sub.id,
        "student": {
            "id": student.id,
            "name": student.name,
            "school": student.school_name
        } if student else None,
        "driver": {
            "id": driver.driver_id,
            "name": f"Driver {driver.driver_id}",
            "phone": driver.phone_number
        } if driver else None,
        "route": {
            "name": route.route_name,
            "pickup_time": route.start_time,
            "stop_address": stop.address
        } if route and stop else None,
        "status": sub.status,
        "start_date": sub.start_date,
        "end_date": sub.end_date
    }

@app.get("/api/user/{user_id}/subscriptions")
def get_user_subscriptions(user_id: int, db: Session = Depends(get_db)):
    """Get all subscriptions for a user with today's OTP"""
    subscriptions = db.query(SchoolPassSubscription).filter(
        SchoolPassSubscription.user_id == user_id,
        SchoolPassSubscription.status == "active"
    ).all()
    
    result = []
    for sub in subscriptions:
        student = db.query(StudentProfile).filter(StudentProfile.id == sub.student_id).first()
        route = db.query(SchoolRoute).filter(SchoolRoute.id == sub.route_id).first()
        stop = db.query(RouteStop).filter(RouteStop.id == sub.stop_id).first()
        
        # Generate deterministic OTP for today (for demo purposes)
        # In prod, this should be stored in a daily_rides table
        import hashlib
        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d")
        seed = f"{sub.id}-{today_str}-SECRET"
        otp_hash = hashlib.sha256(seed.encode()).hexdigest()
        otp = str(int(otp_hash[:8], 16) % 10000).zfill(4)
        
        result.append({
            "id": sub.id,
            "student_name": student.name if student else "Unknown",
            "school_name": student.school_name if student else "Unknown",
            "route_name": route.route_name if route else "Unknown",
            "pickup_time": route.start_time if route else "00:00",
            "driver_id": sub.assigned_driver_id,
            "status": sub.status,
            "otp": otp  # Include OTP for today
        })
        
    return {"subscriptions": result}

@app.get("/api/drivers/{driver_id}/school-routes")
def get_driver_school_routes(driver_id: int, db: Session = Depends(get_db)):
    """Get driver's assigned school routes for today"""
    from datetime import date
    import datetime
    
    # Get day of week (Monday=0, Sunday=6)
    # We map 0-4 to mon-fri. For demo, let's assume it's a weekday.
    day_name = date.today().strftime("%A").lower()
    
    # Join with Subscription to ensure it's active
    # Handle both full names ("monday") and short names ("mon")
    target_days = [day_name, day_name[:3]]
    
    schedules = db.query(SubscriptionSchedule).join(
        SchoolPassSubscription, 
        SubscriptionSchedule.subscription_id == SchoolPassSubscription.id
    ).filter(
        SchoolPassSubscription.assigned_driver_id == driver_id,
        SchoolPassSubscription.status == "active",
        SubscriptionSchedule.day_of_week.in_(target_days)
    ).all()
    
    if not schedules:
        # Fallback for demo: if no schedule found for 'today', try 'monday' (for testing weekends)
        fallback_days = ["monday", "mon"]
        schedules = db.query(SubscriptionSchedule).join(
            SchoolPassSubscription,
            SubscriptionSchedule.subscription_id == SchoolPassSubscription.id
        ).filter(
            SchoolPassSubscription.assigned_driver_id == driver_id,
            SchoolPassSubscription.status == "active",
            SubscriptionSchedule.day_of_week.in_(fallback_days)
        ).all()
        
    if not schedules:
        return {"today_routes": [], "stats": {"total_students": 0}}

    # Group by Route + Type (Pickup/Drop)
    # Key: (route_id, ride_type)
    trips = {}
    
    for sched in schedules:
        sub = db.query(SchoolPassSubscription).filter(SchoolPassSubscription.id == sched.subscription_id).first()
        route = db.query(SchoolRoute).filter(SchoolRoute.id == sub.route_id).first()
        if not route: continue
        
        trip_key = (route.id, sched.ride_type)
        
        if trip_key not in trips:
            trips[trip_key] = {
                "route_id": route.id,
                "route_name": route.route_name,
                "type": sched.ride_type,
                "start_time": sched.pickup_time,
                "students": [],
                "stops": []
            }
            
        # Add Student to Trip
        student = db.query(StudentProfile).filter(StudentProfile.id == sub.student_id).first()
        stop = db.query(RouteStop).filter(RouteStop.id == sub.stop_id).first()
        
        if student and stop:
            import hashlib
            today_str = date.today().strftime("%Y-%m-%d")
            seed = f"{sub.id}-{today_str}-SECRET"
            otp_hash = hashlib.sha256(seed.encode()).hexdigest()
            otp = str(int(otp_hash[:8], 16) % 10000).zfill(4)
            
            trips[trip_key]["students"].append({
                "id": student.id,
                "name": student.name,
                "stop_id": stop.id,
                "stop_name": stop.stop_name,
                "otp": otp,
                "status": "pending"
            })

    # Final formatting with stops
    final_routes = []
    for key, trip in trips.items():
        route_id = trip["route_id"]
        
        # Get stops for this route
        stops = db.query(RouteStop).filter(RouteStop.route_id == route_id).order_by(RouteStop.stop_order).all()
        
        # If dropping off, reverse the stops logically or just list them
        # For simplicity, we just list stops and let frontend show navigation
        
        trip["stops"] = [
            {
                "id": s.id,
                "name": s.stop_name,
                "lat": float(s.latitude),
                "lng": float(s.longitude),
                "eta": trip["start_time"]
            } for s in stops
        ]
        
        final_routes.append(trip)
        
    return {
        "today_routes": final_routes,
        "stats": {
            "total_students": sum(len(t["students"]) for t in final_routes)
        }
    }

class PickupEventCreate(BaseModel):
    student_id: int
    route_id: int
    stop_id: int
    event_type: str  # picked_up, dropped_off, absent
    otp: str = None
    location: dict = None
    notes: str = None

@app.post("/api/drivers/{driver_id}/pickup-event")
def record_pickup_event(driver_id: int, event: PickupEventCreate, db: Session = Depends(get_db)):
    """Record a pickup/dropoff event"""
    
    # Verify student exists
    student = db.query(StudentProfile).filter(StudentProfile.id == event.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Find subscription
    subscription = db.query(SchoolPassSubscription).filter(
        SchoolPassSubscription.student_id == event.student_id,
        SchoolPassSubscription.route_id == event.route_id,
        SchoolPassSubscription.assigned_driver_id == driver_id,
        SchoolPassSubscription.status == "active"
    ).first()
    
    # Create event
    new_event = PickupEvent(
        subscription_id=subscription.id if subscription else None,
        driver_id=driver_id,
        student_id=event.student_id,
        route_id=event.route_id,
        stop_id=event.stop_id,
        event_type=event.event_type,
        otp_verified=True if event.otp else False,
        notes=event.notes
    )
    
    if event.location:
        new_event.location_lat = event.location.get("lat")
        new_event.location_lng = event.location.get("lng")
    
    db.add(new_event)
    db.commit()
    
    print(f"📍 {event.event_type.upper()}: Student {student.name} by Driver {driver_id}")
    
    return {
        "event_id": new_event.id,
        "status": "success",
        "message": f"Student {event.event_type.replace('_', ' ')}"
    }

@app.post("/api/drivers/{driver_id}/start-school-route")
def start_school_route(driver_id: int, route_id: int, db: Session = Depends(get_db)):
    """Start a school route and mark driver as busy"""
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
        
    # Mark driver as unavailable for normal rides
    driver.available = False
    db.commit()
    
    print(f"🚌 Driver {driver_id} started school route {route_id}. Marked as BUSY.")
    
    return {"status": "success", "message": "Route started, driver marked busy"}

# ==================== ADMIN APIs ====================

@app.get("/api/admin/drivers")
def get_all_drivers_admin(db: Session = Depends(get_db)):
    """Get all drivers with verification status and details"""
    drivers = db.query(DriverInfo).all()
    
    result = []
    for driver in drivers:
        # Count assigned school routes
        assigned_routes = db.query(SchoolPassSubscription).filter(
            SchoolPassSubscription.assigned_driver_id == driver.driver_id,
            SchoolPassSubscription.status == "active"
        ).count()
        
        result.append({
            "driver_id": driver.driver_id,
            "name": f"Driver {driver.driver_id}",
            "phone_number": driver.phone_number,
            "vehicle_type": driver.vehicle_type,
            "vehicle_details": driver.vehicle_details,
            "is_verified_safe": driver.is_verified_safe,
            "available": driver.available,
            "current_location": driver.current_location,
            "penalty_count": driver.penalty_count,
            "rating": float(driver.rating) if driver.rating else 5.0,
            "rating_count": driver.rating_count,
            "assigned_routes": assigned_routes,
            "created_at": driver.created_at.isoformat() if driver.created_at else None,
            "updated_at": driver.updated_at.isoformat() if driver.updated_at else None
        })
    
    return {
        "total_drivers": len(result),
        "verified_drivers": sum(1 for d in result if d["is_verified_safe"]),
        "drivers": result
    }

@app.post("/api/admin/drivers/{driver_id}/verify")
def verify_driver(driver_id: int, db: Session = Depends(get_db)):
    """Mark a driver as verified safe for school routes"""
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    driver.is_verified_safe = True
    db.commit()
    
    print(f"✅ Driver {driver_id} marked as VERIFIED SAFE")
    
    return {
        "message": "Driver verified successfully",
        "driver_id": driver_id,
        "is_verified_safe": True
    }

@app.post("/api/admin/drivers/{driver_id}/unverify")
def unverify_driver(driver_id: int, db: Session = Depends(get_db)):
    """Remove verification status from a driver"""
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    driver.is_verified_safe = False
    db.commit()
    
    print(f"⚠️ Driver {driver_id} verification REMOVED")
    
    return {
        "message": "Driver verification removed",
        "driver_id": driver_id,
        "is_verified_safe": False
    }

@app.get("/api/admin/drivers/verified")
def get_verified_drivers(db: Session = Depends(get_db)):
    """Get only verified drivers"""
    drivers = db.query(DriverInfo).filter(DriverInfo.is_verified_safe == True).all()
    
    result = []
    for driver in drivers:
        assigned_routes = db.query(SchoolPassSubscription).filter(
            SchoolPassSubscription.assigned_driver_id == driver.driver_id,
            SchoolPassSubscription.status == "active"
        ).count()
        
        result.append({
            "driver_id": driver.driver_id,
            "name": f"Driver {driver.driver_id}",
            "phone_number": driver.phone_number,
            "vehicle_details": driver.vehicle_details,
            "assigned_routes": assigned_routes
        })
    
    return {
        "count": len(result),
        "drivers": result
    }

@app.get("/api/admin/drivers/{driver_id}/details")
def get_driver_details(driver_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific driver"""
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Get assigned subscriptions
    subscriptions = db.query(SchoolPassSubscription).filter(
        SchoolPassSubscription.assigned_driver_id == driver_id,
        SchoolPassSubscription.status == "active"
    ).all()
    
    subscription_details = []
    for sub in subscriptions:
        student = db.query(StudentProfile).filter(StudentProfile.id == sub.student_id).first()
        route = db.query(SchoolRoute).filter(SchoolRoute.id == sub.route_id).first()
        
        subscription_details.append({
            "subscription_id": sub.id,
            "student_name": student.name if student else "Unknown",
            "route_name": route.route_name if route else "Unknown",
            "start_date": sub.start_date,
            "end_date": sub.end_date
        })
    
    return {
        "driver_id": driver.driver_id,
        "name": f"Driver {driver.driver_id}",
        "phone_number": driver.phone_number,
        "vehicle_type": driver.vehicle_type,
        "vehicle_details": driver.vehicle_details,
        "is_verified_safe": driver.is_verified_safe,
        "available": driver.available,
        "current_location": driver.current_location,
        "penalty_count": driver.penalty_count,
        "assigned_subscriptions": subscription_details,
    }
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚗 Mini Uber Main Server")
    print("="*60)
    print("   Port: 8000")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")