from flask import jsonify, request, url_for, abort, flash, get_flashed_messages, g

from app import app, db, auth
from models import User

'''
*** Data resources
'''
# User model routes
@app.route('/beer/api/v0.1/users', methods = ['GET'])
def list_users():
    users = User.query.all()
    return jsonify(results=[u.serialize() for u in users])

@app.route('/beer/api/v0.1/users', methods = ['POST'])
def create_user():
    username = request.json.get(u'username')
    email = request.json.get(u'email')
    password = request.json.get(u'password')

    print request.json.get(u'username')
    if username is None or password is None:
        flash(u'Missing required field (username/password)', 'error')
        abort(400) #TODO: handle this better
    if User.query.filter_by(username=username).first() is not None:
        flash(u'Username already exists', 'error')
        abort(400) #TODO: handle this better
    user = User(username, email, password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'username': user.username, 'message': 'User created successfully'}), 201, {'Location': url_for('get_user', id=user.id, __external=True)}

@app.route('/beer/api/v0.1/users/<int:id>', methods = ['GET'])
@auth.login_required
def get_user(id):
    u = User.query.get_or_404(id)
    return jsonify({"username":u.username, "hash":u.password})



'''
*** Authentication
'''
@auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return False
    g.user = user
    return True



'''
*** Error Handling
'''
# 400 Error Handling
@app.errorhandler(400)
def malformed_error(error):
    messages = get_flashed_messages(with_categories=True)
    print messages
    if messages:
        errors = dict() 
        for category, message in messages:
            #TODO: Could be cleaner, multiple messages would overwrite
            errors[category] = message
        return jsonify(errors), 400
    return jsonify({"message": "400: Malformed request"}), 400

# 404 Error Handling
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "404: Not Found"}), 404

# 500 Error Handling
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "500: The application is drunk"}), 500
