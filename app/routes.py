from flask import jsonify, request, url_for, abort, flash, get_flashed_messages,\
        g, make_response
from sqlalchemy.exc import OperationalError
from datetime import datetime, timedelta

from app import app, db, auth
from app.models import User, Glass, Beer, Review

@app.route('/beer/api/v0.1/token')
@auth.login_required
def get_auth_token():
    """ Generates an authentication token for current user.
    Pass the token as username with an empty password as an alternate means of authentication.

    |  **URL:** /beer/api/v0.1/token
    |  **Method:** GET
    |  **Query Args:** None
    |  **Authentication:**  Password Only
    
    """
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })

# User model routes
@app.route('/beer/api/v0.1/users', methods = ['GET'])
def list_users():
    """ List all users in the database.

    |  **URL:** /beer/api/v0.1/users
    |  **Method:** GET
    |  **Query Args:** sort_by=<column name> <desc?>
    |  **Authentication:** None

    Examples:

    *Get list of users* ::

      GET http://domain.tld/beer/api/v0.1/users

    *Sorted by creation date* ::

      GET http://domain.tld/beer/api/v0.1/users?sort_by=created_on
    
    *Sorted by username descending* ::

      GET http://domain.tld/beer/api/v0.1/users?sort_by=username%20desc

    """

    sort = request.args.get('sort_by') or None
    if sort:
        try:
            users = User.query.order_by(sort).all()
        except OperationalError:
            flash(u'Invalid sorting value specified', 'error')
            abort(400)
    else:
        users = User.query.all()
    return jsonify(results=[u.serialize() for u in users])

@app.route('/beer/api/v0.1/users/<int:id>', methods = ['GET'])
def get_user(id):
    """ Retrieve information about a particular user.

    |  **URL:** /beer/api/v0.1/users/<user_id>
    |  **Method:** GET
    |  **Query Args:** None
    |  **Authentication:** None

    Example:

    *Get data for user with id# 5*  ::

      GET http://domain.tld/beer/api/v0.1/users/5

    """

    u = User.query.get_or_404(id)
    return jsonify(results=u.serialize())

@app.route('/beer/api/v0.1/users/<int:id>/reviews', methods = ['GET'])
def get_user_reviews(id):
    """ Return list of reviews authored by a particular user.

    |  **URL:** /beer/api/v0.1/users/<user_id>/reviews
    |  **Method:** GET
    |  **Query Args:** sort_by=<column_name> <desc>
    |  **Authentication:** None

    Example:

    *Get reviews for user with id# 2* ::

      GET http://domain.tld/beer/api/v0.1/users/5/reviews

    *Get reviews for user with id# 1 sorted by aroma* ::

      GET http://domain.tld/beer/api/v0.1/users/5/reviews?sort_by=aroma

    """

    u = User.query.get_or_404(id)
    sort = request.args.get('sort_by') or None
    if sort:
        try:
            return jsonify(results=\
                    [r.serialize() for r in u.reviews.order_by(sort)])
        except OperationalError:
            flash(u'Invalid sorting value specified', 'error')
            abort(400)
    return jsonify(results=[r.serialize() for r in u.reviews])

@app.route('/beer/api/v0.1/users', methods = ['POST'])
def create_user():
    """ Creates a new user and saves it to the database.

    |  **URL:** /beer/api/v0.1/users
    |  **Method:** POST
    |  **Query Args:** None
    |  **Authentication:** None
    |  **Expected Data:** username, password
    |  **Optional Data:** email

    Example:

    *Create user 'john' with password 'suchsafety' and email 'john@inter.net'* ::

      POST http://domain.tld/beer/api/v0.1/users
      data={"username":"john", "email":"john@inter.net", "password":"suchsafety"}
    
    """
    username = request.json.get(u'username')
    email = request.json.get(u'email')
    password = request.json.get(u'password')

    if username is None or password is None:
        flash(u'Missing required field (username/password)', 'error')
        abort(400) 
    if User.query.filter_by(username=username).first() is not None:
        flash(u'Username already exists', 'error')
        abort(400)
    user = User(username, email, password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'results': user.serialize(), 'status': 'User created successfully'}),\
            201, {'Location': url_for('get_user', id=user.id, _external=True)}

