from wtforms import widgets, Field


class TopicListField(Field):
    """话题列表选择, 待添加
    """
    widget = widgets.TextInput()

    def _value(self):
        if self.data:
            return u','.join(self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(',')]
        else:
            self.data = []
