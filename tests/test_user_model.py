import unittest
from flask import url_for
from app import create_app, db
from app.models import User, Question, Answer, UserOnUser, \
    UserOnQuestion, UserOnAnswer


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_follow_user(self):
        # Add two users
        u1 = User(email='jack@example.com', password='cat')
        u2 = User(email='bob@example.com', password='dog')
        db.session.add_all([u1, u2])
        db.session.commit()

        # u1 follow u2
        u1.follow_user(u2)
        user_on_user = UserOnUser.query.filter_by(follower_id=u1.id).first()
        self.assertFalse(user_on_user is None)
        self.assertEqual(u1.followed_count(), 1)
        self.assertEqual(u2.followers_count(), 1)

        # u1 unfollow u2
        u1.unfollow_user(u2)
        self.assertFalse(user_on_user.follow)
        self.assertEqual(u1.followed_count(), 0)
        self.assertEqual(u2.followers_count(), 0)

        # u1 follow u2 again
        u1.follow_user(u2)
        self.assertTrue(user_on_user.follow)
        self.assertEqual(u1.followed_count(), 1)
        self.assertEqual(u2.followers_count(), 1)

    def test_follow_question(self):
        # Add two users
        u1 = User(email='jack@example.com', password='cat')
        u2 = User(email='bob@example.com', password='dog')
        db.session.add_all([u1, u2])
        db.session.commit()

        # u1 add a question
        q = Question(user=u1, title='abc', content='abc')
        self.assertEqual(u1.questions_count(), 1)

        # u2 follow this question
        u2.follow_question(q)
        user_on_question = UserOnQuestion.query.filter(db.and_(
            UserOnQuestion.user == u2,
            UserOnQuestion.question == q)
        ).first()
        self.assertFalse(user_on_question is None)

        # u2 unfollow this question
        u2.unfollow_question(q)
        self.assertFalse(user_on_question.follow)

    def test_answer(self):
        # Add two users
        u1 = User(email='jack@example.com', password='cat')
        u2 = User(email='bob@example.com', password='dog')
        db.session.add_all([u1, u2])
        db.session.commit()

        # u1 add a question
        q = Question(user=u1, title='abc', content='abc')
        self.assertEqual(u1.questions_count(), 1)

        # u2 add an answer to the question
        a = Answer(author=u2, question=q, content='def')
        self.assertEqual(u2.answers_count(), 1)
        self.assertTrue(u2.can_modify_answer(a))
        self.assertTrue(u2.have_an_answer(q))
