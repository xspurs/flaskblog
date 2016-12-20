# coding: utf-8

__author__ = 'Orclover'

'''
configuration object
use objects which extends Config object to customize configurations
'''

# base configuration
class Config(object):
    # flask configuration
    DEBUG = True
    TESTING = True
    SECRET_KEY = 'development key'

    # mongoengine configuration
    MONGODB_DB = 'flaskblog'
    MONGODB_HOST = '127.0.0.1'
    MONGODB_PORT = 27017

    # service host and port configuration
    APP_HOST = '127.0.0.1'
    APP_PORT = 5000

    # flask-login remember me configuration
    import datetime
    REMEMBER_COOKIE_NAME = 'remember_token'
    REMEMBER_COOKIE_DURATION = datetime.timedelta(days=30)
    REMEMBER_COOKIE_DOMAIN = None
    REMEMBER_COOKIE_PATH = '/'
    REMEMBER_COOKIE_SECURE = None
    REMEMBER_COOKIE_HTTPONLY = True

    # constants
    # page configuration
    NUMBER_PER_PAGE = 5
    DEFAULT_DISPLAY_FLAG = 1
    # user not exists prompt
    USER_NOT_EXISTS = '用户不存在'
    # password mismatch prompt
    PASSWORD_NOT_MATCH = '密码错误'


# development environment's configuraion
class Development(Config):
    DEBUG = True


# production environment's configuration
class Production(Config):
    DEBUG = False
