from flask import render_template, redirect, url_for, flash
from app import app, db, mail
from app.forms import TicketForm
from app.models import Ticket, User
from flask_mail import Message

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/create_ticket', methods=['GET', 'POST'])
def create_ticket():
    form = TicketForm()
    if form.validate_on_submit():
        ticket = Ticket(title=form.title.data, description=form.description.data)
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

@app.route('/hr/dashboard')
def hr_dashboard():
    tickets_new = Ticket.query.filter_by(status='New').count()
    tickets_in_progress = Ticket.query.filter_by(status='Work in Progress').count()
    return render_template('hr/dashboard.html', tickets_new=tickets_new, tickets_in_progress=tickets_in_progress)
