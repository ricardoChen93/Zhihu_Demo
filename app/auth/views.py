#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, \
    login_required
from wtforms import ValidationError
from pypinyin import lazy_pinyin
from . import auth
from .. import db
from ..models import User
from .forms import RegistrationForm, LoginForm


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    nickname=form.nickname.data,
                    password=form.password.data)
        user.username = create_username(user.nickname)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


# 新用户标识名生成
def create_username(nickname):
    char = lazy_pinyin(re.split(r'\s+', nickname))
    username = '-'.join(char)
    user = User.query.filter_by(username=username).first()
    suffix = 1
    while user is not None:
        if suffix != 1:
            char.pop()
        char.append(str(suffix))
        username = '-'.join(char)
        user = User.query.filter_by(username=username).first()
        suffix += 1
    return username
