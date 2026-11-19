"""Local browser access works without pairing while retaining request guards."""
import unittest
from unittest.mock import patch
from starlette.testclient import TestClient
from app.main import app
from app.settings import settings


class BrowserAccessTests(unittest.TestCase):
    def test_fresh_browser_bootstraps_csrf_without_login(self):
        with patch('app.main.SessionLocal'), patch.object(settings, 'agentboard_origin', 'http://127.0.0.1:8080'), TestClient(app, base_url='http://127.0.0.1:8080') as client:
            bootstrap = client.get('/api/v1/session')
            self.assertEqual(bootstrap.status_code, 200)
            csrf = bootstrap.json()['csrf_token']
            path = '/api/v1/nonexistent'
            denied = client.post(path, headers={'Origin': 'http://127.0.0.1:8080'}, json={})
            self.assertEqual(denied.status_code, 403)
            allowed = client.post(path, headers={'Origin': 'http://127.0.0.1:8080', 'X-CSRF-Token': csrf}, json={})
            self.assertEqual(allowed.status_code, 404)
            foreign = client.post(path, headers={'Origin': 'https://example.com', 'X-CSRF-Token': csrf}, json={})
            self.assertEqual(foreign.status_code, 403)


    def test_bodyless_delete_passes_guards_but_non_json_bodies_are_rejected(self):
        with patch('app.main.SessionLocal'), patch.object(settings, 'agentboard_origin', 'http://127.0.0.1:8080'), TestClient(app, base_url='http://127.0.0.1:8080') as client:
            token = client.get('/api/v1/session').json()['csrf_token']
            headers = {'Origin': 'http://127.0.0.1:8080', 'X-CSRF-Token': token}
            response = client.delete('/api/v1/nonexistent', headers=headers)
            self.assertEqual(response.status_code, 404)
            invalid = client.post('/api/v1/nonexistent', headers={**headers, 'Content-Type': 'text/plain'}, content='not json')
            self.assertEqual(invalid.status_code, 415)
