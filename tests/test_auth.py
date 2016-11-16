# -*- coding: utf-8 -*-

import unittest
from urlparse import urlparse
from flask import url_for
from app import create_app, db
from app.models import User


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get(url_for('main.index'))
        self.assertEqual(
            urlparse(response.location).path, url_for('auth.login'))

    def test_register_and_login(self):
        # register a new account
        response = self.client.post(url_for('auth.register'), data=dict(
            email='jack@example.com',
            nickname='Jack Smith',
            password='cat'
        ), follow_redirects=True)
        user = User.query.filter_by(email='jack@example.com').first()
        self.assertFalse(user is None)

        # login with new account
        response = self.client.post(url_for('auth.login'), data=dict(
            email='jack@example.com',
            password='cat'
        ), follow_redirects=True)
        check_mark = '我的主页'
        self.assertTrue(check_mark in response.get_data())

        # log out
        response = self.client.get(url_for('auth.logout'))
        self.assertEqual(
            urlparse(response.location).path, url_for('auth.login'))

        # register an account with same name
        response = self.client.post(url_for('auth.register'), data=dict(
            email='jack@gmail.com',
            nickname='Jack Smith',
            password='dog'
        ), follow_redirects=True)
        expected_username = 'Jack-Smith-1'
        user = User.query.filter_by(email='jack@gmail.com').first()
        self.assertEqual(user.username, expected_username)
