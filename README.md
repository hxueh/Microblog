# Microblog

A simple microblog system.

## Features

* Support basic Markdown.
* Support two factor authentication.
* Almost everything else for a simple microblog.

## Requirements

See requirements.txt

## Get started

Creating [virtual environment](https://docs.python.org/3/library/venv.html) is highly recommended.
You should create a database called 'microblog' first in MySQL.

```
export FLASK_APP=application.py
pip install -r requirements.txt

flask shell
Role.insert_roles()

Control + D

flask run
```

Remember to put your secret key and email configuation in your system environments.
e.g.
```
export SECRET_KEY='YourSecretKey'

export GoogleMAIL_SERVER='smtp.googlemail.com'
export GoogleMAIL_PORT='587'
export GoogleMAIL_USE_TLS='true'
export GoogleMAIL_USERNAME='YOUREMAILADDRESS'
export GoogleMAIL_PASSWORD='YOUREMAILPASSWORD'

export SQLALCHEMY_DATABASE_URI=mysql://root@localhost:3306/microblog
```

If you are using another email provider, just modify Mail_Provider in config.py and fit your needs.