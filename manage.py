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
    loader = unittest.TestLoader()
    results = unittest.TestResult()
    test_list = ['app.tests.lib',
                 'app.tests.api_v1']
    tests = loader.loadTestsFromNames(test_list)
    tests.run(results)
    navigator.ui.text_info("Ran {} test(s)".format(results.testsRun))
    if results.wasSuccessful():
        navigator.ui.text_success("All tests passed")
    else:
        navigator.ui.text_error("The following test(s) failed")
        for test, traceback in chain(results.errors, results.failures):
           navigator.ui.text_error("Test {}\n{}".format(test, traceback))


#-----------------------------------------------------------------------------#
if __name__ == '__main__':
    nav.run()
