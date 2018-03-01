from flask import render_template, request
from flask import redirect, url_for, flash
from sqlalchemy import asc
from db_setup import Subject, Item, User
from flask import session as login_session
from oauth2client import client
from flask import Blueprint
from functools import wraps
from mod_db.connect_db import connect_db

views = Blueprint('mod_views', __name__, template_folder='templates')

session = connect_db()


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'username' in login_session:
            return function(*args, **kwargs)
        else:
            return redirect('/login')
    return wrapper


@views.route('/')
@views.route('/subject/')
def showSubjects():
    """
    Show all subjects stored in the database
    """
    subjects = session.query(Subject).order_by(asc(Subject.name))
    subject_creator = []
    for subject in subjects:
        timestamp = subject.timestamp
        user = getUser(subject.user_id)
        card_info = (subject, user, timestamp)
        subject_creator.append(card_info)
    if 'username' not in login_session:
        return render_template('publicsubjects.html', subjects=subject_creator)
    else:
        picture = login_session['picture']
        return render_template(
            'subjects.html', subjects=subject_creator, picture=picture)


@views.route('/subject/new/', methods=['GET', 'POST'])
@login_required
def newSubject():
    """
    Create a new subject
    """
    picture = login_session['picture']
    if request.method == 'POST':

        # Subject name cannot be empty
        if request.form['name'] == "":
            flash('Please enter a subject name.', 'error')
            return render_template('new_subject.html', picture=picture)
        # Check if subject name already exists with this user
        subjectName = getSubjectName(
            request.form['name'], login_session['user_id'])
        if subjectName == request.form['name']:
            flash(
                '%s already exists. Please enter a different subject name.'
                % request.form['name'], 'error')
            return render_template('new_subject.html', picture=picture)
        else:
            newSubject = Subject(
                name=request.form['name'], user_id=login_session['user_id'])
            session.add(newSubject)
            flash(
                'New subject \'%s\' successfully created!' % newSubject.name,
                'success')
            session.commit()
            return redirect(url_for('mod_views.showSubjects'))
    else:
        return render_template('new_subject.html', picture=picture)


@views.route('/subject/<int:subject_id>/edit/', methods=['GET', 'POST'])
@login_required
def editSubject(subject_id):
    """
    Edit a subject
    """
    try:
        editedSubject = session.query(Subject).filter_by(id=subject_id).one()
    except:
        flash('No such subject is found.', 'error')
        return redirect(url_for('mod_views.showSubjects'))

    if login_session['user_id'] != editedSubject.user_id:
        session.close()
        flash('You are not authorized to edit this subject.', 'error')
        return redirect(url_for('mod_views.showSubjects'))
    if request.method == 'POST':
        if request.form['name']:
            editedSubject.name = request.form['name']
            flash(
                '\'%s\' successfully edited ' % editedSubject.name, 'success')
            return redirect(url_for('mod_views.showSubjects'))
    else:
        picture = login_session['picture']
        return render_template(
            'edit_subject.html', subject=editedSubject, picture=picture)