@app.route('/beer/api/v0.1/users/<int:id>', methods = ['PUT'])
@auth.login_required
def edit_user(id):
    """ Allows editing of a user in the database.

    |  **URL:** /beer/api/v0.1/users/<user_id>
    |  **Method:** PUT
    |  **Query Args:** None
    |  **Authentication:** Token/Password
    |  **Optional Data:** email, username, password

    Example:

    *Edit user with id#1, change email to 'john@newisp.com'* ::

      PUT http://domain.tld/beer/api/v0.1/users/1
      data={"email":"john@newisp.com"}
    
    """
    u = User.query.get_or_404(id)
    if 'username' in request.json and type(request.json['username']) != str:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'email' in request.json and type(request.json['email']) != str:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'password' in request.json and type(request.json['password']) != str:
        flash(u'Invalid input', 'error')
        abort(400)
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    if username is not None:
        if User.query.filter_by(username=username).first() is not None:
            flash(u'User with new username already exists', 'error')
            abort(400)
        u.username = username
    if email is not None:
        if User.query.filter_by(email=email).first() is not None:
            flash(u'User with that email already exists', 'error')
            abort(400)
        u.email = email
    if password is not None:
        u.password = u.hash_password(password)
    db.session.commit()
    return jsonify({'status': 'User updated successfully', 'results': u.serialize()})

@app.route('/beer/api/v0.1/users/<int:id>', methods = ['DELETE'])
@auth.login_required
def delete_user(id):
    """ Delete a user from the database.

    |  **URL:** /beer/api/v0.1/users/<user_id>
    |  **Method:** DELETE 
    |  **Query Args:** None
    |  **Authentication:** Token/Password

    Example:

    *Delete user with id# 4* ::

      DELETE http://domain.tld/beer/api/v0.1/users/4
    
    """
    u = User.query.get_or_404(id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'results': True, 'status': 'User deleted successfully'})



# Glass model routes
@app.route('/beer/api/v0.1/glasses', methods = ['GET'])
def list_glasses():
    """ List glass types in the database.

    |  **URL:** /beer/api/v0.1/glasses
    |  **Method:** GET
    |  **Query Args:** sort_by=<column name> <desc>
    |  **Authentication:** None

    Example:

    *List all glass styles in the database* ::

      GET http://domain.tld/beer/api/v0.1/glasses

    *List glass styles by name descending* ::

      GET http://domain.tld/beer/api/v0.1/glasses?sort_by=name%20desc
    
    """
    sort = request.args.get('sort_by') or None
    if sort:
        try:
            glasses = Glass.query.order_by(sort).all()
        except OperationalError:
            flash(u'Invalid sorting value specified', 'error')
            abort(400)
    else:
        glasses = Glass.query.all()
    return jsonify(results=[g.serialize() for g in glasses])

@app.route('/beer/api/v0.1/glasses/<int:id>', methods = ['GET'])
def get_glass(id):
    """ Get data about a particular glass in the database.

    |  **URL:** /beer/api/v0.1/glasses/<glass_id>
    |  **Method:** GET
    |  **Query Args:** None
    |  **Authentication:** None

    Example:

    *Get data about glass with id# 3* ::

      GET http://domain.tld/beer/api/v0.1/glasses/3

    """
    g = Glass.query.get_or_404(id)
    return jsonify(results=g.serialize())

