# GreenCity — Community Environmental Reporting Platform 🌿

A complete, responsive full-stack civic environmental reporting and accountability platform aligned with the **United Nations Sustainable Development Goals (SDGs)**. 

GreenCity enables residents to report local environmental issues—such as garbage dumping, water leakage, air pollution, plastic waste, and illegal tree felling—using interactive map coordinates, photographic evidence, and real-time tracking, while providing municipal administrators with a triage and analytics dashboard.

---

## 🎯 United Nations Sustainable Development Goals (SDGs) Focus

GreenCity directly operationalizes the following UN SDGs:
- **SDG 11: Sustainable Cities and Communities** (Target 11.6: Reduce urban environmental impact and municipal waste burdens).
- **SDG 12: Responsible Consumption and Production** (Target 12.5: Substantially reduce waste generation through civic reporting and recycling diversion).
- **SDG 13: Climate Action** (Target 13.3: Improve awareness and human capacity on climate mitigation and industrial smoke compliance).
- **SDG 14: Life Below Water** (Target 14.1: Prevent and reduce marine & waterway plastic litter and runoff).
- **SDG 15: Life on Land** (Target 15.2: Halt deforestation and protect public green urban canopies).

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, Modern CSS3 (custom green-and-white design system with CSS variables, responsive grid & flexbox, glassmorphic touches), Vanilla JavaScript (ES6+).
- **Mapping**: [Leaflet.js](https://leafletjs.com/) (v1.9.4) & [OpenStreetMap](https://www.openstreetmap.org/) for interactive map pin-dropping, coordinates auto-detection, and public reporting markers.
- **Analytics & Visualizations**: [Chart.js](https://www.chartjs.org/) (v4.4.1) for live category distribution, status breakdown, and activity trends.
- **Backend**: Python 3.10+ with [Flask](https://flask.palletsprojects.com/) (v3.x).
- **Database**: SQLite3 with foreign key constraints, connection pooling, and automated schema migration/seeding.
- **Security & Auth**: Werkzeug password hashing (`pbkdf2:sha256`), secure session management, role-based route decorators (`@login_required`, `@admin_required`), and safe file upload validation (`secure_filename`, extension whitelist, 16MB ceiling).

---

## ✨ Features & Pages

### 1. Home Page (`/`)
- Modern, clean hero section with live civic impact stats (Verified Reports, Problems Solved, Resolution Rate).
- Interactive **UN SDGs Spotlight** detailing Goals 11, 12, 13, 14, and 15.
- **5 Environmental Categories** grid with live issue counts and quick-report triggers:
  1. *Garbage dumping*
  2. *Water leakage and water wastage*
  3. *Air pollution*
  4. *Plastic waste*
  5. *Tree cutting and damage to green spaces*
- Recent verified citizen submissions with status badges and responsive cards.
- "How It Works" 3-step civic workflow.

### 2. Report an Issue (`/report`)
- Accessible 2-column submission form.
- Title, category selector, detailed description.
- **Evidence photo upload** with drag-and-drop zone, file type validation, and instant thumbnail preview.
- **Interactive Leaflet Map Pin Picker**:
  - Click anywhere on the map or drag the pin to set exact coordinates.
  - "Use My Current Location" button using HTML5 Geolocation.
  - Live coordinate feedback display (`Lat: 40.7128, Lng: -74.0060`).
  - Sensible fallback to default downtown coordinates if location permissions are denied.

### 3. View Environmental Reports (`/reports`)
- **Full Interactive Public Map** with custom color-coded pins:
  - 🟡 **Pending** (Amber)
  - 🔵 **In Progress** (Blue)
  - 🟢 **Resolved** (Emerald Green)
- Clicking any map pin reveals a popup card with report photo thumbnail, title, address, and quick-link to open the full modal.
- Multi-dimensional Search & Filter toolbar:
  - Keyword search across titles, descriptions, and street addresses.
  - Category filter dropdown.
  - Status filter dropdown (`Pending`, `In Progress`, `Resolved`).
  - Sort order (Newest first, Oldest first).
- Detailed report modal with full image inspection, submitter name, precise coordinates, and official municipal feedback.

### 4. Resident Dashboard (`/dashboard`)
- Welcome header with personalized profile summary and quick "Report New Issue" button.
- Personal KPI counters: My Total Reports, Pending Review, In Progress, and Community Eco-Points.
- Status progression tracker: `1. Reported` ➔ `2. In Action` ➔ `3. Resolved`.
- Status filter tabs (`All`, `Pending`, `In Progress`, `Resolved`).
- Official city resolution notes prominently highlighted.

### 5. Admin Dashboard (`/admin`)
- Strictly restricted to authorized administrators (`role == 'admin'`).
- High-level operational KPI metric cards: Total Reports, Pending Review, Under Action, Resolved Cases, Resolution Rate (%).
- **Interactive Chart.js Visualizations**:
  - Doughnut chart: *Reports by Category*
  - Pie chart: *Reports by Status*
  - Bar chart: *Citizen Activity Timeline*
- Comprehensive Report Management Table with inline search and filtering.
- **Status & Feedback Update Modal**:
  - Change status between `Pending`, `In Progress`, and `Resolved`.
  - Add official municipal feedback and dispatch notes that sync immediately to the database and resident dashboard.
  - Delete inappropriate or spam reports with photo cleanup.

### 6. Authentication (`/login`, `/register`, `/logout`)
- User registration with role selection (Resident default or Administrator).
- Secure password hashing and credential verification.
- **One-Click Demo Login Helpers**:
  - `⚡ Demo Resident` (`resident@greencity.org` / `Resident@123`)
  - `🛡️ Demo Admin` (`admin@greencity.org` / `Admin@123`)

---

## 📁 Project Structure

```
green-city/
├── app.py                  # Core Flask backend with all routes, auth & APIs
├── database.py             # SQLite schema initialization and seed dataset
├── test_app.py             # Comprehensive automated unittest test suite
├── requirements.txt        # Python dependency manifest
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # Complete platform documentation
├── static/
│   ├── css/
│   │   └── style.css       # Master stylesheet (theme, components, responsive)
│   ├── js/
│   │   ├── main.js         # Navigation, modals, alerts, drag-drop preview
│   │   ├── map.js          # Leaflet OpenStreetMap logic (picker & public map)
│   │   └── admin.js        # Chart.js analytics & admin status modals
│   └── uploads/            # Uploaded citizen evidence photos & sample media
└── templates/
    ├── base.html           # Master layout with navbar, footer, modals, CDNs
    ├── index.html          # Modern landing page with SDGs and recent reports
    ├── report.html         # Interactive issue submission with map picker
    ├── reports.html        # Public reports directory and interactive map
    ├── login.html          # Authentication with one-click demo logins
    ├── register.html       # Citizen registration form
    ├── dashboard.html      # Resident tracking dashboard with status timeline
    └── admin.html          # Admin triage portal with Chart.js analytics
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
Ensure you have **Python 3.10 or higher** installed.

### 2. Install Dependencies
In your terminal, navigate to the project directory and install the required packages:
```powershell
pip install -r requirements.txt
```

### 3. Initialize Database
Initialize the SQLite database with default tables and realistic seed data:
```powershell
python database.py
```

### 4. Run the Automated Tests (Optional)
Run the test suite to verify all endpoints, database queries, and role-based permissions:
```powershell
python -m unittest -v test_app.py
```

### 5. Start the Application
Run the Flask server:
```powershell
python app.py
```
Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## 🔑 Demo Credentials

To test the application immediately without manually registering:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Civic Administrator** | `admin@greencity.org` | `Admin@123` | Full access to Admin Portal, Chart.js charts, status triage, notes & deletion |
| **Citizen Resident** | `resident@greencity.org` | `Resident@123` | Report submission, photo upload, resident dashboard, personal tracking |

*(You can also click the **"⚡ Demo Resident"** or **"🛡️ Demo Admin"** buttons on the Login page for one-click access).*

---

## 📡 REST API Endpoints

- `GET /api/reports`: Returns JSON array of geo-tagged reports for Leaflet map markers.
- `GET /api/reports/<id>`: Returns full single report details for modal inspection.
- `GET /api/admin/stats`: Returns aggregated counts for Chart.js analytics (admin only).

---

## 🔒 Security & Quality Standards

- **Server-Side Validation**: Form inputs are validated on both client and server sides.
- **SQL Injection Prevention**: All database queries use parameterized SQL (`?` placeholders).
- **File Upload Safety**: Validated extensions (`png`, `jpg`, `jpeg`, `gif`, `webp`), content length enforced (`<= 16MB`), and files are renamed using UUIDs and `secure_filename`.
- **Role-Based Authorization**: Administrative routes are protected by `@admin_required`, preventing unauthorized status edits.
- **Responsive Layout**: Fluid breakpoints optimized for mobile (320px+), tablet, and desktop viewports.
