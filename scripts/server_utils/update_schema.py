from database.connections import engine
from sqlalchemy import text

def update_schema():
    with engine.connect() as conn:
        try:
            # Add rating column
            conn.execute(text("ALTER TABLE driver_info ADD COLUMN IF NOT EXISTS rating NUMERIC(3, 2) DEFAULT 5.00;"))
            print("Added rating column")
            
            # Add rating_count column
            conn.execute(text("ALTER TABLE driver_info ADD COLUMN IF NOT EXISTS rating_count INTEGER DEFAULT 0;"))
            print("Added rating_count column")
            
            # Create driver_ratings table if not exists (SQLAlchemy create_all should handle this, but just in case)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS driver_ratings (
                    id SERIAL PRIMARY KEY,
                    driver_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    ride_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL,
                    comment VARCHAR,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
                );
            """))
            print("Ensured driver_ratings table exists")
            
            conn.commit()
            print("Schema update successful")
        except Exception as e:
            print(f"Error updating schema: {e}")

if __name__ == "__main__":
    update_schema()