@app.route('/beer/api/v0.1/glasses', methods = ['POST'])
@auth.login_required
def create_glass():
    """ Add a new glass type to the database.

    |  **URL:** /beer/api/v0.1/glasses
    |  **Method:** POST
    |  **Query Args:** None
    |  **Authentication:** Token/Password
    |  **Expected Data:** name

    Example:

    *Create a glass-type with name 'tumbler'* ::

      POST http://domain.tld/beer/api/v0.1/glasses
      data={"name":"tumbler"}

    """

    name = request.json.get(u'name')
    if name is None:
        flash(u'Missing required field (glass name)', 'error')
        abort(400)
    if Glass.query.filter_by(name=name).first() is not None:
        flash(u'Glass-type already exists', 'error')
        abort(400)
    glass = Glass(name)
    db.session.add(glass)
    db.session.commit()
    return jsonify({'results': glass.serialize(),\
            'status': 'Glass-type created successfully'}), 201,\
            {'Location': url_for('get_glass', id=glass.id, _external=True)}

@app.route('/beer/api/v0.1/glasses/<int:id>', methods = ['PUT'])
@auth.login_required
def edit_glass(id):
    """ Edit the name of a glass-type.

    |  **URL:** /beer/api/v0.1/glasses/<glass_id>
    |  **Method:** PUT
    |  **Query Args:** None
    |  **Authentication:** Token/Password

    Example:

    *Rename glass with id# 2 to 'Goblet'* ::

      PUT http://domain.tld/beer/api/v0.1/glasses/2
      data={"name":"Goblet"}

    """

    g = Glass.query.get_or_404(id)
    if 'name' in request.json and type(request.json['name']) != str:
        flash(u'Invalid input', 'error')
        abort(400)
    name = request.json.get('name')

    if name is not None:
        if Glass.query.filter_by(name=name).first() is not None:
            flash(u'Glass with that name already exists', 'error')
            abort(400)
        g.name = name
    db.session.commit()
    return jsonify({'status': 'Glass-type updated successfully',\
            'results': g.serialize()})

@app.route('/beer/api/v0.1/glasses/<int:id>', methods = ['DELETE'])
@auth.login_required
def delete_glass(id):
    """ Delete a glass-type from the database.

    |  **URL:** /beer/api/v0.1/glasses/<glass_id>
    |  **Method:** DELETE
    |  **Query Args:** None
    |  **Authentication:** Token/Password

    Example:

    *Delete glass-type with id# 5* ::

      DELETE http://domain.tld/beer/api/v0.1/glasses/5

    """

    g = Glass.query.get_or_404(id)
    db.session.delete(g)
    db.session.commit()
    return jsonify({'results': True, 'status': 'Glass deleted successfully'})




# Beer model routes
@app.route('/beer/api/v0.1/beers', methods = ['GET'])
def list_beers():
    """ List all of the beers in the database.

    |  **URL:** /beer/api/v0.1/beers
    |  **Method:** GET
    |  **Query Args:** sort_by=<column_name> <desc>
    |  **Authentication:** None

    Example:

    *List all beers in the system* ::

      GET http://domain.tld/beer/api/v0.1/beers

    *Sort beers by ABV%* ::

      GET http://domain.tld/beer/api/v0.1/beers?sort_by=abv

    *Sort beers by calories descending* ::

      GET http://domain.tld/beer/api/v0.1/beers?sort_by=calories%20desc

    """
    sort = request.args.get('sort_by') or None
    if sort:
        try:
            beers = Beer.query.order_by(sort).all()
        except OperationalError:
            flash(u'Invalid sorting value specified', 'error')
            abort(400)
    else:
        beers = Beer.query.all()
    return jsonify(results=[b.serialize() for b in beers])

@app.route('/beer/api/v0.1/beers/<int:id>', methods = ['GET'])
def get_beer(id):
    """ Get data about a particular beer.

    |  **URL:** /beer/api/v0.1/beers/<beer_id>
    |  **Method:** GET
    |  **Query Args:** None
    |  **Authentication:** None

    Example:

    *Return data about beer with id# 5* ::

      GET http://domain.tld/beer/api/v0.1/beers/5

    """
    b = Beer.query.get_or_404(id)
    return jsonify(results=b.serialize())

