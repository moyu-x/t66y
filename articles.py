import mongoengine

mongoengine.connect('t66y', alias='t66y')


class Articles(mongoengine.Document):
    """Articls，数据保存模型"""
    url = mongoengine.StringField()
    title = mongoengine.StringField()
    author = mongoengine.StringField()
    post_date = mongoengine.StringField()
    content = mongoengine.StringField()
    content_no_tag = mongoengine.StringField()

    meta = {'db_alias': 't66y', 'indexes': ['url']}
