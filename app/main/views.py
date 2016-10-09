#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from random import randint, sample
from datetime import datetime
from flask import render_template, url_for, redirect, \
    flash, request, abort
from flask_login import current_user, login_required
from flask_cache import make_template_fragment_key
from . import main
from .forms import AddQuestionForm, AddAnswerForm
from .. import db, cache, api
from ..models import User, Question, Answer, UserOnAnswer, \
    UserOnUser, Comment, Feed, QuestionLog


@main.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    user = current_user._get_current_object()
    context = api.feeds.get_context()
    count = context.get('count')
    if count > 10:
        load_more = True
        feeds = context.get('feeds')[:10]
    else:
        load_more = False
        feeds = context.get('feeds')
    return render_template('index.html', feeds=feeds, count=count,
                            load_more=load_more)


@main.route('/people/<username>', methods=['GET', 'POST'])
def profile(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    newest_questions = user.questions.order_by(
        Question.create_time.desc()).all()[:3]
    newest_answers = user.answers.order_by(
        Answer.create_time.desc()).all()[:3]
    status = check_profile_status(user)
    return render_template('profile.html', user=user, status=status, 
                            newest_questions=newest_questions, 
                            newest_answers=newest_answers)


@main.route('/people/<username>/answers', methods=['GET', 'POST'])
def profile_answer(username, order_by='vote_num'):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    order_by = request.args.get('order_by')
    if order_by == 'created':
        answers = user.answers.order_by(Answer.create_time.desc()).all()
    else:
        answers = user.answers.order_by(Answer.agrees_count.desc()).all()
    status = check_profile_status(user)
    return render_template('profile_answers.html', user=user, 
                            answers=answers, status=status, 
                            order_by=order_by)


@main.route('/people/<username>/questions', methods=['GET', 'POST'])
def profile_question(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    questions = user.questions.order_by(Question.create_time.desc()).all()
    status = check_profile_status(user)
    return render_template('profile_question.html', user=user,
                            questions=questions, status=status)


@main.route('/question/<int:id>', methods=['GET', 'POST'])
def question_page(id):
    question = Question.query.get_or_404(id)
    answers = Answer.query.filter_by(question_id=id).order_by(
        Answer.score.desc()).all()
    status, user = check_user_status(question, answers)
    form = AddAnswerForm()
    if form.validate_on_submit():
        answer = Answer(author=user,
                        question=question,
                        content=form.content.data)
        db.session.add(answer)
        db.session.commit()
        feed = Feed(user_id=user.id,
                    action="answer_question",
                    question_id=question.id,
                    answer_id=answer.id)
        db.session.add(feed)
        return redirect(url_for('main.question_page', id=id))
    return render_template('question.html', form=form,
                           question=question, answers=answers,
                           status=status, user=user)


@main.route('/question/<int:q_id>/answer/<int:a_id>', methods=['GET', 'POST'])
def single_answer_page(q_id, a_id):
    question = Question.query.get_or_404(q_id)
    answers = Answer.query.filter_by(id=a_id).all()
    if answers is None:
        abort(404)
    status, user = check_user_status(question, answers)
    return render_template('answer.html', question=question, 
                            answers=answers, status=status)


@main.route('/answer/<int:a_id>/agree', methods=['POST'])
@login_required
def agree_answer(a_id):
    answer = Answer.query.get_or_404(a_id)
    user = current_user._get_current_object()
    answer.agrees_count += 1
    u_on_a = UserOnAnswer.query.filter(
        db.and_(UserOnAnswer.user_id==user.id, 
                UserOnAnswer.answer_id==answer.id)
    ).first()
    if u_on_a is None:
        u_on_a = UserOnAnswer(user=user, answer=answer, 
            vote=1, vote_up_timestamp=datetime.now())
    elif u_on_a.vote == -1:
        u_on_a.vote = 1
        answer.disagrees_count -= 1
    else:
        u_on_a.vote = 1
    db.session.add_all([answer, u_on_a])
    db.session.commit()
    feed = Feed.query.filter(db.and_(
        Feed.user==user, Feed.answer==answer, 
        Feed.action=="voteup_answer")).first()
    if feed is None:
        feed = Feed(user_id=user.id,
                    action="voteup_answer",
                    question_id=answer.question.id,
                    answer_id=answer.id)
        db.session.add(feed)
    return redirect(request.referrer)

@main.route('/answer/<int:a_id>/disagree', methods=['POST'])
@login_required
def disagree_answer(a_id):
    answer = Answer.query.get_or_404(a_id)
    user = current_user._get_current_object()
    answer.disagrees_count += 1
    u_on_a = UserOnAnswer.query.filter(
        db.and_(UserOnAnswer.user_id==user.id, 
                UserOnAnswer.answer_id==answer.id)
    ).first()
    if u_on_a is None:
        u_on_a = UserOnAnswer(user=user, answer=answer, vote=-1)
    elif u_on_a.vote == 1:
        u_on_a.vote = -1
        answer.agrees_count -= 1
    else:
        u_on_a.vote = -1
    db.session.add_all([answer, u_on_a])
    db.session.commit()
    return redirect(request.referrer)


@main.route('/answer/<int:a_id>/cancel_vote', methods=['POST'])
@login_required
def cancel_vote(a_id):
    answer = Answer.query.get_or_404(a_id)
    user = current_user._get_current_object()
    u_on_a = UserOnAnswer.query.filter(
        db.and_(UserOnAnswer.user_id==user.id, 
                UserOnAnswer.answer_id==answer.id)
    ).first()
    if u_on_a.vote == 1:
        answer.agrees_count -= 1
        u_on_a.vote = 0
        db.session.add_all([answer, u_on_a])
        db.session.commit()
    else:
        answer.disagrees_count -= 1
        u_on_a.vote = 0
        db.session.add_all([answer, u_on_a])
        db.session.commit()
    return redirect(request.referrer)


@main.route('/add-question', methods=['POST'])
@login_required
def add_question():
    form = AddQuestionForm()
    if form.validate_on_submit():
        user = current_user._get_current_object()
        prev_question = Question.query.order_by(Question.id.desc()).first()
        if prev_question is None:
            question = Question(user=user,
                                title=form.title.data,
                                content=form.content.data)
            db.session.add(question)
            db.session.commit()
        else:
            id_plus = randint(1, 4)
            question_id = prev_question.id + id_plus
            question = Question(id=question_id,
                                user=user,
                                title=form.title.data,
                                content=form.content.data)
            db.session.add(question)
            db.session.commit()
        user.follow_question(question)
        feed = Feed(user_id=user.id, 
                    action="ask_question", 
                    question_id=question.id)
        db.session.add(feed)
        return redirect(url_for('main.question_page', id=question.id))


@main.route('/edit-question/<int:id>', methods=['POST'])
@login_required
def edit_question(id):
    question = Question.query.get_or_404(id)
    user = current_user._get_current_object()
    jsonData = request.get_json()
    log = QuestionLog(user=user, question=question, 
                      action=jsonData['action'], 
                      reason=jsonData['reason'])
    if log.action == 'edit-title':
        question.title = jsonData['title']
    elif log.action == 'edit-content':
        question.content = jsonData['content']
    db.session.add_all([question, log])
    return redirect(request.referrer)


@main.route('/edit-answer/<int:id>', methods=['POST'])
@login_required
def edit_answer(id):
    answer = Answer.query.get_or_404(id)
    jsonData = request.get_json()
    answer.update_time = datetime.now()
    answer.content = jsonData['content']
    db.session.add(answer)
    return redirect(request.referrer)


@main.route('/explore', methods=['GET', 'POST'])
def explore():
    questions = Question.query.all()
    if len(questions) <= 5:
        random_questions = questions
    else:
        random_questions = sample(questions, 5)
    return render_template('explore.html', questions=random_questions)


@main.route('/search', methods=['GET', 'POST'])
def search(conditions=None):
    if request.method == 'POST':
        conditions = request.form['conditions']
        return redirect(url_for('.search', conditions=conditions))
    conditions = request.args.get('conditions')
    questions = []
    if conditions != None: 
        keywords = re.split(r'[\s\,\;]+', conditions)
        filters = []
        for keyword in keywords:
            filters.append(Question.title.like('%' + keyword +'%'))
        questions = Question.query.filter(db.or_(*filters))
        # questions is an object of type "BaseQuery"
        # set questions to [] if search result is None
        num = 0
        for question in questions:
            num += 1
            if num != 0:
                break
        if num == 0:
            questions = []
    return render_template('search.html', questions=questions)   


@main.route('/follow/question/<int:id>', methods=['POST'])
@login_required
def follow_question(id):
    question = Question.query.get_or_404(id)
    user = current_user._get_current_object()
    user.follow_question(question)
    feed = Feed.query.filter(db.and_(
        Feed.user==user, Feed.question==question, 
        Feed.action=="follow_question")).first()
    if feed is None:
        feed = Feed(user_id=user.id,
                    action="follow_question",
                    question_id=question.id)
        db.session.add(feed)
    return redirect(request.referrer)


@main.route('/unfollow/question/<int:id>', methods=['POST'])
@login_required
def unfollow_question(id):
    question = Question.query.get_or_404(id)
    current_user.unfollow_question(question)
    return redirect(request.referrer)


@main.route('/follow/<int:id>', methods=['POST'])
@login_required
def follow_user(id):
    user = User.query.get_or_404(id)
    current_user.follow_user(user)
    return redirect(request.referrer)


@main.route('/unfollow/<int:id>', methods=['POST'])
@login_required
def unfollow_user(id):
    user = User.query.get_or_404(id)
    current_user.unfollow_user(user)
    return redirect(request.referrer)


@main.route('/comment/question/<int:q_id>', methods=['POST'])
@login_required
def comment_question(q_id, u_id=None):
    user = current_user._get_current_object()
    if request.args.get('u_id'):
        u_id = int(request.args.get('u_id'))
        comment = Comment(question_id=q_id,
                          replier_id=user.id,
                          replied_id=u_id,
                          reply=True,
                          content=request.form['comment-content'])
    else:
        comment = Comment(question_id=q_id,
                          replier_id=user.id,
                          content=request.form['comment-content'])
    db.session.add(comment)
    return redirect(request.referrer)


@main.route('/comment/answer/<int:a_id>', methods=['POST'])
@login_required
def comment_answer(a_id, u_id=None):
    user = current_user._get_current_object()
    if request.args.get('u_id'):
        u_id = int(request.args.get('u_id'))
        comment = Comment(answer_id=a_id,
                          replier_id=user.id,
                          replied_id=u_id,
                          reply=True,
                          content=request.form['comment-content'])
    else:
        comment = Comment(answer_id=a_id,
                          replier_id=user.id,
                          content=request.form['comment-content'])
    db.session.add(comment)
    return redirect(request.referrer)        


def check_user_status(question, answers):
    status = {}
    user = current_user._get_current_object()
    if current_user.is_authenticated:        
        f = user.user_on_question.filter_by(question_id=question.id).first()
        if f is None:
            status['follow'] = False
        elif f.follow == False:
            status['follow'] = False
        else:
            status['follow'] = True
        for answer in answers:
            u_on_a = UserOnAnswer.query.filter(
                db.and_(UserOnAnswer.user_id==user.id, 
                        UserOnAnswer.answer_id==answer.id)
            ).first()
            if u_on_a is None:
                status[answer.id] = 0
            elif u_on_a.vote == 1:
                status[answer.id] = 1
            elif u_on_a.vote == -1:
                status[answer.id] = -1
            else:
                status[answer.id] = 0
    return (status, user)


def check_profile_status(user):
    status = {}
    if current_user.is_authenticated:
        if current_user.username != user.username:
            status['visit'] = True
            f = UserOnUser.query.filter(
                db.and_(UserOnUser.follower_id==current_user.id,
                        UserOnUser.followed_id==user.id)).first()
            if f is None:
                status['follow'] = False
            elif f.follow == False:
                status['follow'] = False
            else:
                status['follow'] = True
        else:
            status['visit'] = False
    else:
        status['visit'] = True
    return status