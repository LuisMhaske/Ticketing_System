from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Ticket
from . import db

tickets = Blueprint('tickets', __name__)


@tickets.route('/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        new_ticket = Ticket(title=title, description=description, creator_id=current_user.id)
        db.session.add(new_ticket)
        db.session.commit()
        flash('Your ticket has been created.')
        return redirect(url_for('main.dashboard'))
    return render_template('create_ticket.html')


@tickets.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if not current_user.is_hr:
        flash('You do not have access to this page.')
        return redirect(url_for('main.index'))
    tickets = Ticket.query.all()
    return render_template('dashboard.html', tickets=tickets)


@tickets.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if request.method == 'POST':
        # Update ticket status or add comments based on form input
        pass
    return render_template('ticket_detail.html', ticket=ticket)
