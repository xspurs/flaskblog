# coding: utf-8

__author__ = 'Orclover'

from mongoengine import *
import datetime
import flask_login


# 用户对象
# 含有用户基本信息
# TODO 用户身份信息
class User(Document, flask_login.UserMixin):
    # name = StringField(required=True)
    # email = StringField(required=True)
    name = StringField()
    email = StringField()
    link = StringField()
    # 为flask_login添加字段
    login_id = StringField(required=True)
    password = StringField(required=True)
    # 区分用户是普通用户还是管理员用户，没有进行细分
    type = IntField(required=True, default=0)



# 文章类别对象
# 通过文章类别可以查找文章
class Classification(Document):
    name = StringField(required=True)


# 文章标签对象
# 通过标签可以查找文章
class Tag(Document):
    name = StringField(required=True)


"""
class Comment(EmbeddedDocument):
    _id = StringField()
    content = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now())
    display_flag = IntField(required=True, default=1)
    user_info = ReferenceField(User)
    sub_comments = ListField(ReferenceField('self'))
    #sub_comments = ListField(DictField())

    #meta = {'allow_inheritance': True}
"""


# 评论对象
# 含有父级评论ID和子级评论ID
class Comment(Document):
    content = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now())
    display_flag = IntField(required=True, default=1)
    user_info = ReferenceField(User, reverse_delete_rule=CASCADE)
    sub_comments = ListField(ReferenceField('self'))
    parent_comment = ReferenceField('self')
    # 不能在此引用之后声明的实体类
    # parent_article = ReferenceField(Article)

    def clean(self):
        """
        Cleaning is only called if validation is turned on and when calling save().
        """
        pass


# 文章对象
# 含有评论对象ID
class Article(Document):
    title = StringField(required=True)
    abstract = StringField(required=True)
    content = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now())
    display_flag = IntField(required=True, default=1)
    classification = ReferenceField(Classification, reverse_delete_rule=CASCADE)
    view_number = IntField(required=True, default=0)
    tags = ListField(ReferenceField(Tag, reverse_delete_rule=CASCADE))
    comments = ListField(ReferenceField(Comment, reverse_delete_rule=CASCADE))
