# Searchr
Searchr is a simple python full text search system with a restful API.

## Requirements
+ python (Has only been tested on python 2.7)
+ [redis](http://redis.io/)
+ A database of some kind ([sqlite](https://www.sqlite.org/), [mysql](https://www.mysql.com/), [postgresql](http://www.postgresql.org/) etc)
+ [sqlite](https://www.sqlite.org) (for testing)

## Setup

The following instructions are for starting a dev server and assume that you already have python, redis and a database installed.
+ Set up a virtual environment (This assumes you use [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/))
 + `mkvirtualenv searchr`
+ Use pip to install the requirement
 + `pip install -r requirements.txt`
+ Copy `app/config/main.py-sample` to `app/config/main.py` and edit it to have the correct details
+ Use manage.py to set create the database
 + `python mange.py`
+ Start the index script in a separate shell
 + `python index_daemon.py`
+ Start the dev server
 + `python run_dev_server.py`

## Usage

## TODO
+ Write docs for API users
+ Add/improve doctrings
+ Write more/improve tests
+ The index deamon should be a deamon
+ Add ability to create migrations, upgrade and rollback the DB
+ Add Authentication
