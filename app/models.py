#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import operator
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from sqlalchemy import DDL
from markdown import markdown
from . import db, login_manager


class UserOnUser(db.Model):
    __tablename__ = 'user_on_user'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    follow = db.Column(db.Boolean, default=True)
    follow_timestamp = db.Column(db.DateTime, default=datetime.now)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))
    replier_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reply = db.Column(db.Boolean, default=False)
    replied_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text)
    create_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def get_replier(self):
        return User.query.filter_by(id=self.replier_id).first()

    def get_replied(self):
        return User.query.filter_by(id=self.replied_id).first()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    username = db.Column(db.String(64), unique=True)
    nickname = db.Column(db.String(64), index=True)
    member_since = db.Column(db.DateTime(), default=datetime.now)
    self_introduction = db.Column(db.String(128))
    avatar_file = db.Column(db.String(128), default='avatar/user.jpg')
    questions = db.relationship('Question', backref='user', lazy='dynamic')
    answers = db.relationship('Answer', backref='author', lazy='dynamic')
    user_on_answer = db.relationship('UserOnAnswer', backref='user', lazy='dynamic')
    user_on_question = db.relationship('UserOnQuestion', backref='user', lazy='dynamic')
    reply_comment = db.relationship('Comment', 
                                    foreign_keys=[Comment.replier_id],
                                    backref=db.backref('replier', lazy='joined'),
                                    lazy='dynamic',
                                    cascade='all, delete-orphan')
    replied_comment = db.relationship('Comment', 
                                      foreign_keys=[Comment.replied_id],
                                      backref=db.backref('replied', lazy='joined'),
                                      lazy='dynamic',
                                      cascade='all, delete-orphan')
    followers = db.relationship('UserOnUser', 
                                foreign_keys=[UserOnUser.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    followed = db.relationship('UserOnUser', 
                                foreign_keys=[UserOnUser.follower_id],
                                backref=db.backref('follower', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    feeds = db.relationship('Feed', backref='user', lazy='dynamic')
    question_log = db.relationship('QuestionLog', backref='user', lazy='dynamic')


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def calculate_total_agrees(self):
        total_agrees = 0
        for answer in self.answers:
            total_agrees += answer.agrees_count
        return total_agrees

    def followers_count(self):
        followers = UserOnUser.query.filter_by(followed_id=self.id).all()
        return len(followers)

    def followed_count(self):
        followed = UserOnUser.query.filter_by(follower_id=self.id).all()
        return len(followed)

    def follow_user(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f is None:
            f = UserOnUser(follower=self, followed=user)
        elif f.follow == False:
            f.follow = True
        db.session.add(f)

    def unfollow_user(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            f.follow = False
            db.session.add(f)

    def follow_question(self, question):
        f = self.user_on_question.filter_by(question_id=question.id).first()
        if f is None:
            f = UserOnQuestion(user=self, question=question)
        elif f.follow == False:
            f.follow = True
        db.session.add(f)

    def unfollow_question(self, question):
        f = self.user_on_question.filter_by(question_id=question.id).first()
        if f:
            f.follow = False
            db.session.add(f)

    def questions_count(self):
        questions = Question.query.filter_by(user_id=self.id).all()
        return len(questions)

    def answers_count(self):
        answers = Answer.query.filter_by(author_id=self.id).all()
        return len(answers)

    def get_feeds(self):
        total_feeds = []
        followed = UserOnUser.query.filter_by(follower_id=self.id).all()
        if followed is not None:
            for j in followed:
                feeds = Feed.query.filter_by(user_id=j.followed_id).all()
                for k in feeds:
                    total_feeds.append(k)
        sorted_feeds = sorted(total_feeds, key=operator.attrgetter('timestamp'))
        return sorted_feeds

    def can_modify_answer(self, answer):
        return answer.author_id == self.id

    def have_an_answer(self, question):
        answer = question.answers.filter_by(author_id=self.id).first()
        if answer is not None:
            return True
        else:
            return False

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can_modify_answer(self, answer):
        return False

    def have_an_answer(self, question):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True, default=19550225)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    create_time = db.Column(db.DateTime(), default=datetime.now)
    answers = db.relationship('Answer', backref='question', lazy='dynamic')
    topics = db.relationship('Topic', backref='question', lazy='dynamic')
    comments = db.relationship('Comment', backref='question', lazy='dynamic')
    user_on_question = db.relationship('UserOnQuestion', backref='question', lazy='dynamic')
    feeds = db.relationship('Feed', backref='question', lazy='dynamic')
    logs = db.relationship('QuestionLog', backref='question', lazy='dynamic')

    def answers_count(self):
        return len(self.answers.all())

    def followers_count(self):
        return len(self.user_on_question.all())

    def comments_count(self):
        return len(self.comments.all())

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
            target.content_html = markdown(value, output_format='html')


db.event.listen(Question.content, 'set', Question.on_changed_body)


class QuestionLog(db.Model):
    __tablename__ = 'question_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    action = db.Column(db.String(64))
    reason = db.Column(db.Text)
    update_time = db.Column(db.DateTime(), default=datetime.now)


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    create_time = db.Column(db.DateTime(), default=datetime.now)
    update_time = db.Column(db.DateTime())
    agrees_count = db.Column(db.Integer, default=0)
    disagrees_count = db.Column(db.Integer, default=0)
    score = agrees_count - disagrees_count
    user_on_answer = db.relationship('UserOnAnswer', backref='answer', lazy='dynamic')
    comments = db.relationship('Comment', backref='answer', lazy='dynamic')
    feeds = db.relationship('Feed', backref='answer', lazy='dynamic')

    def get_question(self):
        return Question.query.filter_by(id=self.question_id).first()

    def get_summary(self):
        return ''.join([self.content[:40], '...'])

    def comments_count(self):
        return len(self.comments.all())

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
            target.content_html = markdown(value, output_format='html')


db.event.listen(
    Answer.__table__,
    "after_create",
    DDL("ALTER TABLE answers AUTO_INCREMENT=20160709;")
)
db.event.listen(Answer.content, 'set', Answer.on_changed_body)


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))

    def __repr__(self):
        return '<Topic %r>' % self.name


class UserOnQuestion(db.Model):
    __tablename__ = 'user_on_question'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    follow = db.Column(db.Boolean, default=True)
    follow_timestamp = db.Column(db.DateTime, index=True, default=datetime.now)


class UserOnAnswer(db.Model):
    __tablename__ = 'user_on_answer'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))
    vote = db.Column(db.Integer, default=0)
    vote_up_timestamp = db.Column(db.DateTime())


class Feed(db.Model):
    __tablename__ = 'feeds'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(64))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)

    def display_time(self):
        td = datetime.now() - self.timestamp
        if td.days >= 1:
            return u'%s 天前' % td.days
        elif td.seconds >= 3600:
            return u'%s 小时前' % (td.seconds // 3600)
        elif td.seconds >= 60:
            return u'%s 分钟前' % (td.seconds // 60)
        else:
            return u'%s 秒前' % td.seconds       