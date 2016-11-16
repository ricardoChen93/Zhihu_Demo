#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

import cPickle as pk
from html2text import html2text
from random import choice, randint
from app import create_app, db
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand
from app.models import User, Question, Answer, Topic, Feed
from app.auth.views import create_username


app = create_app(os.getenv('ZHIHU_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Question=Question,
                Answer=Answer, Topic=Topic, Feed=Feed)

manager.add_command('run', Server())
manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_context=make_shell_context))


# 添加test命令来运行coverage
@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file//%s/index.html' % covdir)
        COV.erase()


# 初次添加数据，已弃用，请使用initial.sql
@manager.command
def deploy():
    db.drop_all()
    db.create_all()

    users = [('admin@example.com', u'知乎小管家', 'password'),
             ('jack@example.com', u'Jack', 'password'),
             ('jim@example.com', u'Jim', 'password'),
             ('vip@qq.com', u'麻花疼', 'password'),
             ('vip@163.com', u'丁磊', 'password'),
             ('zjw@example.com', u'张家玮', 'password'),
             ('lkf@example.com', u'李开复', 'password'),
             ('zxb@example.com', u'张小北', 'password'),
             ('ct@example.com', u'采铜', 'password'),
             ('zl@example.com', u'张亮', 'password'),
             ('zxn@example.com', u'周晓农', 'password'),
             ('ln@example.com', u'李楠', 'password'),
             ('mby@example.com', u'马伯庸', 'password'),
             ('xdr@example.com', u'笑道人', 'password'),
             ('xxmj@example.com', u'谢熊猫君', 'password')]
    for user in users:
        u = User(email=user[0],
                 nickname=user[1],
                 password=user[2])
        u.username = create_username(u.nickname)
        db.session.add(u)
    db.session.commit()

    users = User.query.all()
    for user in users:
        other_users = users[:]
        other_users.remove(user)
        user2 = choice(other_users)
        user.follow_user(user2)
    db.session.commit()

    with open('zhihu_questions.pk', 'rb') as f:
        infos = pk.load(f)
    users = User.query.all()
    i = 0
    while i < len(infos):
        q_html = infos[i]['detail']
        title = infos[i]['title']
        try:
            if i == 0:
                question = Question(user=users[0], title=title,
                                    content=html2text(q_html),
                                    content_html=q_html)
                db.session.add(question)
                db.session.commit
                a_html = infos[i]['answers'][0]
                answer = Answer(author=users[0], question=question,
                                content=html2text(a_html),
                                content_html=a_html)
                db.session.add(answer)
                db.session.commit()
                feed1 = Feed(user=users[0],
                             action="ask_question",
                             question=question)
                feed2 = Feed(user=users[0],
                             action="answer_question",
                             question=question,
                             answer=answer)
                db.session.add_all([feed1, feed2])
                db.session.commit()
            else:
                q_html = infos[i]['detail']
                title = infos[i]['title']
                prev_question = Question.query.order_by(
                    Question.id.desc()).first()
                id_plus = randint(1, 4)
                question_id = prev_question.id + id_plus
                asker = choice(users)
                question = Question(id=question_id, user=asker, title=title,
                                    content=html2text(q_html),
                                    content_html=q_html)
                db.session.add(question)
                db.session.commit()
                feed1 = Feed(user=asker,
                             action="ask_question",
                             question=question)
                db.session.add(feed1)
                db.session.commit()
                answerers = users[:]
                j = 0
                while j < len(infos[i]['answers']):
                    answerer = choice(answerers)
                    a_html = infos[i]['answers'][j]
                    answer = Answer(author=answerer, question=question,
                                    content=html2text(a_html),
                                    content_html=a_html)
                    db.session.add(answer)
                    db.session.commit()
                    feed2 = Feed(user=answerer,
                                 action="answer_question",
                                 question=question,
                                 answer=answer)
                    db.session.add(feed2)
                    db.session.commit()
                    answerers.remove(answerer)
                    j += 1
        except Exception:
            continue
        i += 1
        print(u'第%s个问题已收录' % i)


if __name__ == '__main__':
    manager.run()
