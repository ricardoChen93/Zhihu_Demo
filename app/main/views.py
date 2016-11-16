#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from random import randint, sample
from datetime import datetime
from flask import render_template, url_for, redirect, \
    flash, request, abort
from flask_login import current_user, login_required
from flask_caching import make_template_fragment_key
from . import main
from .forms import AddQuestionForm, AddAnswerForm
from .. import db, cache, api
from ..models import User, Question, Answer, UserOnAnswer, \
    UserOnUser, Comment, Feed, QuestionLog


@main.route('/', methods=['GET', 'POST'])
def index():
    """首页, 如果用户未登录则跳转到登录界面
    """
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    user = current_user._get_current_object()

    # 推送消息从api获取， 默认获取10条
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
    """用户主页
    @username, 用户标识名
    """
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
    """用户的所有回答
    @username, 用户标识名
    @order_by, 回答排序方式, 回答时间或赞同数
    """
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
    """用户所有提问
    @username, 用户标识名
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    questions = user.questions.order_by(Question.create_time.desc()).all()
    status = check_profile_status(user)
    return render_template('profile_question.html', user=user,
                           questions=questions, status=status)


@main.route('/question/<int:id>', methods=['GET', 'POST'])
def question_page(id):
    """问题页
    @id, 问题的id
    """
    question = Question.query.get_or_404(id)
    answers = Answer.query.filter_by(question_id=id).order_by(
        Answer.score.desc()).all()
    status, user = check_user_status(question, answers)
    form = AddAnswerForm()

    # 添加回答并推送给关注用户
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
    """回答页
    @q_id, 此回答所属问题的id
    @a_id, 此回答的id
    """
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
    """赞同回答
    @a_id, 被赞同回答的id
    """
    answer = Answer.query.get_or_404(a_id)
    user = current_user._get_current_object()

    # 修改回答赞同数、反对数、当前用户与回答的关系
    answer.agrees_count += 1
    u_on_a = UserOnAnswer.query.filter(db.and_(
                UserOnAnswer.user_id == user.id,
                UserOnAnswer.answer_id == answer.id)).first()
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

    # 确认是否推送消息，防止重复推送
    feed = Feed.query.filter(db.and_(
                Feed.user == user, Feed.answer == answer,
                Feed.action == "voteup_answer")).first()
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
    """反对回答
    @a_id, 被反对回答的id
    """
    answer = Answer.query.get_or_404(a_id)
    user = current_user._get_current_object()

    # 修改回答赞同数、反对数、当前用户与回答的关系
    answer.disagrees_count += 1
    u_on_a = UserOnAnswer.query.filter(db.and_(
                UserOnAnswer.user_id == user.id,
                UserOnAnswer.answer_id == answer.id)).first()
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
    """取消投票
    @a_id, 被取消回答的id
    """
    answer = Answer.query.get_or_404(a_id)
    user = current_user._get_current_object()

    # 修改回答赞同数、反对数、当前用户与回答的关系
    u_on_a = UserOnAnswer.query.filter(db.and_(
                UserOnAnswer.user_id == user.id,
                UserOnAnswer.answer_id == answer.id)).first()
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
    """添加新问题并推送消息
    """
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
    """编辑问题并添加问题日志
    @id, 被编辑问题的id
    """
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
    """编辑回答
    @id, 被编辑回答的id
    """
    answer = Answer.query.get_or_404(id)
    jsonData = request.get_json()
    answer.update_time = datetime.now()
    answer.content = jsonData['content']
    db.session.add(answer)
    return redirect(request.referrer)


@main.route('/explore', methods=['GET', 'POST'])
def explore():
    """发现页，随机展示问题，待修改
    """
    questions = Question.query.all()
    if len(questions) <= 5:
        random_questions = questions
    else:
        random_questions = sample(questions, 5)
    return render_template('explore.html', questions=random_questions)


@main.route('/search', methods=['GET', 'POST'])
def search(conditions=None):
    """搜索问题
    @conditions, 搜索关键词, 支持空格、英文逗号、分号分隔
    """
    if request.method == 'POST':
        conditions = request.form['conditions']
        return redirect(url_for('.search', conditions=conditions))
    conditions = request.args.get('conditions')
    questions = []
    if conditions is not None:
        keywords = re.split(r'[\s\,\;]+', conditions)
        filters = []
        for keyword in keywords:
            filters.append(Question.title.like('%' + keyword + '%'))
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
    """关注问题
    @id, 被关注问题的id
    """
    question = Question.query.get_or_404(id)
    user = current_user._get_current_object()
    user.follow_question(question)

    # 检查当前用户是否曾经关注过该问题，防止重复推送
    feed = Feed.query.filter(db.and_(
                Feed.user == user, Feed.question == question,
                Feed.action == "follow_question")).first()
    if feed is None:
        feed = Feed(user_id=user.id,
                    action="follow_question",
                    question_id=question.id)
        db.session.add(feed)

    return redirect(request.referrer)


@main.route('/unfollow/question/<int:id>', methods=['POST'])
@login_required
def unfollow_question(id):
    """取消关注问题
    @id, 被取消关注的问题的id
    """
    question = Question.query.get_or_404(id)
    current_user.unfollow_question(question)
    return redirect(request.referrer)


@main.route('/follow/<int:id>', methods=['POST'])
@login_required
def follow_user(id):
    """关注用户
    @id, 被关注用户的id
    """
    user = User.query.get_or_404(id)
    current_user.follow_user(user)
    return redirect(request.referrer)


@main.route('/unfollow/<int:id>', methods=['POST'])
@login_required
def unfollow_user(id):
    """取消关注用户
    @id, 被取消关注的用户的id
    """
    user = User.query.get_or_404(id)
    current_user.unfollow_user(user)
    return redirect(request.referrer)


@main.route('/comment/question/<int:q_id>', methods=['POST'])
@login_required
def comment_question(q_id, u_id=None):
    """添加问题评论或回复他人评论
    @q_id, 被评论问题的id
    @u_id, 被回复用户的id
    """
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
    """添加回答评论或回复他人评论
    @a_id, 被评论回答的id
    @u_id, 被回复用户的id
    """
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
    """确认当前用户与问题及回答的关系
    @question, 当前浏览的问题
    @answers, 该问题下已有的所有回答
    @status['follow'], 是否已关注当前问题
    @status[answer_id], 赞同/反对/两者都不 某个回答
    """
    status = {}
    user = current_user._get_current_object()
    if current_user.is_authenticated:
        f = user.user_on_question.filter_by(question_id=question.id).first()
        if f is None:
            status['follow'] = False
        elif not f.follow:
            status['follow'] = False
        else:
            status['follow'] = True
        for answer in answers:
            u_on_a = UserOnAnswer.query.filter(db.and_(
                        UserOnAnswer.user_id == user.id,
                        UserOnAnswer.answer_id == answer.id)).first()
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
    """确认当前用户与被访问用户的关系
    @user, 被访问用户
    @status['visit'], 是否为当前用户的主页
    @status['follow'], 是否已关注被访问用户
    """
    status = {}
    if current_user.is_authenticated:
        if current_user.username != user.username:
            status['visit'] = True
            f = UserOnUser.query.filter(db.and_(
                    UserOnUser.follower_id == current_user.id,
                    UserOnUser.followed_id == user.id)).first()
            if f is None:
                status['follow'] = False
            elif not f.follow:
                status['follow'] = False
            else:
                status['follow'] = True
        else:
            status['visit'] = False
    else:
        status['visit'] = True
    return status
