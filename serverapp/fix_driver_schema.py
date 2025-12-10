import sqlite3
import os

DB_FILE = "mini_uber.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"❌ Database file {DB_FILE} not found!")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check existing columns in driver_info
        cursor.execute("PRAGMA table_info(driver_info)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Current columns in driver_info: {columns}")

        # Add missing columns to driver_info
        new_columns = {
            "vehicle_type": "TEXT DEFAULT 'auto'",
            "phone_number": "TEXT",
            "vehicle_details": "TEXT",
            "is_verified_safe": "BOOLEAN DEFAULT 0",
            "penalty_count": "INTEGER DEFAULT 0",
            "parent_rating": "FLOAT DEFAULT 5.0",
            "school_routes_completed": "INTEGER DEFAULT 0"
        }

        for col, dtype in new_columns.items():
            if col not in columns:
                print(f"Adding column {col}...")
                try:
                    cursor.execute(f"ALTER TABLE driver_info ADD COLUMN {col} {dtype}")
                except Exception as e:
                    print(f"Error adding {col}: {e}")
            else:
                print(f"Column {col} already exists.")

        conn.commit()
        print("✅ Migration completed successfully.")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
