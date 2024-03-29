import os
import unittest
from flask import json
from passlib.apps import custom_app_context as pwd_context
from base64 import b64encode

from config import basedir
from app import app, db
from app.models import User, Glass, Beer, Review

class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'testing.db')
        self.app = app.test_client()
        db.create_all()
        u = User('testunit1', 'unit1@tests.local', 'testing')
        db.session.add(u)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def open_with_auth(self, url, method, data=None):
        return self.app.open(url, method=method, headers={
            'Authorization': 'Basic ' + b64encode('testunit1' + ":" + 'testing'),
            'Content-Type': 'application/json'}, data=data)

    # Try creating a new user
    def test_user_creation(self):
        data = json.dumps({u'username':'testunit2', u'email':'unit2@tests.local',\
                u'password':'testing2'})
        rv = self.open_with_auth('/beer/api/v0.1/users', 'POST', data)
        assert rv.status_code is 201
        u = User.query.filter_by(username='testunit2').first()
        assert u.username == "testunit2"
        assert pwd_context.verify('testing2', u.password)

    # Get user an authentication token
    def test_token_creation(self):
        rv = self.open_with_auth('/beer/api/v0.1/token', 'GET')
        assert rv.status_code is 200

    # Create a new glass_type
    def test_glass_creation(self):
        data = json.dumps({u'name':'Goblet'})
        rv = self.open_with_auth('/beer/api/v0.1/glasses', 'POST', data)
        assert rv.status_code is 201
        g = Glass.query.filter_by(name='Goblet').first()
        assert g.name == 'Goblet'

    # Create a new beer
    def test_beer_creation(self):
        data = json.dumps({u'name':'Spotted Cow', u'brewer':'New Glarus',\
                u'abv':'4.80', u'style':'Cream Ale'})
        rv = self.open_with_auth('/beer/api/v0.1/beers', 'POST', data)
        assert rv.status_code is 201
        b = Beer.query.filter_by(name='Spotted Cow').first()
        assert b.abv == 4.80

    # Test adding glass to beer 
    def test_glass_beer_relationship(self):
        g = Glass('Goblet')
        b = Beer('Fat Tire', 'New Belgium', '4', '20', '4.60', 'Amber Ale', 'USA')
        db.session.add(g)
        db.session.add(b)
        db.session.commit()
        data = json.dumps({u'glass_type':g.id})
        rv = self.open_with_auth('/beer/api/v0.1/beers/'+str(b.id), 'PUT', data)
        g = Glass.query.filter_by(name='Goblet').first()
        rv = self.open_with_auth('/beer/api/v0.1/glasses/'+str(g.id), 'GET')
        assert json.loads(rv.data)['results']['name'] == "Goblet"

    # Create new review and test relationships
    def test_review_creation(self):
        b = Beer('Fat Tire', 'New Belgium', '4', '20', '4.60', 'Amber Ale', 'USA')
        db.session.add(b)
        db.session.commit()
        data = json.dumps({'aroma':4, 'appearance':4, 'taste':4, 'palate':4, \
                'bottle_style':4, 'beer_id':'1'})
        rv = self.open_with_auth('/beer/api/v0.1/reviews', 'POST', data)
        assert rv.status_code == 201
        r = Review.query.get(1)
        assert r.aroma == 4
        b = Beer.query.get(1)
        u = User.query.get(1)
        assert r.beer_id == b.id
        assert r.author_id == u.id

    # Test creating a new list of favorites
    def test_favorites_creation(self):
        b1 = Beer('Fat Tire', 'New Belgium', '4', '20', '4.60', 'Amber Ale', 'USA')
        b2 = Beer('Skinny Tire', 'New Belgium', '4', '20', '4.60', 'Amber Ale', 'USA')
        db.session.add(b1)
        db.session.add(b2)
        db.session.commit()
        data = json.dumps({"beers": ["1", "2"]})
        rv = self.open_with_auth('/beer/api/v0.1/users/1/favorites', 'POST', data)
        assert rv.status_code == 201
        u = User.query.get(1)
        assert u.favorites != []
        rv = self.open_with_auth('/beer/api/v0.1/users/1/favorites', 'DELETE', data)
        assert rv.status_code == 200
        u = User.query.get(1)
        assert u.favorites == []

    # Add and remove a beer from users favorite list
    def test_add_and_remove_favorite(self):
        b = Beer('Fat Tire', 'New Belgium', '4', '20', '4.60', 'Amber Ale', 'USA')
        db.session.add(b)
        db.session.commit()
        rv = self.open_with_auth('/beer/api/v0.1/users/1/favorites', 'PUT',\
                json.dumps({"beer": '1', "action": "add"}))
        assert rv.status_code == 200
        u = User.query.get(1)
        b =  Beer.query.get(1)
        assert u.favorites[0] == b
        rv = self.open_with_auth('/beer/api/v0.1/users/1/favorites', 'PUT',\
                json.dumps({"beer": '1', "action": "remove"}))
        assert rv.status_code == 200
        u = User.query.get(1)
        assert u.favorites == []


if __name__ == '__main__':
    unittest.main()

