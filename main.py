from flask import Flask, request, make_response, render_template, redirect, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField
from wtforms.validators import DataRequired
from wtforms import validators
from wtforms.fields.html5 import EmailField
from data import db_session
from data.users import User
from data.jobs import Jobs
from data.departments import Departments
import jobs_api
import users_api
from flask import jsonify
from y_api import get_toponym_by_address, get_area_object
import requests
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


class JobsForm(FlaskForm):
    job = StringField('Название работы', validators=[DataRequired()])
    team_leader = IntegerField("Id ТимЛида", validators=[DataRequired()])
    work_size = IntegerField("Время работы", validators=[DataRequired()])
    collaborators = StringField("Участники", validators=[DataRequired()])
    is_finished = BooleanField("Завершено?")
    submit = SubmitField('Отправить')


class DepartmentsForm(FlaskForm):
    title = StringField('Название департамента', validators=[DataRequired()])
    chief = IntegerField("Id ТимЛида", validators=[DataRequired()])
    members = StringField("Участники", validators=[DataRequired()])
    email = EmailField('Почта', validators=[DataRequired(), validators.Email()])
    submit = SubmitField('Отправить')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), validators.Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повтор пароля', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    age = StringField('Возраст', validators=[DataRequired()])
    position = StringField('Должность', validators=[DataRequired()])
    speciality = StringField('Профессия', validators=[DataRequired()])
    address = StringField('Посадочное место', validators=[DataRequired()])
    city_from = StringField('Родной город', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


@app.route('/')
def main():
    session = db_session.create_session()
    users = session.query(User).all()
    jobs = session.query(Jobs).all()
    return render_template('index.html', title='Главная', users=users, jobs=jobs)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form, message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form, message="Такой пользователь уже есть")
        user = User(
            email=form.email.data,
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            position=form.position.data,
            speciality=form.speciality.data,
            city_from=form.city_from.data,
            address=form.address.data)
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/add_job',  methods=['GET', 'POST'])
@login_required
def add_job():
    form = JobsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        if not session.query(User).filter(User.id == form.team_leader.data).first():
            return render_template('job.html', title='Добавление работы', form=form, message="Id ТимЛида не существует")
        job = Jobs(job=form.job.data,
                   team_leader=form.team_leader.data,
                   work_size=form.work_size.data,
                   collaborators=form.collaborators.data,
                   is_finished=form.is_finished.data)
        current_user.jobs.append(job)
        session.merge(current_user)
        session.commit()
        return redirect('/')
    return render_template('job.html', title='Добавление работы', form=form)


@app.route('/job_change/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_job(id):
    form = JobsForm()
    if request.method == "GET":
        session = db_session.create_session()
        job = session.query(Jobs).filter(Jobs.id == id, ((current_user == Jobs.user) | (current_user.id == Jobs.team_leader))).first()
        if job:
            form.job.data = job.job
            form.team_leader.data = job.team_leader
            form.work_size.data = job.work_size
            form.collaborators.data = job.collaborators
            form.is_finished.data = job.is_finished
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        job = session.query(Jobs).filter(Jobs.id == id, ((current_user == Jobs.user) | (current_user.id == Jobs.team_leader))).first()
        if job:
            job.job = form.job.data
            job.team_leader = form.team_leader.data
            job.work_size = form.work_size.data
            job.collaborators = form.collaborators.data
            job.is_finished = form.is_finished.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('job.html', title='Редактирование работы', form=form)


@app.route('/job_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def jobs_delete(id):
    session = db_session.create_session()
    job = session.query(Jobs).filter(Jobs.id == id, ((current_user == Jobs.user) | (current_user.id == Jobs.team_leader))).first()
    if job:
        session.delete(job)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/departments')
def department():
    session = db_session.create_session()
    users = session.query(User).all()
    departments = session.query(Departments).all()
    return render_template('list_departments.html', title='Список Департаментов', users=users, departments=departments)


@app.route('/add_department',  methods=['GET', 'POST'])
@login_required
def add_department():
    form = DepartmentsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        if not session.query(User).filter(User.id == form.chief.data).first():
            return render_template('department.html', title='Добавление департамента', form=form, message="Id ТимЛида не существует")
        if session.query(Departments).filter(Departments.email == form.email.data).first():
            return render_template('department.html', title='Добавление департамента', form=form, message="Департамент с такой почтой уже существует")
        dep = Departments(title=form.title.data,
                          chief=form.chief.data,
                          members=form.members.data,
                          email=form.email.data)
        current_user.departments.append(dep)
        session.merge(current_user)
        session.commit()
        return redirect('/departments')
    return render_template('department.html', title='Добавление департамента', form=form)


@app.route('/department_change/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    form = DepartmentsForm()
    if request.method == "GET":
        session = db_session.create_session()
        dep = session.query(Departments).filter(Departments.id == id, ((current_user == Departments.user) | (current_user.id == Departments.chief))).first()
        if dep:
            form.title.data = dep.title
            form.chief.data = dep.chief
            form.members.data = dep.members
            form.email.data = dep.email
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        dep = session.query(Departments).filter(Departments.id == id, ((current_user == Departments.user) | (current_user.id == Departments.chief))).first()
        if not session.query(User).filter(User.id == form.chief.data).first():
            return render_template('department.html', title='Добавление департамента', form=form, message="Id ТимЛида не существует")
        if session.query(Departments).filter(Departments.email == form.email.data).first():
            if dep.email != form.email.data:
                print(session.query(Departments).filter(Departments.email == form.email.data).first().email, form.email.data)
                return render_template('department.html', title='Добавление департамента', form=form, message="Департамент с такой почтой уже существует")
        if dep:
            dep.title = form.title.data
            dep.chief = form.chief.data
            dep.members = form.members.data
            dep.email = form.email.data
            session.commit()
            return redirect('/departments')
        else:
            abort(404)
    return render_template('department.html', title='Редактирование департамента', form=form)


@app.route('/department_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def department_delete(id):
    session = db_session.create_session()
    dep = session.query(Departments).filter(Departments.id == id, ((current_user == Departments.user) | (current_user.id == Departments.chief))).first()
    if dep:
        session.delete(dep)
        session.commit()
    else:
        abort(404)
    return redirect('/departments')


@app.route('/users_show/<int:user_id>')
def user_show(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        return render_template('users_show.html', title='Не найдено', message="Такого пользователя не сущесвтует")

    place = get_toponym_by_address(user.city_from)
    coords = place["Point"]["pos"].replace(' ', ',')
    spn = ",".join(get_area_object(place))
    map_params = {
        "ll": coords,
        "spn": spn,
        "l": 'sat'}

    map_api_server = "http://static-maps.yandex.ru/1.x/"
    surname, name = user.surname, user.name
    city = user.city_from
    src = requests.get(map_api_server, params=map_params).url
    return render_template('users_show.html', title=city, city=city, src=src, surname=surname, name=name)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def main():
    db_session.global_init("db/users.db")
    app.register_blueprint(jobs_api.blueprint)
    app.register_blueprint(users_api.blueprint)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
