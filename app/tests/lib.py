import json
import os
import unittest

from app import app, db
from app.model.document import Document
from app.model.tag import Tag
from app import lib


#-----------------------------------------------------------------------------#
class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://' 
        app.config['INDEX_QUEUE'] = 'test_index'
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def _add_default_doc(self):
        doc = Document(u"Test Title", u"Test Text")
        db.session.add(doc)
        db.session.commit()

    def _add_default_tag(self):
        tag = Tag(u"Test Title", u"Test Description")
        db.session.add(tag)
        db.session.commit()


#-----------------------------------------------------------------------------#
class LibTestCase(BaseTestCase):
    def test_test_string_validator_max_length(self):
        with self.assertRaises(ValueError) as cm:
            lib.string_length(maximum=10)(u'a' * 11, u'Test Name')
        self.assertEqual(cm.exception.message, "Test Name is longer than 10 characters (11)")

    def test_test_string_validator_min_length(self):
        with self.assertRaises(ValueError) as cm:
            lib.string_length(minimum=2)(u'a', u'Test Name')
        self.assertEqual(cm.exception.message, "Test Name is less than 2 characters (1)")

    def test_test_string_validator_min_and_max_length_too_short(self):
        with self.assertRaises(ValueError) as cm:
            lib.string_length(minimum=2, maximum=10)(u'a', u'Test Name')
        self.assertEqual(cm.exception.message, "Test Name is less than 2 characters (1)")

    def test_test_string_validator_min_and_max_length_too_long(self):
        with self.assertRaises(ValueError) as cm:
            lib.string_length(minimum=2, maximum=10)(u'a' * 11, u'Test Name')
        self.assertEqual(cm.exception.message, "Test Name is longer than 10 characters (11)")

    def test_string_length_validator_type(self):
        with self.assertRaises(ValueError) as cm:
            lib.string_length(maximum=256)(1, u'Test Name')
        self.assertEqual(cm.exception.message, "Test Name needs to be a string")

    def test_tag_list_validator_with_valid(self):
        self._add_default_tag()
        res = lib.tag_list([1], u'Tag List')
        self.assertEqual(type(res[0]), Tag)
        self.assertEqual((res[0].id), 1)

    def test_tag_list_validator_with_invalid(self):
        with self.assertRaises(ValueError) as cm:
            res = lib.tag_list([1], u'Tag List')
        self.assertEqual(cm.exception.message, "1 is not a valid Tag id")

    def test_tag_list_validator_with_mix(self):
        self._add_default_tag()
        with self.assertRaises(ValueError) as cm:
            res = lib.tag_list([1,2], u'Tag List')
        self.assertEqual(cm.exception.message, "2 is not a valid Tag id")

    def test_tag_list_validator_empty_list(self):
        res = lib.tag_list([], u'Tag List')
        self.assertEqual(len(res), 0)

    def test_tag_list_validator_no_duplicates(self):
        self._add_default_tag()
        res = lib.tag_list([1,1,1], u'Tag List')
        self.assertEqual(len(res), 1)
        self.assertEqual((res[0].id), 1)
        self.assertEqual(type(res[0]), Tag)

    def test_ensure_dir(self):
        test_dir = "/tmp/searchr/test"
        self.assertFalse(os.path.exists(test_dir))
        lib.ensure_dir(test_dir)
        self.assertTrue(os.path.exists(test_dir))
        os.rmdir(test_dir)
