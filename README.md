# flaskblog

A blog written by python3 and flask, with the [MongoDB](https://www.mongodb.com/) as the backend database.



## Usage

1. clone the source code:

   $ git clone https://github.com/xitongjiagoushi/flaskblog.git

   $ cd flaskblog

2. checkout to the 'nologin' branch:

   $ git checkout nologin

3. create and activate python virtual environment(optional):

   $ pyvenv virtualenv_3.5

   $ source virtualenv_3.5/bin/activate

4. install requirements:

   $ pip install -r requirements.txt

5. run MongoDB(omitted here), create the database, and adjust the configuration:

   $ mongorestore -d flaskblog db/

   $ vim/nano/emacs app_config.py

6. run the web application:

   $ python server.py

7. browse use curl or in the browser(default url is http://127.0.0.1:5000/):

   $ curl http://127.0.0.1:5000/


## Any problems

[mail to me](mailto:root@brctl.com)
