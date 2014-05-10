from datetime import datetime
from passlib.apps import custom_app_context as pwd_context
from flask.ext.sqlalchemy import SQLAlchemy
from app import db, app

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True)
    email = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(128))
    created_on = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    is_public = db.Column(db.Boolean)
    reviews = db.relationship('Review', backref='author', lazy='dynamic')

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.hash_password(password)
        self.created_on = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_public = True

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def serialize(self):
        return {'username':self.username, 'email':self.email, \
                'created-on':self.created_on, 'last_activity':self.last_activity}

    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    def check_password(self, password):
        return pwd_context.verify(password, self.password)

class Glass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    beers = db.relationship('Beer', backref='glass_type', lazy='dynamic')

    def __init__(self, name):
        self.name = name

class Beer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    brewer = db.Column(db.String(200)) #TODO: Implement Brewery object
    ibu = db.Column(db.Integer)
    calories = db.Column(db.Integer)
    abv = db.Column(db.Float)
    style = db.Column(db.String(200))
    brew_location = db.Column(db.String)
    glass_type_id = db.Column(db.Integer, db.ForeignKey('glass.id'))

    def __init__(self):
        self.ibu = 0
        self.calories = 0
        self.abv = 0

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aroma = db.Column(db.Integer)
    appearance = db.Column(db.Integer)
    taste = db.Column(db.Integer)
    palate = db.Column(db.Integer)
    bottle_style = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, aroma=0, appearance=0, taste=0, palate=0, bottle_style=0):
        self.aroma = aroma
        self.appearance = appearance
        self.taste = taste
        self.palate = palate
        self.bottle_style = bottle_style

    @property
    def overall(self):
        return sum(self.aroma, self.appearance, self.taste, self.palate, self.bottle_style)
