# -*- coding: utf-8 -*-

import re
import time
import random
import multiprocessing
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import create_app, db
from app.models import User, Question


class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # start Firefox
        try:
            cls.client = webdriver.Firefox()
        except:
            pass

        # skip these tests if the browser could not be started
        if cls.client:
            # create the application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # suppress logging to keep unittest output clean
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel('ERROR')

            # create the database
            db.create_all()
            User.generate_fake(10)
            Question.generate_fake(20)

            # add a new user
            from app.auth.views import create_username
            username = create_username('Jack Smith')
            user = User(email='jack@example.com',
                        nickname='Jack Smith',
                        username=username,
                        password='cat')
            db.session.add(user)
            db.session.commit()

            # start the Flask server in a thread
            #cls.thread = threading.Thread(target=cls.app.run)
            cls.process = multiprocessing.Process(target=cls.app.run)
            cls.process.start()

            # give the server a second to ensure it is up
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # stop the flask server and the browser
            # cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()

            # destory database
            db.drop_all()
            db.session.remove()

            # remove application context
            cls.app_context.pop()

            # stop the Flask server
            cls.process.terminate()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_profile_page(self):
        # navigate to index page and redirect to login page
        self.client.get('http://localhost:5000/')
        self.assertEqual(self.client.current_url,
                         'http://localhost:5000/auth/login')

        # login
        self.client.find_element_by_name('email').\
            send_keys('jack@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_id('submit').click()
        try:
            WebDriverWait(self.client, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'name'))
            )
        finally:
            self.assertTrue('Jack Smith' in self.client.page_source)

        # navigate to profile page
        time.sleep(5)
        self.client.find_element_by_class_name('top-nav-userinfo').click()
        edit_button = WebDriverWait(self.client, 15).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, '.profile-header-info-list'))
        )
        self.assertFalse(edit_button is None)
        time.sleep(2)

    def test_question_page(self):
        # login
        self.client.get('http://localhost:5000/auth/login')
        self.client.find_element_by_name('email').\
            send_keys('jack@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_id('submit').click()

        # navigate to a question page
        time.sleep(2)
        self.client.find_element_by_id('explore').click()
        question_links = WebDriverWait(self.client, 10).until(
            EC.presence_of_all_elements_located((
                By.CLASS_NAME, 'question_link'))
        )
        random.choice(question_links).click()

        # follow the question
        WebDriverWait(self.client, 10).until(
            lambda c: len(c.window_handles) == 2)
        self.client.switch_to_window(self.client.window_handles[-1])
        time.sleep(5)
        follow_button = WebDriverWait(self.client, 10).until(
            EC.presence_of_element_located((
                By.XPATH, '//div[@class="side-section"]/button'))
        )
        follow_button.click()
        time.sleep(5)
        self.assertTrue('btn-white' in follow_button.get_attribute('class'))
