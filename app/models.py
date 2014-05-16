from flask import url_for
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from flask.ext.sqlalchemy import SQLAlchemy
from app import db, app

# Model independant id_or_uri_check
def is_model_id_or_uri(session, model, data):
    """Return a valid model.primary_key or None.

    Keyword arguments:

    |  **session** -- the SQLAlchemy session
    |  **model**   -- the db.Model class to lookup
    |  **data**    -- the data to parse (expecting an int(id) or an api link

    If data is a digit, lookup that primary_key for model, otherwise try to parse
    the last chunk from an api 'link' uri.

    """
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

# Favorites list relationship table
favorite = db.Table('favorites',
        db.Column('beer_id', db.Integer, db.ForeignKey('beer.id')),
        db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
        )

class User(db.Model):
    """ Database model representing a single User.

    Properties:

    |  **username** -- the users name/nickname.
    |  **email**    -- the users email address (unused).
    |  **password** -- the users password hash.
    |  **created_on** -- datetime from moment of creation.
    |  **last_activity** -- datetime from last authenticated api call.
    |  **last_beer_added** -- datetime from last added beer (for 24 hour limit).
    |  **reviews** -- reviews writen by the User.
    |  **favorites** -- list of User's favorite beers.

    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True)
    email = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(128))
    created_on = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    last_beer_added = db.Column(db.DateTime)
    reviews = db.relationship('Review', backref='author', lazy='dynamic')
    favorites = db.relationship('Beer', secondary=favorite, \
            backref=db.backref('favorites', lazy='dynamic'))

    def __init__(self, username, email, password):
        """ Creates a new User object.  """

        self.username = username
        self.email = email
        self.hash_password(password)
        self.created_on = datetime.utcnow()
        self.last_activity = datetime.utcnow()

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def serialize(self):
        """ Return a JSON representation of a User object.  """
        return {'username':self.username, 'email':self.email, \
                'link':url_for('edit_user', id=self.id, _external=True), \
                'created_on':self.created_on, 'last_activity':self.last_activity}

    def add_to_favorites(self, beer):
        """ Add a beer to users favorites list, checks for redundancy. """
        if beer not in self.favorites:
            self.favorites.append(beer)
            return True
        return False

    def remove_from_favorites(self, beer):
        """ Remove a beer from users favorites list. """
        if beer in self.favorites:
            self.favorites.remove(beer)
            return True
        return False

    @staticmethod
    def check_auth_token(token):
        """ Validates a user's authentication token, checks for expiration. """
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        user = User.query.get(data['id'])
        return user

    def generate_auth_token(self, expiration=1200):
        """ Generates a new authentication token for a user. """
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    def hash_password(self, password):
        """ Creates a password hash from the plaintext. """
        self.password = pwd_context.encrypt(password)

    def check_password(self, password):
        """ Confirms/validates a plaintext password against the users stored hash """
        return pwd_context.verify(password, self.password)

class Glass(db.Model):
    """ Database model representing a style of beer Glass.

    Properties:

    |  **name** -- The name of the glass-style (e.g. 'Tumbler')
    |  **beers** -- List of beers that should be served in said glass-type

    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    beers = db.relationship('Beer', backref='glass_type', lazy='dynamic')

    def __init__(self, name):
        """ Creates a new Glass-type, required a name string. """
        self.name = name

    def __repr__(self):
        return '<Glass {}>'.format(self.name)

    def serialize(self):
        """ Return a JSON representation of a Glass object.  """
        return {'name':self.name, 'link':url_for('get_glass', id=self.id, _external=True),\
                'beers':[b.serialize() for b in self.beers.all()]}

    @classmethod
    def id_or_uri_check(self, data):
        """ Returns a valid primary_key parsed from 'data', or None. """
        return is_model_id_or_uri(db.session, Glass, data=data)

class Beer(db.Model):
    """ Database model representing an individual Beer.  """

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
        """ Creates a new Beer object. """
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
        """ Return a JSON representation of a Beer object.  """
        serial = {'name':self.name, 'brewer':self.brewer, 'ibu':self.ibu,\
                'calories':self.calories, 'abv':self.abv, 'style':self.style,\
                'brew_location':self.brew_location,\
                'average_scores':self.average_scores,\
                'link': url_for('get_beer', id=self.id, _external=True)}
        if self.glass_type_id:
            serial['glass_type'] = url_for('get_glass',\
                    id=self.glass_type_id, _external=True)
        return serial

    @classmethod
    def id_or_uri_check(self, data):
        """ Returns a valid primary_key parsed from 'data', or None. """
        return is_model_id_or_uri(db.session, Beer, data=data)

    @property
    def average_scores(self):
        """ Finds other reviews for the same beer_id, and returns the average of their scores. """
        totals = {'aroma':0, 'appearance':0, 'taste':0, 'palate':0, 'bottle_style':0}
        for r in self.reviews.all():
            totals['aroma'] += r.aroma
            totals['appearance'] += r.appearance
            totals['taste'] += r.taste
            totals['palate'] += r.palate
            totals['bottle_style'] += r.bottle_style
        for key,value in totals.iteritems():
            totals[key] = value / len(self.reviews.all())
        return totals

class Review(db.Model):
    """ Database model representing a beer Review.

    Properties:

    |  **aroma**  -- Score category, 1-5
    |  **appearance** -- Score category, 1-5
    |  **taste** -- Score category, 1-10
    |  **palate** -- Score category, 1-5
    |  **bottle_style** -- Score category, 1-5

    """

    id = db.Column(db.Integer, primary_key=True)
    aroma = db.Column(db.Integer)
    appearance = db.Column(db.Integer)
    taste = db.Column(db.Integer)
    palate = db.Column(db.Integer)
    bottle_style = db.Column(db.Integer)
    created_on = db.Column(db.DateTime)
    beer_id = db.Column(db.Integer, db.ForeignKey('beer.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, beer_id, author_id, data):
        """ Create a new Review. """
        self.beer_id = beer_id
        self.author_id = author_id
        self.created_on = datetime.utcnow()
        if self.validate_score_values(data):
            self.update_score_values(data)

    def __repr__(self):
        return '<Review {}>'.format(self.id)

    def serialize(self):
        """ Return a JSON representation of a Review object.  """
        return {'author': url_for('get_user', id=self.author_id, _external=True),\
                'beer': url_for('get_beer', id=self.beer_id, _external=True),\
                'link': url_for('get_review', id=self.id, _external=True),\
                'aroma': self.aroma, 'appearance': self.appearance, 'taste': self.taste,\
                'palate': self.palate, 'bottle_style': self.bottle_style,\
                'overall':self.overall}

    def update_score_values(self, data):
        """ Updates a Review's scores based on a passed in dictionary. """
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
        """ Checks that a score-dictionary's values are within review-category constraints.  """
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
        """ Returns the sum of all the Reviews categories. """
        return self.aroma + self.appearance + self.taste + self.palate +\
                self.bottle_style

