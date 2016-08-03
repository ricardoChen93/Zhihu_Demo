#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask_wtf import Form
from wtforms import TextAreaField, SubmitField, \
	BooleanField
from wtforms.validators import DataRequired, Length


class AddQuestionForm(Form):
    title = TextAreaField(u'问题', validators=[DataRequired(), Length(1, 128)])
    content = TextAreaField(u'问题说明')
    submit = SubmitField(u'发布')


class AddAnswerForm(Form):
	content = TextAreaField(u'回答', validators=[DataRequired()])
	submit = SubmitField(u'发布回答')