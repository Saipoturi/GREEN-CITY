import os
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DATABASE_NAME = os.environ.get('DATABASE', 'greencity.db')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DATABASE_NAME)

def get_db_connection():
    """Establish and return a connection to the SQLite database with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Create database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'resident',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            address TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            photo_filename TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

def seed_db():
    """Seed initial demo accounts and verified environmental reports."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if users already exist
    cursor.execute("SELECT COUNT(*) AS count FROM users")
    user_count = cursor.fetchone()['count']

    if user_count == 0:
        print("[GreenCity] Seeding initial users...")
        # 1. Admin
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Civic Environmental Officer",
            "admin@greencity.org",
            generate_password_hash("Admin@123"),
            "admin"
        ))

        # 2. Resident 1
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Sarah Jenkins",
            "resident@greencity.org",
            generate_password_hash("Resident@123"),
            "resident"
        ))

        # 3. Resident 2
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Marcus Chen",
            "marcus@greencity.org",
            generate_password_hash("Marcus@123"),
            "resident"
        ))

        conn.commit()

    # Check if reports already exist
    cursor.execute("SELECT COUNT(*) AS count FROM reports")
    report_count = cursor.fetchone()['count']

    if report_count == 0:
        print("[GreenCity] Seeding verified environmental reports...")
        # Retrieve resident user IDs
        cursor.execute("SELECT id FROM users WHERE role = 'resident' ORDER BY id ASC")
        resident_ids = [row['id'] for row in cursor.fetchall()]
        res1_id = resident_ids[0] if resident_ids else 1
        res2_id = resident_ids[1] if len(resident_ids) > 1 else res1_id

        sample_reports = [
            (
                res1_id,
                "Overflowing municipal waste bins on Elmwood Avenue",
                "Garbage dumping",
                "Multiple commercial and household garbage bags have been left piling up around the bins for over four days, causing severe odor and obstructing the pedestrian walkway. Stray animals are scattering plastic and organic waste.",
                "742 Elmwood Ave, Green District",
                40.7135,
                -74.0040,
                "sample_garbage.jpg",
                "In Progress",
                "Sanitation emergency team dispatched. High-capacity compactor scheduled for installation by Friday.",
                "2026-10-24 09:30:00"
            ),
            (
                res2_id,
                "Subsurface municipal water pipe leaking clean potable water",
                "Water leakage and water wastage",
                "A significant underground pipe fracture near the curb is discharging clean treated water continuously onto the roadway. Substantial water is being wasted into the storm drain for over 18 hours.",
                "128 Oakridge Blvd & 4th Cross",
                40.7160,
                -74.0095,
                "sample_water.jpg",
                "Pending",
                "Report forwarded to Municipal Water Authority. Field crew alert #WA-4091 created.",
                "2026-10-27 14:15:00"
            ),
            (
                res1_id,
                "Heavy industrial smoke emissions near residential boundary",
                "Air pollution",
                "Industrial smokestacks emitting thick dark particulate smoke continuously during morning hours. Resident sensors indicate elevated PM2.5 levels exceeding safe municipal air quality thresholds.",
                "550 Riverfront Industrial Corridor",
                40.7210,
                -74.0150,
                "sample_air.jpg",
                "In Progress",
                "Clean Air Compliance notice issued to plant management. Real-time air quality monitors installed at perimeter.",
                "2026-10-25 08:00:00"
            ),
            (
                res2_id,
                "Plastic bottle and food container pollution along park lake",
                "Plastic waste",
                "Large volume of single-use plastic bottles, styrofoam containers, and micro-plastics washed up on the western shoreline of Meadowbrook Lake, endangering local waterfowl and water purity.",
                "Meadowbrook Eco Park, North Lake Shore",
                40.7090,
                -73.9980,
                "sample_plastic.jpg",
                "Resolved",
                "Community volunteer cleanup drive conducted with City Parks Dept. 180kg of recyclable plastics collected and sent to recycling facility.",
                "2026-10-22 11:20:00"
            ),
            (
                res1_id,
                "Unauthorized felling of mature oak trees in community grove",
                "Tree cutting and damage to green spaces",
                "Four mature canopy oak trees were chopped down along the public greenway without city forestry permit postings. Heavy branches and sawdust left across the walking trail.",
                "Highland Community Park, West Gate",
                40.7175,
                -74.0025,
                "sample_tree.jpg",
                "Resolved",
                "Illegal tree felling citation issued to commercial contractor. 12 native saplings planted in compensatory reforestation program.",
                "2026-10-20 16:45:00"
            ),
            (
                res2_id,
                "Discarded construction drywall and chemical paint cans",
                "Garbage dumping",
                "Unauthorized dumping of drywall sheets, insulation foam, and partially full paint solvent containers in an open alleyway. Hazardous materials require proper disposal.",
                "310 Sycamore Alley, East Ward",
                40.7055,
                -74.0112,
                None,
                "Pending",
                "Awaiting hazardous waste inspection team dispatch.",
                "2026-10-28 07:45:00"
            )
        ]

        for rep in sample_reports:
            cursor.execute("""
                INSERT INTO reports (
                    user_id, title, category, description, address,
                    latitude, longitude, photo_filename, status, admin_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rep[0], rep[1], rep[2], rep[3], rep[4],
                rep[5], rep[6], rep[7], rep[8], rep[9], rep[10], rep[10]
            ))

        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    seed_db()
    print("[GreenCity] Database initialized and verified.")
