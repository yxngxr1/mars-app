from flask import jsonify, request
import flask
from data import db_session
from data.jobs import Jobs
from flask import make_response

blueprint = flask.Blueprint('jobs_api', __name__, template_folder='templates')


@blueprint.route('/api/jobs')
def get_news():
    session = db_session.create_session()
    job = session.query(Jobs).all()
    return jsonify(
        {
            'jobs':
                [item.to_dict(only=('id', 'team_leader', 'job', 'work_size', 'collaborators', 'start_date', 'end_date', 'is_finished', 'user.id')) for item in job]
        }
    )


@blueprint.route('/api/jobs/<int:jobs_id>',  methods=['GET'])
def get_one_job(jobs_id):
    session = db_session.create_session()
    jobs = session.query(Jobs).get(jobs_id)
    if not jobs:
        print(1)
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'jobs': jobs.to_dict(only=('id', 'team_leader', 'job', 'work_size', 'collaborators', 'start_date', 'end_date', 'is_finished', 'user.id'))
        }
    )


@blueprint.route('/api/jobs', methods=['POST'])
def create_job():
    session = db_session.create_session()
    if not request.json:
        return jsonify({'error': 'Empty request'})

    elif not all(key in request.json for key in
                 ['id', 'job', 'team_leader', 'user_id', 'work_size', 'collaborators', 'is_finished']):
        return jsonify({'error': 'Bad request'})

    # проверка на существование работы
    if session.query(Jobs).filter(Jobs.id == request.json['id']).first():
        return jsonify({'error': 'Id already exists'})

    job = Jobs(
        id=request.json['id'],
        job=request.json['job'],
        team_leader=request.json['team_leader'],
        user_id=request.json['user_id'],
        work_size=request.json['work_size'],
        collaborators=request.json['collaborators'],
        is_finished=request.json['is_finished']
    )
    session.add(job)
    session.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/jobs/<int:jobs_id>', methods=['PUT'])
def edit_job(jobs_id):
    session = db_session.create_session()

    if not request.json:
        return jsonify({'error': 'Empty request'})

    elif not all(key in request.json for key in
                 ['id', 'job', 'team_leader', 'user_id', 'work_size', 'collaborators', 'is_finished']):
        return jsonify({'error': 'Bad request'})

    # проверка на существование работы
    if not session.query(Jobs).filter(Jobs.id == request.json['id']).first():
        return jsonify({'error': 'Id not exists'})

    job = session.query(Jobs).get(jobs_id)

    job.id = request.json['id']
    job.job = request.json['job']
    job.team_leader = request.json['team_leader']
    job.user_id = request.json['user_id']
    job.work_size = request.json['work_size']
    job.collaborators = request.json['collaborators']
    job.is_finished = request.json['is_finished']

    session.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/jobs/<int:jobs_id>', methods=['DELETE'])
def delete_job(jobs_id):
    session = db_session.create_session()
    job = session.query(Jobs).get(jobs_id)
    if not job:
        return jsonify({'error': 'Not found'})
    session.delete(job)
    session.commit()
    return jsonify({'success': 'OK'})
