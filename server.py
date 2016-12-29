# coding: utf-8

__author__ = 'Orclover'

"""
    个人博客
    ~~~~~~

    基于flask、MongoDB
"""

# DONE
# 1. 发布文章接口 + 页面
# 2. 发布评论接口，包括评论文章，也包括评论评论
# 3. 修改文章详情页面，主要在与子级评论和父级评论的渲染/展示
# 12. 文章内容编辑
# 3. classification的增删改查
# 14. 添加404页面
# 15. 添加日期格式转换
# 16. 使用gunicorn部署，改造server.py结构

# TODO todo-list
# 1. 页面样式与页面风格
# 2. 用户注册与登录(必要性?)
# 4. 文章的搜索功能，根据tags/classification
# 6. 评论文章/评论评论时，应该由jQuery去添加元素，还是将整个的重新加载
# 7. 纯接口，取回数据后，返回HTTP Status 200
# 8. 发布评论时的前后端校验
# 9. 发布文章时的前后端校验
# 10. 使用pygments进行代码高亮显示
# 11. 发布文章时，支持两种格式——富文本编辑/Markdown
# 13. flask-admin中的级联删除/显示问题，如对于评论内容的增删改查等等
# 17. 优化文章类别页面（articles.htm），太丑
# 19. 移动端页面适配
# 20. 必要位置的日志


from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, make_response, Markup, json, Blueprint


# ODM mongoengine
from flask_mongoengine import MongoEngine

import flask_login
from werkzeug.security import generate_password_hash, check_password_hash
# wtforms
from wtforms import form, fields, validators

# 日志模块
import logging.config
from os import path

log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.conf')
logging.config.fileConfig(log_file_path)
# TODO 使用的日志移入配置项，根据不同环境使用不同logger
logger = logging.getLogger("root")

# 分页功能
# TODO 能否通过装饰器实现
from pagination import Pagination
# RSS
from werkzeug.contrib.atom import AtomFeed

# 创建应用
app = Flask(__name__)
# blueprints
# @See: https://segmentfault.com/a/1190000002480266
from blog import blog
app.register_blueprint(blog, url_prefix='/blog')

# 配置获取，本项目使用两种方式：
# 更多，@See: http://www.pythondoc.com/flask/config.html
# http://www.pythondoc.com/flask/patterns/distribute.html#distribute-deployment
# 1. 从配置文件中读取配置
# app.config.from_pyfile('app.conf')
# 2. 从配置对象中读取配置(推荐)
app.config.from_object('app_config.Development')


# 创建数据库实例
db = MongoEngine(app)

# TODO 将beautifulsoup从server.py中摘除，作为单独服务使用
from bs4 import BeautifulSoup

# flask_login相关，考虑从本文件中摘除
# @See:http://flask-login.readthedocs.io/en/latest
# 开始
login_manager = flask_login.LoginManager(app)


@login_manager.user_loader
def user_loader(id):
    '''
    TODO 提示用户不存在，在验证密码前的controller中做
    '''
    from bson import ObjectId

    if not ObjectId.is_valid(id):
        return
    user = User.objects(id=id).first()
    if not user:
        return

    return user


'''
暂时没有用到，request_loader存在的目的是什么？
@login_manager.request_loader
def request_loader(request):
    email = request.form.get('loginid')
    if email not in users:
        return

    user = User()
    user.login_id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['pw'] == users[email]['pw']

    return user
'''


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'


# 结束


# TODO 程序异常时添加处理，如关闭数据库连接等（MongoEngine应该可以自动关闭连接）
@app.teardown_appcontext
def close_db(error):
    # db.close()
    pass


