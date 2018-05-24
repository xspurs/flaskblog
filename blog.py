# coding: utf-8

__author__ = 'Orclover'

"""
    使用Blueprint添加静态前缀
"""

from flask import Blueprint

blog = Blueprint('blog', __name__)


@blog.route('/sayhi')
def say_hi():
    return "hello, blog and world."
