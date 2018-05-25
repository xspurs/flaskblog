# flaskblog

[![Build Status](https://travis-ci.org/xspurs/flaskblog.svg?branch=master)](https://travis-ci.org/xspurs/flaskblog) [![Coveage](https://img.shields.io/codecov/c/github/xspurs/flaskblog/master.svg)](https://codecov.io/gh/xspurs/flaskblog)

A blog written by python3 and flask, with the [MongoDB](https://www.mongodb.com/) as the backend database.

## Usage

1\. clone the source code:

```shell
$ git clone https://github.com/xitongjiagoushi/flaskblog.git
$ cd flaskblog
```

2\. create and activate python virtual environment(optional):

```shell
$ pyvenv virtualenv_3.5
$ source virtualenv_3.5/bin/activate
```

3\. install requirements:

```shell
$ pip install -r requirements.txt
```

4\. run MongoDB(omitted here), create the database, and adjust the configuration:

```shell
$ mongorestore -d flaskblog db/
$ vim/nano/emacs app_config.py
```

adjust MongoDB connection configuration:

```python
# mongodb connection configuration
MONGODB_DB = 'flaskblog'
MONGODB_HOST = '127.0.0.1'
MONGODB_PORT = 27017
```

5\. run the web application:

```shell 
$ python server.py
```

6\. browse use curl or in the browser(default url is http://127.0.0.1:5000/):

```shell
$ curl http://127.0.0.1:5000/
```

## Tech used

- [Flask](http://flask.pocoo.org/): a microframework for Python based on Werkzeug, Jinja 2 and good intentions.
- [Vue.js](https://vuejs.org/): the progressive JavaScript framework.
- [jQuery](https://jquery.com/): a fast, small, and feature-rich JavaScript library.
- [MongoDB](https://www.mongodb.com/): an open-source document database that provides high performance, high availability, and automatic scaling.
- [MongoEngine](http://mongoengine.org/): a Document-Object Mapper (think ORM, but for document databases) for working with MongoDB from Python.
- [Bootstrap](https://getbootstrap.com/): an open source toolkit for developing with HTML, CSS, and JS.
- [NicEdit](http://www.nicedit.com/): a Lightweight, Cross Platform, Inline Content Editor to allow easy editing of web site content on the fly in the browser.

## TODO List

- [ ] Comment module
- [ ] Screening conditions for blog
- [ ] Customize admin manage console
- [ ] Unit test
- [ ] Code tuning

## Any problems

[mail to me](mailto:root@brctl.com)
