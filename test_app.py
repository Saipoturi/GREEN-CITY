import unittest
import io
import os
import json
import uuid
from app import app
import database

class GreenCityTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        # Initialize and seed DB
        database.init_db()
        database.seed_db()

    def test_01_index_page(self):
        """Test home page loads with statistics and SDG content."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'GreenCity', response.data)
        self.assertIn(b'Sustainable Development Goals', response.data)
        self.assertIn(b'Total Citizen Reports', response.data)

    def test_02_reports_public_page_and_api(self):
        """Test public reports page and JSON map API."""
        response = self.client.get('/reports')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Community Environmental Reports', response.data)

        # JSON API for Leaflet map
        api_res = self.client.get('/api/reports')
        self.assertEqual(api_res.status_code, 200)
        data = json.loads(api_res.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first_report = data[0]
        self.assertIn('title', first_report)
        self.assertIn('category', first_report)
        self.assertIn('latitude', first_report)
        self.assertIn('longitude', first_report)
        self.assertIn('status', first_report)

        # Test single report API
        single_res = self.client.get(f"/api/reports/{first_report['id']}")
        self.assertEqual(single_res.status_code, 200)
        single_data = json.loads(single_res.data)
        self.assertEqual(single_data['id'], first_report['id'])

    def test_03_resident_registration_and_login(self):
        """Test user registration, login, and dashboard access."""
        # Register a new citizen with unique email
        test_email = f"citizen_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = self.client.post('/register', data={
            'name': 'Test Citizen',
            'email': test_email,
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'resident'
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)
        self.assertIn(b'Welcome to GreenCity, Test Citizen!', reg_res.data)

        # Access resident dashboard
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b'Resident Environmental Portal', dash_res.data)

        # Logout
        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)

        # Login again
        login_res = self.client.post('/login', data={
            'email': test_email,
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Welcome back, Test Citizen!', login_res.data)

    def test_04_submit_environmental_report(self):
        """Test submitting a new environmental issue with file upload."""
        # Login as demo resident
        self.client.get('/login?demo=resident', follow_redirects=True)

        # Submit report
        photo_data = (io.BytesIO(b"fake image data"), "test_photo.jpg")
        report_res = self.client.post('/report', data={
            'title': 'Illegal industrial chemical dumping in creek',
            'category': 'Water leakage and water wastage',
            'description': 'Discharge of milky chemical solvent flowing directly into the urban stormwater tributary.',
            'address': 'West Creek Bridge, Sector 4',
            'latitude': '40.7180',
            'longitude': '-74.0080',
            'photo': photo_data
        }, content_type='multipart/form-data', follow_redirects=True)

        self.assertEqual(report_res.status_code, 200)
        self.assertIn(b'Your environmental report has been successfully submitted', report_res.data)

        # Verify it appears in search
        search_res = self.client.get('/reports?q=chemical')
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b'Illegal industrial chemical dumping', search_res.data)

    def test_05_admin_portal_and_status_update(self):
        """Test admin role restriction, dashboard access, and status updates."""
        # Unauthorized resident should be blocked
        self.client.get('/login?demo=resident', follow_redirects=True)
        blocked_res = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Access restricted', blocked_res.data)

        # Login as Admin
        admin_login = self.client.get('/login?demo=admin', follow_redirects=True)
        self.assertEqual(admin_login.status_code, 200)

        # Access admin dashboard
        admin_res = self.client.get('/admin')
        self.assertEqual(admin_res.status_code, 200)
        self.assertIn(b'Environmental Triage & Operations Dashboard', admin_res.data)

        # Test admin stats API
        stats_res = self.client.get('/api/admin/stats')
        self.assertEqual(stats_res.status_code, 200)
        stats_data = json.loads(stats_res.data)
        self.assertIn('categories', stats_data)
        self.assertIn('statuses', stats_data)
        self.assertIn('timeline', stats_data)

        # Test updating report status to Resolved
        update_res = self.client.post('/admin/update-status/1', data={
            'status': 'Resolved',
            'admin_notes': 'Cleaned by municipal squad. Inspection verified.'
        }, follow_redirects=True)
        self.assertEqual(update_res.status_code, 200)
        self.assertIn(b'status updated to', update_res.data)
        self.assertIn(b'Resolved', update_res.data)

if __name__ == '__main__':
    unittest.main()
