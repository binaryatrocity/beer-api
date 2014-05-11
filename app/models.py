from flask import url_for
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from flask.ext.sqlalchemy import SQLAlchemy
from app import db, app

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True)
    email = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(128))
    created_on = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    reviews = db.relationship('Review', backref='author', lazy='dynamic')

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.hash_password(password)
        self.created_on = datetime.utcnow()
        self.last_activity = datetime.utcnow()

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def serialize(self):
        return {'username':self.username, 'email':self.email, \
                'link':url_for('edit_user', id=self.id, _external=True), \
                'created-on':self.created_on, 'last_activity':self.last_activity}

    def generate_auth_token(self, expiration=1200):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def check_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        user = User.query.get(data['id'])
        return user

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

    def __repr__(self):
        return '<Glass {}>'.format(self.name)

    def serialize(self):
        return {'name':self.name, 'link':url_for('get_glass', id=self.id, _external=True),\
                'beers':[b.serialize() for b in self.beers.all()]}

    @staticmethod
    def id_or_uri_check(data):
        uri = data.split('/')[-1]
        if data.isdigit():
            g = Glass.query.get(data)
            if g is not None:
                return int(data)
        elif uri.isdigit():
            g = Glass.query.get(uri)
            if g is not None:
                return int(uri)
        return None

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

    def __init__(self, name, brewer, ibu, calories, abv, style, brew_location):
        self.name = name
        self.brewer = brewer
        self.ibu = ibu
        self.calories = calories 
        self.abv = abv 
        self.style = style
        self.brew_location = brew_location

    def __repr__(self):
        return '<Beer {}>'.format(self.name)

    def serialize(self):
        return {'name':self.name, 'brewer':self.brewer, 'ibu':self.ibu,\
                'calories':self.calories, 'abv':self.abv, 'style':self.style,\
                'brew_location':self.brew_location, \
                'link': url_for('get_beer', id=self.id, _external=True)}

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
