# from flask import render_template, redirect, url_for, flash, current_app
# from flask_login import login_required, current_user, login_user, logout_user
# from flask import request
# from app import db, mail
# from app.forms import TicketForm, LoginForm, RegistrationForm, CommentForm
# from app.models import Ticket, User, Comment
# from flask_mail import Message
# from werkzeug.security import generate_password_hash
#
#
# @current_app.route("/", methods=['GET'])
# def index():
#     return render_template('base.html')
#
#
# @current_app.route('/login', methods=['GET', 'POST'])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user and user.check_password(form.password.data):
#             login_user(user)
#             flash('Login successful.', 'success')
#             return redirect(url_for('dashboard'))
#         else:
#             flash('Invalid email or password.', 'danger')
#     return render_template('login.html', form=form)
#
#
# @current_app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('You have been logged out.', 'success')
#     return redirect(url_for('index'))
#
#
# @current_app.route('/create_ticket', methods=['GET', 'POST'])
# @login_required
# def create_ticket():
#     form = TicketForm()
#     if form.validate_on_submit():
#         ticket = Ticket(title=form.title.data, description=form.description.data, creator_id=current_user.id)
#         db.session.add(ticket)
#         db.session.commit()
#         flash('Ticket created successfully!', 'success')
#         if User.query.filter_by(is_hr=True).count() > 0:
#             hr_emails = [user.email for user in User.query.filter_by(is_hr=True).all()]
#             msg = Message('New Ticket Created', sender='your_email@example.com', recipients=hr_emails)
#             msg.body = 'A new ticket has been created. Please check the HR dashboard.'
#             mail.send(msg)
#         return redirect(url_for('index'))
#     return render_template('associate/create_ticket.html', form=form)
#
#
# @current_app.route('/ticket/<int:ticket_id>')
# @login_required
# def view_ticket(ticket_id):
#     ticket = Ticket.query.get_or_404(ticket_id)
#     if current_user.id != ticket.creator_id and not current_user.is_hr:
#         flash('You are not authorized to view this ticket.', 'warning')
#         return redirect(url_for('index'))
#     return render_template('ticket_detail.html', ticket=ticket)
#
#
# @current_app.route('/ticket/<int:ticket_id>/comment', methods=['GET', 'POST'])
# @login_required
# def add_comment(ticket_id):
#     form = CommentForm()
#     ticket = Ticket.query.get_or_404(ticket_id)
#     if form.validate_on_submit():
#         if not current_user.is_hr and current_user.id != ticket.creator_id:
#             flash('You are not authorized to comment on this ticket.', 'warning')
#             return redirect(url_for('main.index'))
#         content = form.comment.data
#         comment = Comment(content=content, ticket_id=ticket_id, author_id=current_user.id)
#         db.session.add(comment)
#         db.session.commit()
#         flash('Your comment has been added.', 'success')
#         return redirect(url_for('view_ticket', ticket_id=ticket_id))
#     return render_template('add_comment.html', form=form, ticket_id=ticket_id)
#
#
# @current_app.route('/registration', methods=['GET','POST'])
# def registration():
#     form = RegistrationForm()
#     if form.validate_on_submit():
#         hashed_password = generate_password_hash(form.password.data)
#         new_user = User(email=form.email.data, password_hash=hashed_password )
#         db.session.add(new_user)
#         db.session.commit()
#         flash('Registration successful! you can log in.', 'success')
#         return redirect(url_for('auth.login'))
#     return render_template('registration.html', form=form)
#
#
# @current_app.route('/dashboard')
# @login_required
# def dashboard():
#     if current_user.is_hr:
#         tickets = Ticket.query.all()  # HR sees all tickets
#     else:
#         tickets = Ticket.query.filter_by(creator_id=current_user.id)  # Associates see only their tickets
#     return render_template('dashboard.html', tickets=tickets)
