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
    is_jieba = mongoengine.BooleanField(default=False)
    top_key = mongoengine.ListField(default=[])

    meta = {'db_alias': 't66y', 'indexes': ['url']}

    @classmethod
    def get_day_item_sum(cls):
        """统计每天的数量"""
        pipline = [{
            '$group': {
                '_id': '$post_date',
                'sum': {
                    '$sum': 1
                }
            }
        }, {
            '$sort': {
                '_id': -1
            }
        }]
        data = list(Articles.objects().aggregate(*pipline))
        print(data)


if __name__ == "__main__":
    Articles.get_day_item_sum()
