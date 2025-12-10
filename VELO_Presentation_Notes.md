# 🎓 Project Presentation Guide: VELO Cabs & School Pool

Use this guide to explain your project confidently to your professors.

---

## 🛠️ Technology Stack

### 1. Frontend (User Interface)
*   **Framework:** **React.js** (v18)
*   **Language:** **TypeScript**
*   **Build Tool:** **Vite**
*   **Styling:** **Tailwind CSS**
*   **Routing:** React Router DOM

**Why?**
*   **React:** Component-based architecture makes it easy to build reusable UI elements (like the Map view or Driver Card).
*   **TypeScript:** Adds static typing to JavaScript, which prevents many common bugs (like missing data fields) before the code even runs. It makes the code more robust and "enterprise-grade."
*   **Vite:** Extremely fast build tool, making development quick and efficient.
*   **Tailwind CSS:** Utility-first CSS allows for rapid styling without writing separate CSS files, keeping the design consistent.

### 2. Backend (Server & Logic)
*   **Framework:** **FastAPI** (Python)
*   **Language:** **Python 3.10+**
*   **ORM (Object-Relational Mapping):** **SQLAlchemy**

**Why?**
*   **FastAPI:** As the name suggests, it's very fast and modern. It automatically generates API documentation (Swagger UI), which is great for testing and explaining APIs. It also uses Python type hints for validation.
*   **Python:** Great for backend logic, easy to read, and has powerful libraries.
*   **SQLAlchemy:** Allows us to interact with the database using Python classes (Models) instead of writing raw SQL queries. This prevents SQL injection attacks and makes the code cleaner.

### 3. Database (Data Storage)
*   **Database:** **PostgreSQL**
*   **Management:** SQLAlchemy (via Python)

**Why?**
*   **PostgreSQL:** Industry-standard, production-grade relational database.
    *   *Reason for choice:* Provides ACID compliance, excellent concurrency handling, and robust data integrity. It's what real companies use in production.
    *   *Features:* Advanced indexing, foreign key constraints, transaction support, and can handle thousands of concurrent connections.
    *   *Note:* Unlike SQLite (file-based), PostgreSQL is a client-server database, making it suitable for multi-user applications.

---

## 🚀 Key Features Explained

1.  **Ride Booking (Uber-like):**
    *   Users can select pickup/dropoff.
    *   Fare is calculated based on distance.
    *   Drivers receive requests and can accept/decline.
2.  **School Pool Pass (New Feature):**
    *   **Problem Solved:** Parents need safe, reliable, recurring transport for kids.
    *   **Solution:** A monthly subscription model for specific school routes.
    *   **Safety:** Verified drivers only, OTP verification for every pickup/dropoff.
3.  **Driver Dashboard:**
    *   Drivers have a dedicated view to manage regular rides and school routes.

---

## 🙋‍♂️ Potential Professor Questions (Q&A)

**Q1: Why did you choose polling instead of WebSockets for real-time updates?**
*   **Answer:** "For this version of the project, I used **Short Polling** (the client asks the server for updates every few seconds). While WebSockets provide true real-time bi-directional communication, polling is simpler to implement and robust enough for a prototype to demonstrate the core logic without the complexity of managing persistent socket connections."

**Q2: How do you handle data consistency?**
*   **Answer:** "I used **SQLAlchemy** with ACID transactions. For example, when a driver accepts a ride, we lock that ride row or check its status atomically to ensure two drivers can't accept the same ride simultaneously."

**Q3: How is the 'School Pool' safety ensured?**
*   **Answer:** "Safety is a priority. We implemented:
    1.  **OTP Verification:** The student must provide a 4-digit code to the driver to start the ride.
    2.  **Verified Drivers:** Only drivers with `is_verified_safe=True` in the database can be assigned school routes.
    3.  **Status Tracking:** We track every event (Picked Up, Dropped Off, Absent) with timestamps."

**Q4: Why TypeScript over JavaScript?**
*   **Answer:** "TypeScript provides **type safety**. In a complex app with many data models (User, Driver, Ride, School, Route), it's easy to make mistakes like accessing `user.name` when it might be undefined. TypeScript catches these errors at compile time, reducing runtime crashes."

**Q5: How would you scale this if 10,000 users joined tomorrow?**
*   **Answer:**
    1.  **Database:** Migrate from SQLite to **PostgreSQL** for better concurrent write performance.
    2.  **Backend:** Run multiple instances of the FastAPI server behind a load balancer (like Nginx).
    3.  **Caching:** Introduce **Redis** to cache frequent data like 'available drivers' to reduce database load.
