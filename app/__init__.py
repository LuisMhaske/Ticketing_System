from _socket import gaierror
from functools import wraps
from smtplib import SMTPException

from flask import Flask, render_template, flash, abort, request, redirect, url_for

from flask_login import login_required, login_user, logout_user, LoginManager, current_user
from flask_mail import Mail, Message
import os
from werkzeug.security import generate_password_hash
from flask_migrate import Migrate
from app.forms import TicketForm, LoginForm, RegistrationForm, CommentForm, HRRegistrationForm, StatusForm
from app.models import Ticket, User, Comment
from app.extension import db


login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///ticketing_system.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'your.smtp.server.com') #For Production Environment implement companies server details here
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))#For Production Environment implement companies server details here
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't'] #For Production Environment implement companies server details here
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_TLS', 'false').lower() in ['true', '1', 't']#For Production Environment implement companies server details here
    app.config['MAIL_USERNAME'] = os.getenv('your email address/username')#For Production Environment implement companies server details here
    app.config['MAIL_PASSWORD'] = os.getenv('your password')#For Production Environment implement companies server details here


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

            try:
                if User.query.filter_by(is_hr=True).count() > 0:
                    sender = current_user.email
                    hr_emails = [user.email for user in User.query.filter_by(is_hr=True).all()]
                    msg = Message('New Ticket Created', sender=sender, recipients=hr_emails)#functionality checked in test environment
                    msg.body = f'''
                    Dear HR,

                    A new ticket has been created with the following details:
                    Title: {form.title.data}
                    Description: {form.description.data}
                    Creator: {current_user.email}

                    Please check the HR dashboard for more details.

                    Best regards,
                    Your Company
                    '''
                    mail.send(msg)#functionality checked in test environment
            #add exception incase there is no test server to test the functionality
            except SMTPException as e:
                flash(f'An error occurred while sending the email: {str(e)}', 'danger')
            except gaierror as e:
                flash(f'Failed to resolve SMTP server hostname: {str(e)}', 'danger')

            return redirect(url_for('index'))
        return render_template('associate/create_ticket.html', form=form)

    @app.route('/ticket/<int:ticket_id>')
    @login_required
    def view_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        if current_user.id != ticket.creator_id and not current_user.is_hr:
            flash('You are not authorized to view this ticket.', 'warning')
            return redirect(url_for('index'))
        comment_form = CommentForm()
        status_form = StatusForm()
        return render_template('ticket_detail.html', ticket=ticket, comment_form=comment_form, status_form=status_form)

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
    def dashboard():
        if current_user.is_hr:
            tickets = Ticket.query.all()  # HR sees all tickets
        else:
            tickets = Ticket.query.filter_by(creator_id=current_user.id)  # Associates see only their tickets
        return render_template('dashboard.html', tickets=tickets)



    @app.route('/hr_signup', methods=['GET', 'POST'])
    def hr_signup():
        if not current_user.is_authenticated:  # Only allow access if the user is not logged in
            form = HRRegistrationForm()
            if form.validate_on_submit():
                try:
                    # Create a new user object with HR privileges
                    new_user = User(email=form.email.data, password_hash=generate_password_hash(form.password.data),
                                    is_hr=True, is_approved=False)
                    db.session.add(new_user)  # Add the new user to the database session
                    db.session.commit()  # Commit the changes to the database
                    print("User added to the database:", new_user)  # Debug print to check if user is added
                    flash('HR registration submitted for approval.', 'info')  # Show a success message
                    return redirect(url_for('index'))  # Redirect to the index page
                except Exception as e:
                    flash('An error occurred while processing your request.', 'danger')  # Show an error message
                    print("Error:", e)  # Print the error for debugging purposes
                    db.session.rollback()  # Rollback changes in case of error
            else:
                print("Form errors:", form.errors)  # Debug print to check form errors
            return render_template('hr_signup.html', title='HR Registration', form=form)  # Render the sign-up form
        else:
            flash('You are already logged in.', 'info')  # Show a message if the user is already logged in
            return redirect(url_for('index'))  # Redirect to the index page

    @app.route('/admin/hr_approvals')
    @login_required
    def hr_approvals():
        if not current_user.is_admin:
            return redirect(url_for('index'))
        pending_hr_users = User.query.filter_by(is_hr=True, is_approved=False).all()
        return render_template('admin/hr_approvals.html', users=pending_hr_users)

    @app.route('/admin/approve_hr/<int:user_id>', methods=['POST'])
    @login_required
    def approve_hr(user_id):
        if not current_user.is_admin:
            return redirect(url_for('index'))
        user = User.query.get_or_404(user_id)
        user.is_approved = True
        db.session.commit()
        flash('HR user approved.')
        return redirect(url_for('hr_approvals'))

    @app.route('/admin/disapprove_hr/<int:user_id>', methods=['POST'])
    @login_required
    def disapprove_hr(user_id):
        if not current_user.is_admin:
            return redirect(url_for('index'))

        user = User.query.get_or_404(user_id)

        # Set is_approved to False
        user.is_approved = False

        # Delete the HR request from the database
        db.session.delete(user)

        db.session.commit()

        flash('HR approval disapproved and request deleted successfully!', 'success')

        return redirect(url_for('hr_approvals'))

    @app.route('/ticket/<int:ticket_id>/change_status', methods=['POST'])
    @login_required
    def change_status(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        if current_user.is_hr:  # Only HR should be able to change the status
            new_status = request.form.get('status')
            ticket.status = new_status
            db.session.commit()
            flash('Status updated successfully!', 'success')
        else:
            flash('You are not authorized to change the status of this ticket.', 'danger')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))

    @app.route('/delete_ticket/<int:ticket_id>', methods=['POST'])
    @login_required
    def delete_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        if current_user.is_hr or current_user.id == ticket.creator_id:
            db.session.delete(ticket)
            db.session.commit()
            flash('Ticket deleted successfully!', 'success')
        else:
            flash('You are not authorized to delete this ticket.', 'warning')
        return redirect(url_for('dashboard'))

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