# 页面
# 博客首页
@app.route('/', defaults={'page': 1}, methods=['GET'])
@app.route('/page-<int:page>', methods=['GET'])
def index(page):
    start = (page - 1) * number_per_page
    limit = page * number_per_page
    count = Article.objects.count()
    classifications = Classification.objects.order_by('+name')
    articles = Article.objects.order_by('-create_time')[start:limit]
    pagination = Pagination(page, number_per_page, count)
    # 添加最新发表文章列表，取最新发表的五篇文章
    # TODO 最近文章不需要，因为首页就是按最近发表排序的，可以考虑根据业务切换为其他条件的文章，如热度等
    '''
    recent_articles = Article.objects.order_by('-create_time').limit(5)
    if recent_articles:  # 文章不存在时，不进行转换
        article = recent_articles[0]
        # articles[0].content = Markup(misaka.html(articles[0].content))
        article.content = Markup(misaka.html(article.content))
    '''
    return render_template('index.html', classifications=classifications,
                           articles=articles, recent_articles=None, pagination=pagination)


# 接口
# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login_id = request.form.get('loginid')
        password = request.form.get('password')
        # 1. 使用hashlib.sha256作为摘要算法加密
        # encrypted_password = sha256(password.encode('utf-8')).hexdigest()
        # 2. 使用werkzeug.security中的摘要算法进行加密
        encrypted_password = generate_password_hash(password)
        if User.objects(login_id=login_id):
            # TODO 提示用户已存在
            pass
        User(login_id=login_id, password=encrypted_password).save()
        # return '注册成功', 200
        # TODO 跳转到注册成功页面
        # 如果需要，注册成功后帮助用户自动登录
        return redirect(url_for('index'))

    return render_template('blog.register.html')


# 接口
# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    redirect_uri = request.args.get('redirect_uri')
    action_uri = request.url_rule.rule
    from urllib.parse import quote_plus
    if request.method == 'POST':
        is_remember = request.form.get('remember', False)
        login_id = request.form.get('loginid')
        password = request.form.get('password')

        # 1. 使用hashlib.sha256作为摘要算法加密
        # if sha256(request.form.get('password').encode('utf-8')).hexdigest() == User.objects(login_id=login_id).first().password:
        # 2. 使用werkzeug.security中的摘要算法进行加密
        user = User.objects(login_id=login_id).first()
        if not user:
            error = app.config['USER_NOT_EXISTS']
        elif check_password_hash(user.password, password):
            '''
            user = User()
            user.login_id = login_id
            user.id = login_id
            '''
            # remember参数默认为False，设置为True后可通过Cookie记录用户登录状态
            flask_login.login_user(user, remember=is_remember)
            if redirect_uri:
                return redirect(redirect_uri)
            else:
                return redirect(url_for('index'))
        else:
            error = app.config['PASSWORD_NOT_MATCH']
    # TODO 优化保证URL一致性的代码
    elif request.method == 'GET':
        # 为保证action中的URL一致
        if redirect_uri:
            action_uri += '?redirect_uri=' + quote_plus(redirect_uri)
    # 用户验证错误时，需要对URL做处理
    if error:
        # 三种方式获取query param
        # 通过这三个example可以熟悉下urllib.parse方法
        '''
        from urllib.parse import unquote
        abs_url = unquote(request.url)
        redirect_uri = abs_url[abs_url.index('redirect_uri') + len('redirect_uri='):]
        if redirect_uri:
            action_uri += '?redirect_uri=' + quote(redirect_uri, safe='')
        '''
        '''
        from urllib.parse import unquote, urlparse, urlencode
        abs_url = unquote(request.url)
        redirect_uri = urlencode(parse_qs(urlparse(abs_url).query), doseq=True)
        if redirect_uri:
            action_uri += '?' + redirect_uri
        '''
        from urllib.parse import urlparse
        parse_result = urlparse(request.url)
        query_param = parse_result.query
        if query_param:
            action_uri += '?' + query_param
            # OR
            # action_uri = '?'.join([action_uri, query_param])

    return render_template('login.html', error=error, action_uri=action_uri)


# 接口
# 用户登出
@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for('index'))


# 测试
# 测试用户时候登录成功
@app.route('/protected')
@flask_login.login_required
# 相比于login_required注解，有一种更加严格的注解：fresh_login_required，这种注解要求session是fresh状态（从remember me自动登录时，
# 是non-fresh状态）
def protected():
    return 'Logged in as: ' + flask_login.current_user.login_id


