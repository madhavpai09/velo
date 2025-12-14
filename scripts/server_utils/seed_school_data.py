import sys
import os
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal
from database.models import School, SchoolRoute, RouteStop, StudentProfile, DriverInfo

def seed_data():
    db = SessionLocal()
    try:
        print("🌱 Seeding School Pool data...")

        # 1. Create School
        school = db.query(School).filter_by(name="Delhi Public School").first()
        if not school:
            school = School(
                name="Delhi Public School",
                address="Survey No. 35/1A, Sathnur Village, Bagalur Post, Jala Hobli, North, Bengaluru, Karnataka 562149",
                city="Bengaluru",
                latitude=13.1500,
                longitude=77.6400,
                contact_phone="080-29724861",
                verified=True
            )
            db.add(school)
            db.commit()
            print(f"✅ Created School: {school.name}")
        else:
            print(f"ℹ️ School already exists: {school.name}")

        # 2. Create Route
        route = db.query(SchoolRoute).filter_by(route_name="Indiranagar Route A").first()
        if not route:
            route = SchoolRoute(
                school_id=school.id,
                route_name="Indiranagar Route A",
                route_type="pickup",
                start_time="07:30",
                end_time="08:30",
                days_of_week='["monday", "tuesday", "wednesday", "thursday", "friday"]',
                max_capacity=10,
                current_occupancy=0
            )
            db.add(route)
            db.commit()
            print(f"✅ Created Route: {route.route_name}")
        else:
            print(f"ℹ️ Route already exists: {route.route_name}")

        # 3. Create Stops
        stops_data = [
            {
                "order": 1,
                "name": "Indiranagar Metro",
                "address": "Indiranagar, Bengaluru",
                "lat": 12.9784,
                "lng": 77.6408,
                "offset": 0
            },
            {
                "order": 2,
                "name": "Domlur Flyover",
                "address": "Domlur, Bengaluru",
                "lat": 12.9600,
                "lng": 77.6400,
                "offset": 15
            },
            {
                "order": 3,
                "name": "Koramangala Sony Signal",
                "address": "Koramangala, Bengaluru",
                "lat": 12.9350,
                "lng": 77.6200,
                "offset": 30
            }
        ]

        for stop_data in stops_data:
            stop = db.query(RouteStop).filter_by(route_id=route.id, stop_name=stop_data["name"]).first()
            if not stop:
                stop = RouteStop(
                    route_id=route.id,
                    stop_order=stop_data["order"],
                    stop_name=stop_data["name"],
                    address=stop_data["address"],
                    latitude=stop_data["lat"],
                    longitude=stop_data["lng"],
                    estimated_arrival_offset=stop_data["offset"]
                )
                db.add(stop)
                print(f"✅ Created Stop: {stop.stop_name}")
        
        db.commit()

        # 4. Create Test Student for User 7000
        student = db.query(StudentProfile).filter_by(name="Arjun Pai").first()
        if not student:
            student = StudentProfile(
                user_id=7000,
                name="Arjun Pai",
                school_name="Delhi Public School",
                school_address="Bagalur, Bengaluru",
                home_address="Indiranagar, Bengaluru",
                grade="5th Standard"
            )
            db.add(student)
            db.commit()
            print(f"✅ Created Student: {student.name}")
        else:
            print(f"ℹ️ Student already exists: {student.name}")
            
        # 5. Ensure a verified driver exists
        driver = db.query(DriverInfo).filter_by(driver_id=5001).first()
        if not driver:
            driver = DriverInfo(
                driver_id=5001,
                available=True,
                current_location="12.9716,77.5946",
                vehicle_type="auto",
                is_verified_safe=True
            )
            db.add(driver)
            db.commit()
            print(f"✅ Created Verified Driver: 5001")
        else:
            driver.is_verified_safe = True
            db.commit()
            print(f"ℹ️ Driver 5001 verified status updated")

        print("\n🎉 Seeding completed successfully!")

    except Exception as e:
        print(f"❌ Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
