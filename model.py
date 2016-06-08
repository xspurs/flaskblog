# coding: utf-8

__author__ = 'Orclover'

from mongoengine import *
import datetime


# 用户对象
# 含有用户基本信息
# TODO 用户身份信息
class User(Document):
    name = StringField(required=True)
    email = StringField(required=True)
    link = StringField()


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
