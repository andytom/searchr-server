"""
    manage.py
    ---------

    A simple script for managing Searchr
"""
import navigator

from app import db
from app.tests.api_v1_tests import *
from app.tests.lib_tests import *


#-----------------------------------------------------------------------------#
# Set up
#-----------------------------------------------------------------------------#
nav = navigator.Navigator(intro="Searchr Manager")


#-----------------------------------------------------------------------------#
# Routes
#-----------------------------------------------------------------------------#
# TODO - Add option to create migrations, upgrade and rollback the DB
@nav.route("Create Database", "Creates the Database")
def create_db():
    navigator.ui.text_info("Trying to create the Database")
    db.create_all()
    navigator.ui.text_success("Database created")


@nav.route("Run Tests", "Run all the Unit Tests")
def run_unit_tests():
    navigator.ui.text_info("Running Unit Tests")
    unittest.main(exit=False)


#-----------------------------------------------------------------------------#
if __name__ == '__main__':
    nav.run()