@app.route('/beer/api/v0.1/beers/<int:id>/reviews', methods = ['GET'])
def get_beer_reviews(id):
    """ Return list of reviews about a particular beer.

    |  **URL:** /beer/api/v0.1/beers/<beer_id>/reviews
    |  **Method:** GET
    |  **Query Args:** None
    |  **Authentication:** None

    Example:

    *Retrieve list of reviews about beer with id# 2* ::

      GET http://domain.tld/beer/api/v0.1/beers/2/reviews

    *Get reviews of beer with id# 4 sorted by taste descending* ::
      
      GET http://domain.tld/beer/api/v0.1/beers/4/reviews?sort_by=taste desc

    """

    b = Beer.query.get_or_404(id)
    sort = request.args.get('sort_by') or None
    if sort:
        try:
            return jsonify(results=\
                    [r.serialize() for r in  b.reviews.order_by(sort)])
        except OperationalError:
            flash(u'Invalid sorting value specified', 'error')
            abort(400)
    return jsonify(results=[r.serialize() for r in b.reviews])

@app.route('/beer/api/v0.1/beers', methods = ['POST'])
@auth.login_required
# create_beer, now how do I hook this function into my fridge...
def create_beer():
    """ Add a new beer to the database and return the object.

    |  **URL:** /beer/api/v0.1/beers
    |  **Method:** POST
    |  **Query Args:** None
    |  **Authentication:** Token/Password
    |  **Expected Data:** name, style, abv
    |  **Optional Data:** brewer, ibu, calories, brew_location, glass_type

    Example:

    *Create a beer named 'Mayan Chocolate' by 'Mobcraft Beers', style 'Chocolate Chili Ale', abv 6.3%* ::

      POST http://domain.tld/beer/api/v0.1/beers
      data={"name":"Mayan Chocolate", "style":"Chocolate Chili Ale", "brewer":"Mobcraft", "abv":6.4}

    *Create a beer named 'Riverwest Stein' style 'Amber Lager' abv 5.6% linked to glass_type 2* ::

      POST http://domain.tld/beer/api/v0.1/beers
      data={"name":"Riverwest Stein", "glass_type":"http://domain.tld/beer/api/v0.1/glasses/2", "abv":5.6, "style":"Amber lager"}

    *Create a beer named 'African Amber' style 'Amber Ale' abv 4.6% brewer 'Mac & Jacks' linked to glass_type 4* ::

      POST http://domain.tld/beer/api/v0.1/beers
      data={"abv":5.6, "style":"Amber Lager", "glass_type":4, "name":"African Amber"}

    """
    if g.user.last_beer_added and \
            (datetime.utcnow() - g.user.last_beer_added) < timedelta(days=1):
        # Beer already created in last 24 hours
        flash(u'You\'ve already added a beer today.', 'error')
        abort(400)
    name = request.json.get('name')
    brewer = request.json.get('brewer')
    ibu = request.json.get('ibu')
    calories = request.json.get('calories')
    abv = request.json.get('abv')
    style = request.json.get('style')
    brew_location = request.json.get('brew_location')
    glass_type_id = request.json.get('glass_type')

    if name is None or style is None or abv is None:
        flash(u'Missing required field (name, style, abv)', 'error')
        abort(400)
    if Beer.query.filter_by(name=name).first() is not None:
        flash(u'Beer already exists', 'error')
        abort(400)
    beer = Beer(name, brewer, ibu, calories, abv, style, brew_location)
    if glass_type_id is not None:
        gid = Glass.id_or_uri_check(str(glass_type_id))
        if gid is not None:
            beer.glass_type_id = gid

    db.session.add(beer)
    db.session.commit()
    g.user.last_beer_added = datetime.utcnow()
    return jsonify({'results': beer.serialize(), 'status': 'Beer created successfully'}),\
            201, {'Location':url_for('get_beer', id=beer.id, _external=True)}

