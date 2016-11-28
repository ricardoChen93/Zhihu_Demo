from flask import render_template, request
from flask_login import current_user
from . import api
from ..models import Feed, Notification


def get_context():
    user = current_user._get_current_object()
    feeds = user.get_feeds()
    count = len(feeds)
    context = {
        'feeds': feeds,
        'count': count
    }
    return context


@api.route('/HomeFeedList/')
def send_feeds(size=5):
    offset = request.args.get('offset', 0, type=int)
    count = request.args.get('count', 5, type=int)
    context = get_context()
    total_feeds = context.get('feeds')[context.get('count')-count:]
    if offset + size <= count:
        feeds = total_feeds[offset:offset+size]
    else:
        feeds = total_feeds[offset:]
    return render_template('_feedItem.html', feeds=feeds)
