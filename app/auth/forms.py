#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Regexp
from wtforms import ValidationError
from ..models import User


class RegistrationForm(Form):
    """新用户注册表单
    @nickname, 昵称, 可以重复
    """
    nickname = StringField(u'姓名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[\w\W\u4e00-\u9fff][\s\w\W\u4e00-\u9fff]*$', 0,
               u'姓名只能包含中文，英文和数字')])
    email = StringField(u'电子邮箱', validators=[DataRequired(),
                        Length(1, 64), Email()])
    password = PasswordField(u'设置密码', validators=[DataRequired()])
    submit = SubmitField(u'注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'此邮箱已被注册')


class LoginForm(Form):
    """用户登录表单
    """
    email = StringField(u'电子邮箱', validators=[DataRequired(),
                        Length(1, 64), Email()])
    password = PasswordField(u'密码', validators=[DataRequired()])
    submit = SubmitField(u'登录')
    remember_me = BooleanField(u'记住我')

    # 验证邮箱是否已被注册
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'此邮箱未注册')