@app.route('/beer/api/v0.1/beers/<int:id>', methods = ['PUT'])
@auth.login_required
def edit_beer(id):
    """ Edit an existing beer in the database.

    |  **URL:** /beer/api/v0.1/beers/<beer_id>
    |  **Method:** PUT
    |  **Query Args:** None
    |  **Authentication:** Token/Password
    |  **Optional Data:** brewer, ibu, calories, brew_location, glass_type, brewer, style, abv

    Example:

    *Change the abv value of beer with id# 23 to 3.4* ::

      PUT http://domain.tld/beer/api/v0.1/beers/23
      data={"abv":3.4}

    *Change the style and brew_location of beer with id# 6* ::

      PUT http://domain.tld/beer/api/v0.1/beers/6
      data={"style":"Pale Ale", "brew_location":"Milwaukee, WI"}

    """
    b = Beer.query.get_or_404(id)
    if 'name' in request.json and type(request.json['name']) not in [str, int]:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'brewer' in request.json and type(request.json['brewer']) not in [str, int]:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'ibu' in request.json and type(request.json['ibu']) not in [str, int]:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'calories' in request.json and type(request.json['calories']) not in [str, int]:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'abv' in request.json and type(request.json['abv']) not in [str, int, float]:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'style' in request.json and type(request.json['style']) not in [str, int]:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'brew_location' in request.json and type(request.json['brew_location']) not in [str, int]:
        flash(u'Invalid input', 'error')
        abort(400)
    name = request.json.get('name') or b.name
    brewer = request.json.get('brewer')
    ibu = request.json.get('ibu')
    calories = request.json.get('calories')
    abv = request.json.get('abv') or b.abv
    style = request.json.get('style') or b.style
    brew_location = request.json.get('brew_location')
    glass_type_id = request.json.get('glass_type')

    if name is not None and name is not b.name:
        if Beer.query.filter_by(name=name).first() is not None:
            flash(u'Beer with new name already exists', 'error')
            abort(400)
        b.name = name
    if glass_type_id is not None:
        gid = Glass.id_or_uri_check(str(glass_type_id))
        if gid is None:
            flash(u'Invalid glass_type specified', 'error')
            abort(400)
        b.glass_type_id = gid
    if brewer is not None:
        b.brewer = brewer
    if ibu is not None:
        b.ibu = ibu
    if calories is not None:
        b.calories = calories
    if abv is not None:
        b.abv = abv
    if style is not None:
        b.style = style
    if brew_location is not None:
        b.brew_location = brew_location
    db.session.commit()
    return jsonify({'status': 'Beer updated successfully', 'results': b.serialize()})

@app.route('/beer/api/v0.1/beers/<int:id>', methods= ['DELETE'])
@auth.login_required
def delete_beer(id):
    """ Remove a particular beer from the database.

    |  **URL:** /beer/api/v0.1/beers/<beer_id>
    |  **Method:** DELETE
    |  **Query Args:** None
    |  **Authentication:** Token/Password

    Example:

    *Delete the beer with id# 4* ::

      DELETE http://domain.tld/beer/api/v0.1/beers/4

    """
    b = Beer.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    return jsonify({'results':True, 'status': 'Beer deleted successfully'})




# Review model routes
@app.route('/beer/api/v0.1/reviews', methods = ['GET'])
def list_reviews():
    """ Return a list of all reviews in the database.

    |  **URL:** /beer/api/v0.1/reviews
    |  **Method:** GET
    |  **Query Args:** sort_by=<column_name> <desc>
    |  **Authentication:** None

    Examples:

    *List all reviews in the system* ::

      GET http://domain.tld/beer/api/v0.1/reviews

    *List reviews sorted by aroma rating* ::

      GET http://domain.tld/beer/api/v0.1/reviews?sort_by=aroma

    """
    sort = request.args.get('sort_by') or None
    if sort:
        try:
            reviews = Review.query.order_by(sort).all()
        except OperationalError:
            flash(u'Invalid sorting value specified', 'error')
            abort(400)
    else:
        reviews = Review.query.all()
    return jsonify(results=[r.serialize() for r in reviews])

