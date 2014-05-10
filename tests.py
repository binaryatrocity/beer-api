import os
import unittest
from flask import json
from passlib.apps import custom_app_context as pwd_context
from base64 import b64encode

from config import basedir
from app import app, db
from app.models import User

class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'testing.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def open_with_auth(self, url, method, username, password):
        return self.app.open(url, method=method, headers={
            'Authorization': 'Basic ' + b64encode(username + ":" + password),
            'Content-Type': 'application/json'})

    # Try creating a new user
    def test_user_creation(self):
        data = json.dumps({u'username':'testunit1', u'email':'unit1@tests.local',\
                u'password':'testing'})
        rv = self.app.post('/beer/api/v0.1/users',\
                data=data, content_type='application/json') 
        print rv.status_code
        assert rv.status_code is 201

        u = User.query.filter_by(username='testunit1').first()
        assert u.username == "testunit1"
        assert pwd_context.verify('testing', u.password)

    # Get user an authentication token
    def test_token_creation(self):
        u = User('testunit1', 'unit1@tests.local', 'testing')
        db.session.add(u)
        db.session.commit()
        rv = self.open_with_auth('/beer/api/v0.1/token', 'GET', 'testunit1', 'testing')
        assert rv.status_code is 200


if __name__ == '__main__':
    unittest.main()

