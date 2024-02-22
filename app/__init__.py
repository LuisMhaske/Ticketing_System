from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, abort

from flask_login import login_required, current_user, login_user, logout_user, LoginManager
from flask_mail import Mail, Message
import os
from werkzeug.security import generate_password_hash
from flask_migrate import Migrate
from app.forms import TicketForm, LoginForm, RegistrationForm, CommentForm, HRRegistrationForm
from app.models import Ticket, User, Comment
from app.extension import db


login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///ticketing_system.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'

    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.tickets import tickets as tickets_blueprint
    app.register_blueprint(tickets_blueprint, url_prefix='/tickets')

    with app.app_context():
        db.create_all()

    @app.route("/", methods=['GET'])
    def index():
        return render_template('base.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash('Login successful.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('index'))

    @app.route('/create_ticket', methods=['GET', 'POST'])
    @login_required
    def create_ticket():
        form = TicketForm()
        if form.validate_on_submit():
            ticket = Ticket(title=form.title.data, description=form.description.data, creator_id=current_user.id)
            db.session.add(ticket)
            db.session.commit()
            flash('Ticket created successfully!', 'success')
            if User.query.filter_by(is_hr=True).count() > 0:
                hr_emails = [user.email for user in User.query.filter_by(is_hr=True).all()]
                msg = Message('New Ticket Created', sender='your_email@example.com', recipients=hr_emails)
                msg.body = 'A new ticket has been created. Please check the HR dashboard.'
                mail.send(msg)
            return redirect(url_for('index'))
        return render_template('associate/create_ticket.html', form=form)

    @app.route('/ticket/<int:ticket_id>')
    @login_required
    def view_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        if current_user.id != ticket.creator_id and not current_user.is_hr:
            flash('You are not authorized to view this ticket.', 'warning')
            return redirect(url_for('index'))
        return render_template('ticket_detail.html', ticket=ticket)

    @app.route('/ticket/<int:ticket_id>/comment', methods=['GET', 'POST'])
    @login_required
    def add_comment(ticket_id):
        form = CommentForm()
        ticket = Ticket.query.get_or_404(ticket_id)
        if form.validate_on_submit():
            if not current_user.is_hr and current_user.id != ticket.creator_id:
                flash('You are not authorized to comment on this ticket.', 'warning')
                return redirect(url_for('main.index'))
            content = form.comment.data
            comment = Comment(content=content, ticket_id=ticket_id, author_id=current_user.id)
            db.session.add(comment)
            db.session.commit()
            flash('Your comment has been added.', 'success')
            return redirect(url_for('view_ticket', ticket_id=ticket_id))
        return render_template('add_comment.html', form=form, ticket_id=ticket_id)

    @app.route('/registration', methods=['GET', 'POST'])
    def registration():
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(email=form.email.data, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! you can log in.', 'success')
            return redirect(url_for('auth.login'))
        return render_template('registration.html', form=form)

    @app.route('/dashboard')
    @login_required
    @hr_required
    def dashboard():
        if current_user.is_hr:
            tickets = Ticket.query.all()  # HR sees all tickets
        else:
            tickets = Ticket.query.filter_by(creator_id=current_user.id)  # Associates see only their tickets
        return render_template('dashboard.html', tickets=tickets)

    from flask_login import current_user

    @app.route('/hr_signup', methods=['GET', 'POST'])
    def hr_signup():
        if not current_user.is_authenticated:
            # If no user is logged in, proceed with HR sign-up
            form = HRRegistrationForm()
            if form.validate_on_submit():
                user = User(email=form.email.data, password=form.password.data, is_hr=True, is_approved=False)
                db.session.add(user)
                db.session.commit()
                flash('HR registration submitted for approval.', 'info')
                return redirect(url_for('index'))  # Redirect to the index page after sign-up
            return render_template('hr_signup.html', title='HR Registration', form=form)
        elif not current_user.is_admin:
            # If user is logged in but not an admin, deny access
            flash('You do not have permission to access this page.', 'warning')
            return redirect(url_for('index'))
        else:
            # If user is logged in and is an admin, redirect to index page
            flash('You are already logged in as an admin.', 'info')
            return redirect(url_for('index'))

    @app.route('/admin/hr_approvals')
    @login_required
    def hr_approvals():
        if not current_user.is_admin:
            return redirect(url_for('index'))
        pending_hr_users = User.query.filter_by(is_hr=True, is_approved=False).all()
        return render_template('hr_approvals.html', users=pending_hr_users)

    @app.route('/admin/approve_hr/<int:user_id>')
    @login_required
    def approve_hr(user_id):
        if not current_user.is_admin:
            return redirect(url_for('index'))
        user = User.query.get_or_404(user_id)
        user.is_approved = True
        db.session.commit()
        flash('HR user approved.')
        return redirect(url_for('hr_approvals'))

    migrate = Migrate(app, db)
    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin():
    admin_email = 'admin@example.com'
    admin_password = 'secure_admin_password'
    existing_admin = User.query.filter_by(email=admin_email).first()

    if not existing_admin:
        admin_user = User(
            email=admin_email,
            password_hash=generate_password_hash(admin_password, method='pbkdf2:sha256'),
            is_admin=True  # Assuming your User model has an 'is_admin' field
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")

def hr_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_hr or not current_user.is_approved:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