@app.route('/beer/api/v0.1/reviews/<int:id>', methods = ['GET'])
def get_review(id):
    """ Return data about a specific review.

    |  **URL:** /beer/api/v0.1/reviews/<review_id>
    |  **Method:** GET
    |  **Query Args:** None
    |  **Authentication:** None

    Example:

    *Get data about review with id# 5* ::

      GET http://domain.tld/beer/api/v0.1/reviews/5

    """
    r = Review.query.get_or_404(id)
    return jsonify(results=r.serialize())

@app.route('/beer/api/v0.1/reviews', methods = ['POST'])
@auth.login_required
def create_review():
    """ Post a new review to the database. Return the review object.

    |  **URL:** /beer/api/v0.1/reviews
    |  **Method:** POST
    |  **Query Args:** None
    |  **Authentication:** Token/Password
    |  **Expected Data:** beer_id, aroma, appearance, taste, palate, bottle_style

    Example:

    *Review beer with id# 4 with scores, 3, 3, 8, 4, 1* ::

      POST http://domain.tld/beer/api/v0.1/reviews
      data={"beer_id":4, "aroma":3, "appearance":3, "taste":8, "palate":4, "bottle_style":1}

    *Review beer with id# 2 with scores, 1, 1, 5, 5, 5* ::

      POST http://domain.tld/beer/api/v0.1/reviews
      data={"aroma":"1", "appearance":"1", "taste":"5", "palate":"5", "bottle_style":"5", "beer_id":"http://domain.tld/beer/api/v0.1/beers/2"}

    """

    score = dict()
    score['aroma'] = request.json.get(u'aroma')
    score['appearance'] = request.json.get(u'appearance')
    score['taste'] = request.json.get(u'taste')
    score['palate'] = request.json.get(u'palate')
    score['bottle_style'] = request.json.get(u'bottle_style')
    score['beer_id'] = request.json.get(u'beer_id')

    for key, value in score.items():
        if value == None:
            flash(u'Missing value for '+key, 'error')
            abort(400)
        if key == 'beer_id':
            bid = Beer.id_or_uri_check(str(value))
            if bid is None:
                flash(u'That beer does not exist, please create it first', 'error')
                abort(400)
            # Has user reviewed that beer this week?
            for review in g.user.reviews:
                if review.beer_id == bid:
                    if (datetime.utcnow() - review.created_on) < timedelta(weeks=1):
                        flash(u'You have already reviewed that beer this week!', 'error')
                        abort(400)
    if not Review.validate_score_values(score):
        flash(u'Invalid score data, please try again', 'error')
        abort(400)
    review = Review(bid, g.user.id, score)
    db.session.add(review)
    db.session.commit()
    return(jsonify({'results': review.serialize(), \
            'status': 'Review created successfully'}), 201, \
            {'Location': url_for('get_review', id=review.id, _external=True)})

@app.route('/beer/api/v0.1/reviews/<int:id>', methods = ['PUT'])
@auth.login_required
def edit_review(id):
    """ Edit an existing review.

    |  **URL:** /beer/api/v0.1/reviews/<review_id>
    |  **Method:** PUT 
    |  **Query Args:** None
    |  **Authentication:** Token/Password
    |  **Optional Data:** aroma, appearance, taste, palate, bottle_style

    Example:

    *Change the aroma score to '5' on review with id# 3* ::

      PUT http://domain.tld/beer/api/v0.1/reviews/3
      data={"aroma":5}

    *Change the scores of review with id# 1* ::

      PUT http://domain.tld/beer/api/v0.1/reviews/1
      data={"aroma":"5", "appearance":"1", "taste":"3", "palate":"3", "bottle_style":"2"}

    """
    r = Review.query.get_or_404(id)
    data = dict()
    for key, value in request.json.items():
        data[key] = value
    if not r.validate_score_values(data):
        flash(u'Unable to validate new scores', 'error')
        abort(400)
    r.update_score_values(data)
    db.session.commit()
    return(jsonify({'results': r.serialize(), 'status': 'Review updated successfully'}))