@views.route('/subject/<int:subject_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteSubject(subject_id):
    """
    Delete a subject
    """
    try:
        subjectToDelete = session.query(Subject).filter_by(id=subject_id).one()
    except:
        flash('No such subject is found.', 'error')
        return redirect(url_for('mod_views.showSubjects'))

    if subjectToDelete.user_id != login_session['user_id']:
        session.close()
        flash('You are not authorized to delete this subject.', 'error')
        return redirect(url_for('mod_views.showSubjects'))

    if request.method == 'POST':
        session.delete(subjectToDelete)
        flash(
            '\'%s\' successfully deleted' % subjectToDelete.name,
            'success')
        session.commit()
        return redirect(url_for(
            'mod_views.showSubjects', subject_id=subject_id))
    else:
        picture = login_session['picture']
        return render_template(
            'delete_subject.html', subject=subjectToDelete, picture=picture)


@views.route('/subject/<int:subject_id>/')
@views.route('/subject/<int:subject_id>/item/')
def showItems(subject_id):
    """
    Show homework items for each subject
    """
    subject = session.query(Subject).filter_by(id=subject_id).one()
    creator = getUser(subject.user_id)
    items = session.query(Item).filter_by(subject_id=subject_id).all()

    if 'username' not in login_session:
        return render_template(
            'publicitems.html', items=items, subject=subject)
    else:
        # Get picture of current user
        picture = login_session['picture']
        if creator.id != login_session['user_id']:
            return render_template(
                'publicitems.html', items=items, subject=subject,
                picture=picture)
        else:
            items = session.query(Item).filter_by(subject_id=subject_id).all()
            return render_template(
                'items.html', items=items, subject=subject, picture=picture)


@views.route('/subject/<int:subject_id>/item/new/', methods=['GET', 'POST'])
@login_required
def newItem(subject_id):
    """
    Create a new homework item
    """
    try:
        subject = session.query(Subject).filter_by(id=subject_id).one()
    except:
        flash('No such subject is found.', 'error')
        return redirect(url_for('mod_views.showSubjects'))

    if login_session['user_id'] != subject.user_id:
        flash(
            'You are not authorized to create a new item for this subject!',
            'error')
        return redirect(url_for('mod_views.showItems', subject_id=subject_id))
    if request.method == 'POST':
        if request.form['name'] == "":
            flash('Please enter an item name.', 'error')
            return redirect(url_for(
                'mod_views.newItem', subject_id=subject_id))
        newItem = Item(
            name=request.form['name'], description=request.form['description'],
            time_estimate=request.form['time_estimate'],
            priority=request.form['priority'], subject_id=subject_id,
            user_id=subject.user_id)
        session.add(newItem)
        session.commit()
        flash('\'%s\' successfully created' % (newItem.name), 'success')
        return redirect(url_for('mod_views.showItems', subject_id=subject_id))
    else:
        picture = login_session['picture']
        return render_template(
            'new_item.html', subject_id=subject_id, picture=picture)


@views.route(
    '/subject/<int:subject_id>/item/<int:item_id>/edit',
    methods=['GET', 'POST'])
@login_required
def editItem(subject_id, item_id):
    """
    Edit a homework item
    """
    try:
        subject = session.query(Subject).filter_by(id=subject_id).one()
    except:
        flash('No such subject is found.', 'error')
        return redirect(url_for('mod_views.showSubjects'))

    if login_session['user_id'] != subject.user_id:
        flash('You are not authorized to edit items of this subject.', 'error')
        return redirect(url_for('mod_views.showItems', subject_id=subject_id))

    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['time_estimate']:
            editedItem.time_estimate = request.form['time_estimate']
        if request.form['priority']:
            editedItem.priority = request.form['priority']
        session.add(editedItem)
        session.commit()
        flash('\'%s\' successfully edited' % request.form['name'], 'success')
        return redirect(url_for('mod_views.showItems', subject_id=subject_id))
    else:
        picture = login_session['picture']
        return render_template(
            'edit_item.html', subject_id=subject_id, item_id=item_id,
            item=editedItem, picture=picture)


@views.route(
    '/subject/<int:subject_id>/item/<int:item_id>/delete',
    methods=['GET', 'POST'])
@login_required
def deleteItem(subject_id, item_id):
    """
    Delete a homework item
    """
    try:
        subject = session.query(Subject).filter_by(id=subject_id).one()
    except:
        flash('No such subject is found.', 'error')
        return redirect(url_for('mod_views.showSubjects'))

    if login_session['user_id'] != subject.user_id:
        flash(
            'You are not authorized to delete items of this subject.',
            'error')
        return redirect(url_for('mod_views.showItems', subject_id=subject_id))
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    itemName = itemToDelete.name
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('\'%s\' successfully deleted' % itemName, 'success')
        return redirect(url_for('mod_views.showItems', subject_id=subject_id))
    else:
        picture = login_session['picture']
        return render_template(
            'delete_item.html', subject_id=subject_id, item=itemToDelete,
            picture=picture)


# Helper Methods
def getUser(user_id):
    """
    Return user object with the given user_id.  If no user found with
    the id, return None
    """
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None


def getSubjectName(name, user_id):
    """
    Check if a given subject name exists with the given user_id
    If no such subject found, return None
    """
    try:
        subject = session.query(Subject).filter_by(
            name=name, user_id=user_id).one()
        return subject.name
    except:
        return None
