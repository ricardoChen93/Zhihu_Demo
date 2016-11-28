# -*- coding: utf-8 -*-
from flask import request, render_template, jsonify
from flask_login import current_user
from . import api
from .. import db
from ..models import Notification, Question


def get_context():
    user = current_user._get_current_object()
    notifications = Notification.query.filter_by(
        tuser_id=user.id).order_by(Notification.timestamp.desc())
    count = notifications.count()
    context = dict(notifications=notifications, count=count)
    return context


@api.route('/notification/nav/')
def recent_notifications(size=10):
    """获取最新消息
    """
    context = get_context()
    not_read_count = context.get('notifications').filter_by(
        read=False).count()
    notis = context.get('notifications').limit(size)
    noti_html = render_notifications(notis)
    return jsonify(noti_html=noti_html, count=context.get('count'),
                   not_read_count=not_read_count)


@api.route('/notification/batch/', methods=['POST'])
def batch_notification():
    """将未读消息改为已读
    """
    context = get_context()
    not_read_notis = context.get('notifications').filter_by(
        read=False)
    for noti in not_read_notis:
        noti.read = True
        db.session.add(noti)
        db.session.commit()
    return 'Successful'


@api.route('/NotificationList/')
def send_notifications(size=5):
    offset = request.args.get('offset', 0, type=int)
    count = request.args.get('count', 5, type=int)
    context = get_context()
    notis = context.get('notifications').offset(
        context.get('count')-count+offset).limit(size)
    return render_notifications(notis)


def render_notifications(notis):
    params = []
    for notification in notis:
        if notification.action != 'follow_user':
            question = Question.query.filter_by(
                id=notification.question_id).first()
            params.append(dict(
                user=notification.user, title=question.title,
                action=notification.action, read=notification.read,
                q_id=notification.question_id, a_id=notification.answer_id))
        else:
            params.append(dict(user=notification.user,
                               read=notification.read,
                               action=notification.action))
    noti_html = render_template('_notiItem.html', params=params)
    return noti_html