@app.route('/beer/api/v0.1/reviews/<int:id>', methods = ['DELETE'])
@auth.login_required
def delete_review(id):
    """ Delete a review from the database.

    |  **URL:** /beer/api/v0.1/reviews/<review_id>
    |  **Method:** DELETE
    |  **Query Args:** None
    |  **Authentication:** Token/Password

    Example:

    *Delete the review with id# 3* ::

      DELETE http://domain.tld/beer/api/v0.1/reviews/3

    """
    r = Review.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'results': True, 'status': 'Review deleted successfully'})

# Favorites list routes
@app.route('/beer/api/v0.1/users/<int:id>/favorites', methods = ['GET'])
def get_user_favorites(id):
    """ Return a list of users favorite beers.

    |  **URL:** /beer/api/v0.1/users/<user_id>/favorites
    |  **Method:** GET
    |  **Query Args:** None
    |  **Authentication:** None

    Example:

    *Retrieve a list of favorites for user with id# 12* ::

      GET http://domain.tld/beer/api/v0.1/users/12/favorites

    """

    u = User.query.get_or_404(id)
    return jsonify(results=[b.serialize() for b in u.favorites])

@app.route('/beer/api/v0.1/users/<int:id>/favorites', methods = ['POST'])
@auth.login_required
def create_user_favorites_list(id):
    """ Create a fresh list of favorite beers for a user.

    |  **URL:** /beer/api/v0.1/users/<user_id>/favorites
    |  **Method:** POST
    |  **Query Args:** None
    |  **Authentication:** None
    |  **Expected Data:** beers (list of id's)

    Example:

    *Create favorites list including beers with id#'s 2, 6, 3, 19 for user with id# 5* ::

      POST http://domain.tld/beer/api/v0.1/users/5/favorites
      data={"beers":["2", 6, 3, "http://domain.tld/beer/api/v0.1/beers/19"]}

    """
    u = User.query.get_or_404(id)
    if u.favorites != []:
        flash(u'User already has a favorites list, delete it first', 'error')
        abort(400)
    if not "beers" in request.json:
        flash(u'Invalid input, expecting \'beers\' list.')
        abort(400)
    for beer in request.json['beers']:
        if not Beer.id_or_uri_check(beer):
            flash(u'Invalid beer ID/URL specified', 'error')
            abort(400)
        b = Beer.query.get(beer)
        u.add_to_favorites(b)
        db.session.commit()
    return jsonify({"results": [b.serialize() for b in u.favorites],\
            'status': 'Favorites list created with ' + str(len(u.favorites))\
            + ' beers'}), 201

@app.route('/beer/api/v0.1/users/<int:id>/favorites', methods = ['PUT'])
@auth.login_required
def edit_user_favorites(id):
    """ Add or remove a particular beer from a users favorites list.

    |  **URL:** /beer/api/v0.1/users/<user_id>/favorites
    |  **Method:** PUT
    |  **Query Args:** None
    |  **Authentication:** Token/Password
    |  **Expected Data:** beer, action

    Example:

    *Add beer with id# 8 to user with id# 3* ::

      POST http://domain.tld/beer/api/v0.1/users/3/favorites
      data={"beer":8, "action":"add"}

    *Remove beer with id# 2 from user with id# 3* ::

      POST http://domain.tld/beer/api/v0.1/users/3/favorites
      data={"beer":"http://www.domain.tld/beer/api/v0.1/beers/2", "action":"remove"}

    *Add a beer with id# 71 to user with id# 12* ::

      POST http://domain.tld/beer/api/v0.1/users/12/favorites
      data={"beer":71, "action":"add"}

    """

    actions = ['add', 'remove']
    u = User.query.get_or_404(id)
    action = request.json.get('action')
    beer_id = request.json.get('beer')
    beer = Beer.id_or_uri_check(beer_id)
    if not action in actions:
        flash(u'Invalid action specified (try add/remove)', 'error')
        abort(400)
    if not beer:
        flash(u'That beer doesn\'t exist, create it first!', 'error')
        abort(400)
    beer = Beer.query.get(beer)
    exists = (True if beer in u.favorites else False)
    if action == 'add':
        if exists:
            flash(u'Beer already on the favorite list', 'error')
            abort(400)
        u.add_to_favorites(beer)
    if action == 'remove':
        if not exists:
            flash(u'Beer wasn\'t on the favorite list anyway', 'error')
            abort(400)
        u.remove_from_favorites(beer)
    db.session.commit()
    return jsonify({'results': [b.serialize() for b in u.favorites],\
            'status': ''+beer.name+' '+('added to' if action == 'add'\
            else 'removed from')+' favorites'})