# 页面
# 全部文章列表
@app.route('/articles', defaults={'page': 1}, methods=['GET'])
@app.route('/articles/page-<int:page>', methods=['GET'])
def articles(page):
    # 分页相关
    start = (page - 1) * number_per_page
    limit = start + number_per_page
    tags = request.args.get('tags')
    classification_id = request.args.get('classification')
    classification = None
    if tags and classification_id:
        """ TODO 如何做到精确查询tags（多个）？
        tag_in_db_list = []
        if ',' in tags:
            for tag in tags.split(','):
                tag_in_db_list.append(Tag.objects(name=tag).first().id)
        else:
            tag_in_db_list.append(Tag.objects(name=tags).first().id)
        """
        tag_in_db = Tag.objects(name=tags).first()
        # 多条件查询，使用Q函数进行包装，通过|、&进行或、且操作
        articles = Article.objects(Q(tags=tag_in_db) & Q(classification=classification_id)) \
                       .order_by('-create_time')[start:limit]
        count = Article.objects(Q(tags=tag_in_db) & Q(classification=classification_id)).count()
        classification = Classification.objects(id=classification_id)
    elif tags and not classification_id:
        tag_in_db = Tag.objects(name=tags).first()
        articles = Article.objects(tags=tag_in_db).order_by('-create_time')[start:limit]
        count = Article.objects(tags=tag_in_db).count()
    elif not tags and classification_id:
        articles = Article.objects(classification=classification_id).order_by('-create_time')[start:limit]
        count = Article.objects(classification=classification_id).count()
        classification = Classification.objects(id=classification_id).first()
    else:
        articles = Article.objects.order_by('-create_time')[start:limit]
        count = Article.objects.count()
    page_obj = Pagination(page, number_per_page, count)
    return render_template('articles.html', articles=articles, pagination=page_obj, classification=classification)

# 装饰器
# TODO 方法装饰器 －> 类装饰器（参考flask自身的@app.route）
from decorators import *


# 页面
# 文章详情
# 文章生成目录，方便查看，可以使用goose或html5lib(最终选型：beautifulsoup4，使用lxml做解析)
# TODO 将生成目录功能抽取出来
@app.route('/article/<string:article_id>')
@view_increase_wrapper
def article(article_id):
    logger.info("============================enter article pages===================================")
    article = Article.objects(id=article_id).first()
    # 使用flask.Markup进行转义
    article.content = Markup(markdown_it(article.content))
    # 指定使用lxml解析html，如不指定，默认使用html5lib
    soup = BeautifulSoup(article.content, 'lxml')
    # 为每个<h'x'>标签添加id，以便需要时进行定位
    from re import compile

    a_template = '<a href="#{id}">{value}</a>'
    # 使用collections.OrderedDict，以有序字典存储文章目录及对应缩进数
    from collections import OrderedDict

    article_contents = OrderedDict()
    for index, element in enumerate(soup.find_all(compile('^h[1-9]{1}$'))):
        element['id'] = index
        # 目录及对应缩进数
        article_contents.setdefault(Markup(a_template.format(id=index, value=element.string)),
                                    int(element.name[1:]) - 1)
        # 为每个<h'x'>标签添加permalink图标(¶)
        html_tag_a = soup.new_tag('a', **{'class': 'headerlink', 'href': '#' + str(index)})
        html_tag_a.string = '¶'
        element.append(html_tag_a)

    # 将修饰过到内容转换回来
    soup_string = str(soup.body.contents)
    # 去除转换过程中生成的的多余换行符 TODO 查看beautifulsoup API文档，能否在转换过程中不生成多余字符
    # article.content = Markup(soup_string[1:len(soup_string) - 1].replace(r", '\n\n',", "").replace(r", '\n'", ""))
    article.content = Markup(soup_string[1:len(soup_string) - 1].replace(r", '\n',", "").replace(r", '\n'", ""))
    # 是否需要按层级缩进显示目录
    need_indent = len({value for value in article_contents.values()}) != 1

    return render_template('article.html', article=article, mode='release',
                           article_contents=article_contents, need_indent=need_indent)


