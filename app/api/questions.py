from sqlalchemy.sql.expression import func
from flask import jsonify, url_for
from . import api
from ..models import Question


@api.route('/RandomQuestions/')
def random_question(size=5):
    random_questions = Question.query.order_by(func.rand()).limit(5)
    question = [dict(link=url_for('main.question_page', id=x.id),
                     title=x.title) for x in random_questions]
    return jsonify(question=question)