@app.route('/beer/api/v0.1/users/<int:id>/favorites', methods = ['DELETE'])
@auth.login_required
def delete_users_favorites_list(id):
    """ Delete a users entire favorites list.

    |  **URL:** /beer/api/v0.1/users/<user_id>/favorites
    |  **Method:** DELETE
    |  **Query Args:** None
    |  **Authentication:** Token/Password

    Example:

    *Delete favorites list for user with id# 4* ::

      DELETE http://domain.tld/beer/api/v0.1/users/4/favorites

    """
    u = User.query.get_or_404(id)
    if u.favorites == []:
        return jsonify({'results': False, 'status': 'Favorites list was already empty'})
    u.favorites = []
    db.session.commit()
    return jsonify({'results': True, 'status': 'Favorites list deleted successfully'})

@app.route('/beer/api/v0.1/favorites', methods = ['GET'])
@auth.login_required
def list_all_user_favorites():
    """ List favorites list for each user in database.

    |  **URL:** /beer/api/v0.1/favorites
    |  **METHOD:** GET
    |  **Query Args:** None
    |  **Authentication:** Token/Password

    Example:

    *Get all favorites-list in system* ::

      GET http://domain.tld/beer/api/v0.1/favorites

    """

    users = User.query.all()
    return jsonify({'results': \
            [{u.username: [b.serialize() for b in u.favorites]} for u in users]})


    

'''
*** Authentication
'''
@auth.verify_password
def verify_password(username, password):
    """ Returns true if hash of plaintext 'password' equals stored password hash for user. """

    user = User.check_auth_token(username)
    if not user:
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return False
    g.user = user
    return True

@app.before_request
def before_request():
    """ Checks for *Content-Type: application/json* on all POST/PUT/DELETE routes. """
    if request.method != "GET" and request.json == None:
        flash(u'Invalid request, expecting JSON')
        abort(400)

@app.after_request
def after_request(response):
    """ Update a users last_activity field after each authenticated api request. """

    if 'user' in g:
        g.user.last_activity = datetime.utcnow()
        db.session.commit()
    return response



'''
*** Error Handling
'''
@app.errorhandler(400)
def malformed_error(error):
    """ Returns a 400 error when recieving a malformed request. Adds any messages that have been flash()'ed. """

    messages = get_flashed_messages(with_categories=True)
    if messages:
        errors = dict() 
        for category, message in messages:
            #TODO: Could be cleaner, multiple messages would overwrite
            errors[category] = message
        return jsonify(errors), 400
    return jsonify({"error": "400: Malformed request"}), 400

@app.errorhandler(404)
def not_found_error(error):
    """ Return a 404 error, usually when <int:id> in the route is not a valid id# for that model. """

    return jsonify({"error": "404: Not Found"}), 404

@app.errorhandler(405)
def method_unallowed_error(error):
    """ Return a 405 error when an unsupported HTTP method is used on an endpoint. """ 

    return jsonify({"error": "405: Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    """ Return a 500 error when something goes terribly wrong. """

    db.session.rollback()
    return jsonify({"error": "500: The application is drunk"}), 500

@auth.error_handler
def unauthorized_error():
    """ Returns a 403 error when attempting to access data without authorization. """

    return make_response(jsonify({"error": "Unauthorized access"}), 403)