# 页面
# 关于我
@app.route('/about', methods=['GET'])
def about_me():
    return render_template('aboutme.html')


# 接口
# 发表评论
@app.route('/comment', methods=['POST'])
def comment_post():
    """
    # 通过request.get_json()获取JSON数据
    # ==========
    # get_json中必须有非空参数，为什么？因为——
    By default this function will return ``None`` if the mimetype is not
    :mimetype:`application/json` but this can be overridden by the
    ``force`` parameter.
    # ==========
    """
    data = request.get_json(force=True)
    user = User(name=data.get('username'), email=data.get('useremail'), link=data.get('userlink'),
                login_id='default_login_id', password='default_password').save()
    if data.get('parent_id'):
        parent_comment = Comment.objects(id=data.get('parent_id')).first()
        comment = Comment(content=data.get('content'), display_flag=app.config['DEFAULT_DISPLAY_FLAG'], user_info=user,
                          parent_comment=parent_comment).save()  # .save(cascade=True)
        parent_comment.sub_comments.append(comment)
        parent_comment.save(cascade=True)
    else:
        article = Article.objects(id=data.get('article_id')).first()
        comment = Comment(content=data.get('content'), display_flag=app.config['DEFAULT_DISPLAY_FLAG'],
                          user_info=user).save()  # cascade=True
        article.comments.append(comment)
        article.save()
    return make_response('评论成功', 200)


# 接口
# 删除评论
@app.route('/comment/<string:comment_id>', methods=['DELETE'])
def comment_delete(comment_id):
    Comment.objects(id=comment_id).first().delete()
    return make_response('', 200)


# 接口
# 删除文章
@app.route('/article/<string:article_id>', methods=['DELETE'])
def article_delete(article_id):
    Article.objects(id=article_id).first().delete()
    return make_response('', 200)


# 接口
# 发布/保存文章
@app.route('/article', methods=['POST', 'GET'])
def article_post():
    # 获取表单数据
    id = request.form.get('id')
    title = request.form.get('title')
    tags = request.form.get('tags')
    classification_id = request.form.get('classification')
    abstract = request.form.get('abstract')
    # 保存数据库时，不保存HTML格式文本；在读取后，显示前，做HTML格式处理
    content = request.form.get('content')

    '''
    移除文章中的Tags字段
    tag_doc = []
    if ',' in tags:
        for tag in tags.split(','):
            tag_doc.append(Tag(name=tag).save())
    else:
        tag_doc.append(Tag(name=tags).save())
    '''
    classification_doc = Classification.objects(id=classification_id).first()

    if not id:
        article_posted = Article(title=title, classification=classification_doc, abstract=abstract,
                                 content=content).save()
        return url_for('article', article_post.id)
    else:
        Article.objects(id=id).update_one(title=title,
                                          classification=classification_doc, abstract=abstract,
                                          content=content)
        """
        article_putted.title = title
        article_putted.tags = tag_doc
        article_putted.classification = classification_doc
        article_putted.abstract = abstract
        article_putted.content = content
        article_putted.reload()
        """
        return url_for('article', id)


# 接口
# 获取评论
@app.route('/comments/<string:article_id>')
def comments_corr_article(article_id):
    # comments = Article.objects(id=article_id)  # .only('comments')
    comments = Article.objects(id=article_id).only('comments').first().comments
    # TODO to_json()报错
    comments.to_json()
    for comment in comments:
        comment['user_info'] = User.objects(id=comment.user_info.id).first()
    return json.dumps(comments)


# 接口
# 搜索
@app.route('/search', methods=['POST'])
def search():
    if request.method != 'POST':
        return redirect(url_for('index'))
    query_condition = request.form.get('query', None)
    if query_condition:
        return redirect(url_for('results', query_condition=query_condition))
    else:
        return redirect(url_for('index'))


