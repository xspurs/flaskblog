# flaskblog

A blog written by python3 and flask, with the [MongoDB](https://www.mongodb.com/) as the backend database.



## Usage

1\. clone the source code:

```shell
$ git clone https://github.com/xitongjiagoushi/flaskblog.git
$ cd flaskblog
```

2\. checkout to the 'nologin' branch:

```shell
$ git checkout nologin
```

3\. create and activate python virtual environment(optional):

```shell
$ pyvenv virtualenv_3.5
$ source virtualenv_3.5/bin/activate
```

4\. install requirements:

```shell
$ pip install -r requirements.txt
```

5\. run MongoDB(omitted here), create the database, and adjust the configuration:

```shell
$ mongorestore -d flaskblog db/
$ vim/nano/emacs app_config.py
```

6\. run the web application:

```shell 
$ python server.py
```

7\. browse use curl or in the browser(default url is http://127.0.0.1:5000/):

```shell
$ curl http://127.0.0.1:5000/
```



## TODO List

- [ ] Comment module
- [ ] Screening conditions for blog
- [ ] Customize admin manage console
- [ ] Unit test
- [ ] Code tuning

## Any problems

[mail to me](mailto:root@brctl.com)
