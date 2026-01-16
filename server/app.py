#!/usr/bin/env python3

from models import db, Activity, Camper, Signup
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask import Flask, make_response, jsonify, request
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)


@app.route('/')
def home():
    return ''

# GET /campers
@app.route('/campers', methods=['GET'])
def get_campers():
    campers = Camper.query.all()
    return jsonify([camper.to_dict(rules=('-signups',)) for camper in campers]), 200

# GET /campers/<int:id>
@app.route('/campers/<int:id>', methods=['GET'])
def get_camper(id):
    camper = db.session.get(Camper, id)
    if not camper:
        return jsonify({"error": "Camper not found"}), 404
    
    return jsonify(camper.to_dict()), 200

# PATCH /campers/<int:id>
@app.route('/campers/<int:id>', methods=['PATCH'])
def update_camper(id):
    camper = db.session.get(Camper, id)
    if not camper:
        return jsonify({"error": "Camper not found"}), 404
    
    try:
        data = request.get_json()
        for attr, value in data.items():
            setattr(camper, attr, value)
        
        db.session.commit()
        return jsonify(camper.to_dict(rules=('-signups',))), 202
    except ValueError:
        db.session.rollback()
        return jsonify({"errors": ["validation errors"]}), 400  # Generic message

# POST /campers
@app.route('/campers', methods=['POST'])
def create_camper():
    try:
        data = request.get_json()
        camper = Camper(**data)
        db.session.add(camper)
        db.session.commit()
        return jsonify(camper.to_dict(rules=('-signups',))), 201
    except ValueError:
        db.session.rollback()
        return jsonify({"errors": ["validation errors"]}), 400  # Generic message

# GET /activities
@app.route('/activities', methods=['GET'])
def get_activities():
    activities = Activity.query.all()
    return jsonify([activity.to_dict(rules=('-signups',)) for activity in activities]), 200

# DELETE /activities/<int:id>
@app.route('/activities/<int:id>', methods=['DELETE'])
def delete_activity(id):
    activity = db.session.get(Activity, id)
    if not activity:
        return jsonify({"error": "Activity not found"}), 404
    
    try:
        db.session.delete(activity)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# POST /signups
@app.route('/signups', methods=['POST'])
def create_signup():
    try:
        data = request.get_json()
        signup = Signup(**data)
        db.session.add(signup)
        db.session.commit()
        
        # Return signup with camper and activity data
        result = signup.to_dict()
        result['camper'] = signup.camper.to_dict(rules=('-signups',))
        result['activity'] = signup.activity.to_dict(rules=('-signups',))
        
        return jsonify(result), 201
    except ValueError:
        db.session.rollback()
        return jsonify({"errors": ["validation errors"]}), 400  # Generic message

if __name__ == '__main__':
    app.run(port=5555, debug=True)
    