# 页面
# 搜索结果
@app.route('/q/<string:query_condition>', defaults={'page': 1})
@app.route('/q/<string:query_condition>/page-<int:page>')
def results(query_condition, page):
    # 按文章题目搜索
    # @See: http://docs.mongoengine.org/guide/querying.html#limiting-and-skipping-results
    start = (page - 1) * number_per_page
    limit = page * number_per_page
    articles = Article.objects(title__contains=query_condition).order_by('-create_time')[start:limit]
    count = Article.objects(title__contains=query_condition).count()
    page_obj = Pagination(page, number_per_page, count)
    return render_template('results.html', articles=articles, pagination=page_obj)


# 接口
# RSS
@app.route('/rss')
def rss():
    feed = AtomFeed('IT技术博客', feed_url=request.url, url=request.url_root)
    articles = Article.objects.order_by('-create_time')  # 将全部文章检出，而不只检出第一页 [0:number_per_page]
    # python3中，已将urlparse.urljoin合并入urllib包中，变为urllib.parse.urljoin
    from urllib.parse import urljoin

    for article in articles:
        feed.add(article.title, markdown_it(article.content), content_type='html',
                 author='博客老板', url=urljoin(request.url_root, url_for('article', article_id=article.id)),
                 updated=article.create_time)
    return feed.get_response()


# 404页面
@app.errorhandler(404)
def page_not_found(error):
    return make_response(render_template('404.html', title='404'), 404)


# 自定义模板过滤器
# 处理时间格式
@app.template_filter('format_date')
def format_datetime_filter(input_value, _format='%Y-%m-%d %H:%M:%S'):
    if hasattr(input_value, 'strftime'):
        return input_value.strftime(_format)
    return input_value


# 统一处理request，相当于postHandler，可以看下源代码
# @See: http://www.tuicool.com/articles/YBbeM33
@app.after_request
def app_after_request(response):
    # 为静态资源添加缓存
    if request.endpoint != 'static':
        return response
    response.cache_control.max_age = 1200  # 'no-cache'
    # 直接通过这种方式制定的expire无效
    # response.expire = 'Fri, 31 Dec 1999 16:00:00 GMT'
    # 有效
    # response.headers['Expire'] = 'Fri, 31 Dec 1999 16:00:00 GMT'
    # response.headers['Cache-Control'] = 'no-cache'
    return response


# 分页URL生成方法
# 通过@app.template_global将该方法注册到jinja模板中
@app.template_global('url_for_other_pages')
def url_for_other_pages(page):
    """
    两种类型的参数：
    request.view_args   REST风格的参数
    request.args        query parameter风格的参数
    由于本博客未统一使用某种风格，因此两种参数均需带上
    """
    view_args = request.view_args.copy()
    view_args['page'] = page
    for k, v in request.args.items():
        view_args[k] = v
    return url_for(request.endpoint, **view_args)

# flask-admin相关
# 开始
from flask_admin_server import *

# 初始化flask-admin
def create_flask_admin():
    import flask_admin

    admin_instance = flask_admin.Admin(app, name='博客管理后台', template_mode='bootstrap3',
                                       index_view=CustomizedAdminIndexView(),
                                       base_template='customized_master.html')
    admin_instance.add_view(UserView(User, name="用户管理"))
    admin_instance.add_view(ClassificationView(Classification, name="分类管理"))
    admin_instance.add_view(ArticleView(Article, name="文章管理"))
    admin_instance.add_view(CommentView(Comment, name="评论管理"))
    return admin_instance


admin = create_flask_admin()
# 结束


# markdown处理
def markdown_it(content):
    if content:
        import misaka
        # about extents, @See: http://misaka.61924.nl/#extensions
        return misaka.html(content, extensions=('tables', ))
    else:
        raise ValueError('content param is None.')


# 分页页面中，每页显示的数据条
number_per_page = app.config['NUMBER_PER_PAGE']

# 启动服务
# 在使用gunicorn作为应用服务器启动时，该判断为false，if中的语句不执行
if __name__ == '__main__':
    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
