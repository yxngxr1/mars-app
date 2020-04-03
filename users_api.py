from flask import jsonify, request
import flask
from data import db_session
from data.users import User
from flask import make_response

blueprint = flask.Blueprint('users_api', __name__, template_folder='templates')


@blueprint.route('/api/users')
def get_users():
    session = db_session.create_session()
    users = session.query(User).all()
    return jsonify(
        {
            'users':
                [item.to_dict(only=('id', 'surname', 'name', 'speciality', 'address', 'email')) for item in users]
        }
    )


@blueprint.route('/api/users/<int:user_id>',  methods=['GET'])
def get_one_user(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        print(1)
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'user': user.to_dict(only=('id', 'surname', 'name', 'age', 'position', 'speciality', 'address', 'email', 'jobs.id'))
        }
    )


@blueprint.route('/api/users', methods=['POST'])
def create_user():
    session = db_session.create_session()
    if not request.json:
        return jsonify({'error': 'Empty request'})

    elif not all(key in request.json for key in
                 ['id', 'surname', 'name', 'age', 'position', 'speciality', 'address', 'email', 'password']):
        return jsonify({'error': 'Bad request'})

    # проверка на существование юзера
    if session.query(User).filter(User.id == request.json['id']).first():
        return jsonify({'error': 'Id already exists'})

    user = User(
        id=request.json['id'],
        surname=request.json['surname'],
        name=request.json['name'],
        age=request.json['age'],
        position=request.json['position'],
        speciality=request.json['speciality'],
        address=request.json['address'],
        email=request.json['email']
    )
    user.set_password(request.json['password'])
    session.add(user)
    session.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/users/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    session = db_session.create_session()

    if not request.json:
        return jsonify({'error': 'Empty request'})

    elif not all(key in request.json for key in
                 ['id', 'surname', 'name', 'age', 'position', 'speciality', 'address', 'email', 'password']):
        return jsonify({'error': 'Bad request'})

    # проверка на существование юзера
    if not session.query(User).filter(User.id == request.json['id']).first():
        return jsonify({'error': 'Id not exists'})

    user = session.query(User).get(user_id)

    user.id = request.json['id']
    user.surname = request.json['surname']
    user.name = request.json['name']
    user.age = request.json['age']
    user.position = request.json['position']
    user.speciality = request.json['speciality']
    user.address = request.json['address']
    user.email = request.json['email']
    user.set_password(request.json['password'])

    session.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        return jsonify({'error': 'Not found'})
    session.delete(user)
    session.commit()
    return jsonify({'success': 'OK'})

