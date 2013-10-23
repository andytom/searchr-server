import unittest
import json

from app import app, db
from app.model.document import Document
from app.model.tag import Tag
from app import lib


#-----------------------------------------------------------------------------#
class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://' 
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
        with self.assertRaises(ValueError, msg="Test Name is longer than 10 characters (11)"):
            lib.string_length(maximum=10)(u'a' * 11, u'Test Name')

    def test_test_string_validator_min_length(self):
        with self.assertRaises(ValueError, msg="Test Name is less than 2 characters (1)"):
            lib.string_length(minimum=2)(u'a', u'Test Name')

    def test_string_length_validator_type(self):
        with self.assertRaises(ValueError, msg="Test Name needs to be a string"):
            lib.string_length(maximum=256)(1, u'Test Name')

    def test_tag_list_validator_with_valid(self):
        self._add_default_tag()
        res = lib.tag_list([1], u'Tag List')
        self.assertEqual(type(res[0]), Tag)
        self.assertEqual((res[0].id), 1)

    def test_tag_list_validator_with_invalid(self):
        with self.assertRaises(ValueError, msg="1 is not a valid Tag id"):
            res = lib.tag_list([1], u'Tag List')

    def test_tag_list_validator_no_duplicates(self):
        self._add_default_tag()
        res = lib.tag_list([1,1,1], u'Tag List')
        self.assertEqual(len(res), 1)
        self.assertEqual((res[0].id), 1)
        self.assertEqual(type(res[0]), Tag)
