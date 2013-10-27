"""
    manage.py
    ---------

    A simple script for managing Searchr
"""
import navigator
from itertools import chain
import unittest


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
    from app import db
    navigator.ui.text_info("Trying to create the Database")
    db.create_all()
    navigator.ui.text_success("Database created")


@nav.route("Run Tests", "Run all the Unit Tests")
def run_unit_tests():
    navigator.ui.text_info("Running Unit Tests")
    test_list = ['app.tests.lib',
                 'app.tests.api_v1']
    tests = unittest.TestLoader().loadTestsFromNames(test_list)
    results = unittest.TextTestRunner().run(tests)
    if results.wasSuccessful():
        navigator.ui.text_success("All tests passed")


#-----------------------------------------------------------------------------#
if __name__ == '__main__':
    nav.run()
