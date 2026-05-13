import unittest

from app import app


class FlaskAppTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        return super().setUp()
    
    def test_index_endpoint(self):
        response = self.app.get('/')

        
        self.assertEqual(response.status_code, 200)
        self.assertIn(str("<!DOCTYPE html>"), response.text)


if __name__ == '__main__':
    unittest.main()