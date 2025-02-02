from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from database import db, migrate
from models import User, Adventure
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)
migrate.init_app(app, db)
auth = HTTPBasicAuth()

with app.app_context():
    db.create_all()


@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Bad request'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email in use'}), 400
    user = User(email=data['email'], password=generate_password_hash(data['password']))
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'OK'}), 201


@auth.verify_password
def verify_password(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not user.verify_password(password):
        return False
    return user


@app.route('/new', methods=['POST'])
@auth.login_required
def create_ads():
    data = request.get_json()
    if not data or 'title' not in data or 'description' not in data:
        return jsonify({'message': 'Bad request'}), 400
    user = auth.current_user()
    new_ads = Adventure(title=data['title'], description=data['description'], owner=user)
    db.session.add(new_ads)
    db.session.commit()
    return jsonify({
        'id': new_ads.id,
        'title': new_ads.title,
        'description': new_ads.description,
        'owner': new_ads.owner.email}), 201


@app.route('/ads', methods=['GET'])
def get_ads():
    ads = Adventure.query.all()
    return jsonify([{
        'id': ad.id,
        'title': ad.title,
        'description': ad.description,
        'owner': ad.owner.email} for ad in ads])


@app.route('/ads/<int:ads_id>', methods=['GET'])
def get_ads_by_id(id):
    ads_id = Adventure.query.get(id)
    if not ads_id:
        return jsonify({'message': 'Not found'}), 404
    return jsonify({
        'id': ads_id.id,
        'title': ads_id.title,
        'description': ads_id.description,
        'owner': ads_id.owner.email})


@app.route('/delete/<int:ads_id>', methods=['DELETE'])
@auth.login_required
def delete_ads(id):
    user = auth.current_user()
    ads = Adventure.query.get(id)
    if not ads:
        return jsonify({'message': 'Not found'}), 404
    if ads.owner != user:
        return jsonify({'message': 'Forbidden'}), 403
    db.session.delete(ads)
    db.session.commit()
    return jsonify({'message': 'OK'})


@app.route('/update/<int:id>', methods=['PUT'])
@auth.login_required
def update_ads(id):
    data = request.get_json()
    user = auth.current_user()
    ads = Adventure.query.get(id)
    if not ads:
        return jsonify({'message': 'Not found'}), 404
    if ads.owner != user:
        return jsonify({'message': 'Forbidden'}), 403
    if 'title' in data:
        ads.title = data['title']
    if 'description' in data:
        ads.description = data['description']
    db.session.add(ads)
    db.session.commit()
    return jsonify({
        'id': ads.id,
        'title': ads.title,
        'description': ads.description,
        'owner': ads.owner.email})
