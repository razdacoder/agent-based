from flask import Flask, render_template, send_file, request, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
import agentpy as ap
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
# Change this to a random secret key
app.config['SECRET_KEY'] = 'mysecretskey'
# Use SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Updated User model with hashed passwords
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

# Registration form


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


# Login form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6, max=100)])
    submit = SubmitField('Login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(
            username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            new_user = User(username=form.username.data)
            new_user.set_password(form.password.data)  # Set hashed password
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Update login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):  # Check hashed password
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html', form=form)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class StudentAgent(ap.Agent):

    def setup(self):
        self.exam_score = 0
        self.practical_score = 0
        self.attendance_score = 0
        self.test_score = 0
        self.assignment_score = 0

    def add_exam_score(self, score):
        self.exam_score = min(60, max(0, score))

    def add_practical_score(self, score):
        self.practical_score = min(100, max(0, score))

    def add_attendance_score(self, score):
        self.attendance_score = min(100, max(0, score))

    def add_test_score(self, score):
        self.test_score = min(100, max(0, score))

    def add_assignment_score(self, score):
        self.assignment_score = min(100, max(0, score))

    def calculate_overall_score(self):
        overall_score = self.exam_score + self.practical_score + \
            self.attendance_score + self.test_score + self.assignment_score
        return overall_score


class EvaluationModel(ap.Model):

    def setup(self):
        # Create 20 students
        self.students = [StudentAgent(self) for _ in range(20)]

    def step(self):
        # Simulate scores for each category for each student
        for student in self.students:
            student.add_exam_score(self.random.randint(20, 60))
            student.add_practical_score(self.random.randint(5, 10))
            student.add_attendance_score(self.random.randint(2, 5))
            student.add_test_score(self.random.randint(5, 15))
            student.add_assignment_score(self.random.randint(5, 10))

    def evaluate_students(self):
        student_data = []
        for student in self.students:
            overall_score = student.calculate_overall_score()
            student_data.append(
                {"id": student.id, "exams": student.exam_score, "practical": student.practical_score, "att": student.attendance_score, "test": student.test_score, "assg": student.assignment_score, "overall_score": overall_score})

        return student_data


model = EvaluationModel()


def generate_bar_chart(labels, values, title):
    plt.figure(figsize=(10, 6))
    plt.bar(labels, values, color='skyblue')
    plt.xlabel('Student ID')
    plt.ylabel('Score')
    plt.title(f'{title} Scores of Students')
    plt.xticks(labels)

    # Save the plot to a BytesIO object
    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)
    plt.close()

    # Encode the image to base64
    image_base64 = base64.b64encode(image_stream.read()).decode('utf-8')
    return image_base64


@app.route('/')
@login_required
def index():
    model.run(steps=10)
    student_data = model.evaluate_students()

    # Generate bar charts for each metric
    exams_labels = [student["id"] for student in student_data]
    exams_values = [student["exams"] for student in student_data]
    exams_chart = generate_bar_chart(exams_labels, exams_values, 'Exams')

    practical_labels = [student["id"] for student in student_data]
    practical_values = [student["practical"] for student in student_data]
    practical_chart = generate_bar_chart(
        practical_labels, practical_values, 'Practical')

    attendance_labels = [student["id"] for student in student_data]
    attendance_values = [student["att"]
                         for student in student_data]
    attendance_chart = generate_bar_chart(
        attendance_labels, attendance_values, 'Attendance')

    test_labels = [student["id"] for student in student_data]
    test_values = [student["test"] for student in student_data]
    test_chart = generate_bar_chart(test_labels, test_values, 'Test')

    assignments_labels = [student["id"] for student in student_data]
    assignments_values = [student["assg"]
                          for student in student_data]
    assignments_chart = generate_bar_chart(
        assignments_labels, assignments_values, 'Assignments')

    overall_labels = [student["id"] for student in student_data]
    overall_values = [student["overall_score"]
                      for student in student_data]
    overall_chart = generate_bar_chart(
        overall_labels, overall_values, 'Overall Score')

    # chart_image = generate_bar_chart(student_data)
    return render_template('index.html', students=student_data,
                           exams_chart=exams_chart,
                           practical_chart=practical_chart,
                           attendance_chart=attendance_chart,
                           test_chart=test_chart,
                           assignments_chart=assignments_chart,
                           overall_chart=overall_chart)


@app.route('/chart_image')
def overall_chart():
    chart_image = request.args.get('overall_chart', '')
    return send_file(BytesIO(base64.b64decode(chart_image)), mimetype='image/png')

# Add routes to serve individual chart images


@app.route('/exams_chart')
def exams_chart():
    chart_image = request.args.get('exams_chart', '')
    return send_file(BytesIO(base64.b64decode(chart_image)), mimetype='image/png')


@app.route('/practical_chart')
def practical_chart():
    chart_image = request.args.get('practical_chart', '')
    return send_file(BytesIO(base64.b64decode(chart_image)), mimetype='image/png')


@app.route('/attendance_chart')
def attendance_chart():
    chart_image = request.args.get('attendance_chart', '')
    return send_file(BytesIO(base64.b64decode(chart_image)), mimetype='image/png')


@app.route('/test_chart')
def test_chart():
    chart_image = request.args.get('test_chart', '')
    return send_file(BytesIO(base64.b64decode(chart_image)), mimetype='image/png')


@app.route('/assignments_chart')
def assignments_chart():
    chart_image = request.args.get('assignments_chart', '')
    return send_file(BytesIO(base64.b64decode(chart_image)), mimetype='image/png')
