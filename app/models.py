from flask import url_for
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from flask.ext.sqlalchemy import SQLAlchemy
from app import db, app

# Model independant id_or_uri_check
def is_model_id_or_uri(session, model, data):
    uri = data.split('/')[-1]
    if data.isdigit():
        x = model.query.get(data)
        if x is not None:
            return int(data)
    elif uri.isdigit():
        x = model.query.get(uri)
        if x is not None:
            return int(uri)
    return None

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

    @classmethod
    def id_or_uri_check(self, data):
        return is_model_id_or_uri(db.session, Glass, data=data)

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
    reviews = db.relationship('Review', backref='beer', lazy='dynamic')

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
        serial = {'name':self.name, 'brewer':self.brewer, 'ibu':self.ibu,\
                'calories':self.calories, 'abv':self.abv, 'style':self.style,\
                'brew_location':self.brew_location,\
                'link': url_for('get_beer', id=self.id, _external=True)}
        if self.glass_type_id:
            serial['glass_type'] = url_for('get_glass',\
                    id=self.glass_type_id, _external=True)
        return serial

    @classmethod
    def id_or_uri_check(self, data):
        return is_model_id_or_uri(db.session, Beer, data=data)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aroma = db.Column(db.Integer)
    appearance = db.Column(db.Integer)
    taste = db.Column(db.Integer)
    palate = db.Column(db.Integer)
    bottle_style = db.Column(db.Integer)
    beer_id = db.Column(db.Integer, db.ForeignKey('beer.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, beer_id, author_id, data):
        self.beer_id = beer_id
        self.author_id = author_id
        if self.validate_score_values(data):
            self.update_score_values(data)

    def __repr__(self):
        return '<Review {}>'.format(self.id)

    def serialize(self):
        return {'author': url_for('get_user', id=self.author_id, _external=True),\
                'beer': url_for('get_beer', id=self.beer_id, _external=True),\
                'link': url_for('get_review', id=self.id, _external=True),\
                'aroma': self.aroma, 'appearance': self.appearance, 'taste': self.taste,\
                'palate': self.palate, 'bottle_style': self.bottle_style}

    def update_score_values(self, data):
        if 'aroma' in data:
            self.aroma = int(data['aroma'])
        if 'appearance' in data:
            self.appearance = int(data['appearance'])
        if 'taste' in data:
            self.taste = int(data['taste'])
        if 'palate' in data:
            self.palate = int(data['palate'])
        if 'bottle_style' in data:
            self.bottle_style = int(data['bottle_style'])

    @classmethod
    def validate_score_values(self, data):
        #TODO: Maybe return a tuple with an error message? (e.g. which was invalid)
        score_max = {'aroma':5, 'appearance':5, 'taste':10, 'palate':5, 'bottle_style':5}
        for category, value in score_max.iteritems():
            try:
                if int(data[category]) < 0 or int(data[category]) > value:
                    return False # score is out of bounds
            except ValueError:
                return False # score is not a valid integer
            except KeyError:
                pass # score missing a category
        return True

    @property
    def overall(self):
        return sum(self.aroma, self.appearance, self.taste, self.palate, self.bottle_style)
