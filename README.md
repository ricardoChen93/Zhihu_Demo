# Zhihu_Demo
Simple Zhihu Demo By Flask
## Installation
1. Install [pip](https://pip.pypa.io/en/latest/installing/) and [mysql](http://dev.mysql.com/downloads/mysql/)
2. Make a [virtualenv](http://virtualenvwrapper.readthedocs.io/en/latest/#introduction) for this project
3. Install the required dependencies: `pip install -r requirements/dev.txt`
4. Edit config.py: change 'db_user' and 'db_passwd' to your mysql account
5. Initialize data: `mysql -u root -p < initial.sql`

## Run
`python manage.py run`

goto: http://127.0.0.1:5000/
