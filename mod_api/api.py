from flask import jsonify
from db_setup import Subject, Item
from mod_db.connect_db import connect_db
from flask import Blueprint

api = Blueprint('mod_api', __name__)

session = connect_db()


# JSON APIs to view Subject Information
@api.route('/subject/<int:subject_id>/item/JSON')
def homeworkItemsJSON(subject_id):
    subject = session.query(Subject).filter_by(id=subject_id).one()
    items = session.query(Item).filter_by(subject_id=subject_id).all()
    return jsonify(Items=[i.serialize for i in items])


@api.route('/subject/<int:subject_id>/item/<int:item_id>/JSON')
def homeworkItemJSON(subject_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@api.route('/subject/JSON')
def subjectsJSON():
    subjects = session.query(Subject).all()
    return jsonify(subjects=[s.serialize for s in subjects])
