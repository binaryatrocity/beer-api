from flask import jsonify, request, url_for, abort, flash, get_flashed_messages,\
        g, make_response
from sqlalchemy.exc import OperationalError
from datetime import datetime, timedelta

from app import app, db, auth
from models import User, Glass, Beer, Review

# FOR DEBUG DELETE
@app.route('/beer')
@auth.login_required
def show_index():
    return "testing"

# Generate an authentication token for future requests
@app.route('/beer/api/v0.1/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })


'''
*** Data resources
'''
# User model routes
@app.route('/beer/api/v0.1/users', methods = ['GET'])
def list_users():
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
    u = User.query.get_or_404(id)
    return jsonify(results=u.serialize())

@app.route('/beer/api/v0.1/users/<int:id>/reviews', methods = ['GET'])
def get_user_reviews(id):
    u = User.query.get_or_404(id)
    return jsonify(results=[r.serialize() for r in u.reviews])

@app.route('/beer/api/v0.1/users', methods = ['POST'])
def create_user():
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
    u = User.query.get_or_404(id)
    if 'username' in request.json and type(request.json['username']) != unicode:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'email' in request.json and type(request.json['email']) != unicode:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'password' in request.json and type(request.json['password']) != unicode:
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
    u = User.query.get_or_404(id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'results': True, 'status': 'User deleted successfully'})

# Glass model routes
@app.route('/beer/api/v0.1/glasses', methods = ['GET'])
def list_glasses():
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
    g = Glass.query.get_or_404(id)
    return jsonify(results=g.serialize())

@app.route('/beer/api/v0.1/glasses', methods = ['POST'])
@auth.login_required
def create_glass():
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
    g = Glass.query.get_or_404(id)
    if 'name' in request.json and type(request.json['name']) != unicode:
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
    g = Glass.query.get_or_404(id)
    db.session.delete(g)
    db.session.commit()
    return jsonify({'results': True, 'status': 'Glass deleted successfully'})


# Beer model routes
@app.route('/beer/api/v0.1/beers', methods = ['GET'])
def list_beers():
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
    b = Beer.query.get_or_404(id)
    return jsonify(results=b.serialize())

@app.route('/beer/api/v0.1/beers/<int:id>/reviews', methods = ['GET'])
def get_beer_reviews(id):
    b = Beer.query.get_or_404(id)
    return jsonify(results=[r.serialize() for r in b.reviews])

@app.route('/beer/api/v0.1/beers', methods = ['POST'])
@auth.login_required
# create_beer, now how do I hook this function into my fridge...
def create_beer():
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
    b = Beer.query.get_or_404(id)
    if 'name' in request.json and type(request.json['name']) != unicode:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'brewer' in request.json and type(request.json['brewer']) != unicode:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'ibu' in request.json and type(request.json['ibu']) != unicode:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'calories' in request.json and type(request.json['calories']) != unicode:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'abv' in request.json and type(request.json['abv']) != unicode:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'style' in request.json and type(request.json['style']) != unicode:
        flash(u'Invalid input', 'error')
        abort(400)
    if 'brew_location' in request.json and type(request.json['brew_location']) != unicode:
        flash(u'Invalid input', 'error')
        abort(400)
    name = request.json.get('name') or b.name
    brewer = request.json.get('brewer')
    ibu = request.json.get('ibu')
    calories = request.json.get('calories')
    abv = request.json.get('ibu') or b.abv
    style = request.json.get('style') or b.style
    brew_location = request.json.get('ibu')
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
    b = Beer.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    return jsonify({'results':True, 'status': 'Beer deleted successfully'})


# Review model routes
@app.route('/beer/api/v0.1/reviews', methods = ['GET'])
def list_reviews():
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
    r = Review.query.get_or_404(id)
    return jsonify(results=r.serialize())

@app.route('/beer/api/v0.1/reviews', methods = ['POST'])
@auth.login_required
def create_review():
    score = dict()
    score['aroma'] = request.json.get(u'aroma')
    score['appearance'] = request.json.get(u'appearance')
    score['taste'] = request.json.get(u'taste')
    score['palate'] = request.json.get(u'palate')
    score['bottle_style'] = request.json.get(u'bottle_style')
    score['beer_id'] = request.json.get(u'beer_id')

    for key, value in score.iteritems():
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
    r = Review.query.get_or_404(id)
    data = dict()
    for key, value in request.json.iteritems():
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
    r = Review.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'results': True, 'status': 'Review deleted successfully'})

# Favorites list routes
@app.route('/beer/api/v0.1/users/<int:id>/favorites', methods = ['GET'])
def get_user_favorites(id):
    u = User.query.get_or_404(id)
    return jsonify(results=[b.serialize() for b in u.favorites])

@app.route('/beer/api/v0.1/users/<int:id>/favorites', methods = ['POST'])
def create_user_favorites_list(id):
    u = User.query.get_or_404(id)
    if u.favorites != []:
        flash(u'User already has a favorites list, delete it first', 'error')
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
def add_to_user_favorites(id):
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
    u = User.query.get_or_404(id)
    if u.favorites == []:
        return jsonify({'results': False, 'status': 'Favorites list was already empty'})
    u.favorites = []
    db.session.commit()
    return jsonify({'results': True, 'status': 'Favorites list deleted successfully'})

@app.route('/beer/api/v0.1/favorites', methods = ['GET'])
@auth.login_required
def list_all_user_favorites():
    users = User.query.all()
    return jsonify({'results': \
            [{u.username: [b.serialize() for b in u.favorites]} for u in users]})


    

'''
*** Authentication
'''
@auth.verify_password
def verify_password(username, password):
    user = User.check_auth_token(username)
    if not user:
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return False
    g.user = user
    return True


@app.after_request
def after_request(response):
    if 'user' in g:
        # Update users last_activity after each authenticated request
        g.user.last_activity = datetime.utcnow()
        db.session.commit()
    return response



'''
*** Error Handling
'''
@app.errorhandler(400)
def malformed_error(error):
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
    return jsonify({"error": "404: Not Found"}), 404

@app.errorhandler(405)
def method_unallowed_error(error):
    return jsonify({"error": "405: Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "500: The application is drunk"}), 500

@auth.error_handler
def unauthorized_error():
    return make_response(jsonify({"error": "Unauthorized access"}), 403)
