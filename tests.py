import os
import unittest
from passlib.apps import custom_app_context as pwd_context

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

    # User model test methods
    def test_user_creation(self):
        u = User('testunit1', 'unit1@tests.local', 'testing')
        db.session.add(u)
        db.session.commit()
        u2 = User.query.filter_by(username='testunit1').first()
        assert u.id == u2.id
        assert pwd_context.verify('testing', u2.password)


if __name__ == '__main__':
    unittest.main()

