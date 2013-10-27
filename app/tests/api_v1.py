import unittest
import json

from app import app, db
from app.model.document import Document
from app.model.tag import Tag


#-----------------------------------------------------------------------------#
class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://' 
        app.config['INDEX_QUEUE'] = 'test_index'
        self.index_dir = '/tmp/searchr/test_ix'
        app.config['WHOOSH_INDEX_DIR'] = self.index_dir
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def _index_doc(self, doc):
        ix = Document.get_index(self.index_dir)
        writer = ix.writer()
        writer.update_document(**doc.prepare())
        writer.commit()

    def _add_default_doc(self):
        doc = Document(u"Test Title", u"Test Text")
        db.session.add(doc)
        db.session.commit()
        return doc

    def _add_default_tag(self):
        tag = Tag(u"Test Title", u"Test Description")
        db.session.add(tag)
        db.session.commit()
        return tag


#-----------------------------------------------------------------------------#
class DocumentAPITestCase(BaseTestCase):
    def test_get_document_with_empty_db(self):
        rv = self.app.get(u'/api/v1.0/document/1')
        self.assertEqual(rv.status_code, 404)

    def test_get_document(self):
        self._add_default_doc()
        rv = self.app.get(u'/api/v1.0/document/1')
        rv_json = json.loads(rv.data)
        self.assertEqual(rv_json[u'title'], u'Test Title')
        self.assertEqual(rv_json[u'text'], u'Test Text')

    def test_add_document_with_id(self):
        data = {u"title": u"Test Title", u"text": u"Test Text"}
        rv = self.app.post(u'/api/v1.0/document/1', data=json.dumps(data),
                           content_type=u'application/json')
        rv_json = json.loads(rv.data)
        # Check the return values are ok
        self.assertEqual(rv_json[u'title'], u"Test Title")
        self.assertEqual(rv_json[u'text'], u"Test Text")
        self.assertEqual(rv_json[u'uri'], u"/api/v1.0/document/1")
        # Check the DB values are ok
        doc = Document.query.get(1)
        self.assertTrue(doc)
        self.assertEqual(doc.title, u"Test Title")
        self.assertEqual(doc.text, u"Test Text")
        
    def test_update_document(self):
        self._add_default_doc()
        updated_data = {u"title": u"Test Update Title", 
                        u"text": u"Test Update Text"}
        rv = self.app.put(u'/api/v1.0/document/1',
                          data=json.dumps(updated_data),
                          content_type=u'application/json')
        rv_json = json.loads(rv.data)
        # Check the return values are ok
        self.assertEqual(rv_json[u'title'], u"Test Update Title")
        self.assertEqual(rv_json[u'text'], u"Test Update Text")
        self.assertEqual(rv_json[u'uri'], u"/api/v1.0/document/1")
        # Check the DB values are ok
        doc = Document.query.get(1)
        self.assertTrue(doc)
        self.assertEqual(doc.title, u"Test Update Title")
        self.assertEqual(doc.text, u"Test Update Text")

    def test_delete_document(self):
        self._add_default_doc()
        rv = self.app.delete(u'/api/v1.0/document/1')
        rv_json = json.loads(rv.data)
        # Check the return values are ok
        self.assertEqual(rv_json[u'message'], u"Document 1 has been deleted")
        # Check the DB values are ok
        doc = Document.query.get(1)
        self.assertTrue(doc.deleted)


#-----------------------------------------------------------------------------#
class DocumentTagAPITestCase(BaseTestCase):
    def test_delete_tag_from_document(self):
        doc = self._add_default_doc()
        tag = self._add_default_tag()
        doc.tags.append(tag)
        db.session.commit()
        # Check the return values are ok
        rv = self.app.delete(u'/api/v1.0/document/1/tag/1')
        rv_json = json.loads(rv.data)
        self.assertEqual(len(rv_json[u'tags']), 0)
        # Check the DB values are ok
        doc = Document.query.get(1)
        self.assertTrue(doc)
        self.assertEqual(len(doc.tags), 0)

    def test_add_tag_to_document(self):
        self._add_default_doc()
        self._add_default_tag()
        rv = self.app.post(u'/api/v1.0/document/1/tag/1')
        rv_json = json.loads(rv.data)
        # Check the return values are ok
        self.assertEqual(len(rv_json[u'tags']), 1)
        self.assertEqual(rv_json[u'tags'][0][u'id'], 1)
        # Check the DB values are ok
        doc = Document.query.get(1)
        self.assertTrue(doc)
        self.assertEqual(len(doc.tags), 1)
        self.assertEqual(doc.tags[0].id, 1)


#-----------------------------------------------------------------------------#
class DocumentListAPITestCase(BaseTestCase):
    def test_get_document_with_empty_db(self):
        rv = self.app.get(u'/api/v1.0/document')
        rv_json = json.loads(rv.data)
        self.assertEqual(rv_json[u'meta'][u'per_page'], 25)
        self.assertEqual(rv_json[u'meta'][u'total'], 0)
        self.assertEqual(rv_json[u'meta'][u'pages'], 0)
        self.assertEqual(rv_json[u'meta'][u'page'], 1)

    def test_get_document_with_document(self):
        self._add_default_doc()
        rv = self.app.get(u'/api/v1.0/document')
        rv_json = json.loads(rv.data)
        self.assertEqual(rv_json[u'meta'][u'per_page'], 25)
        self.assertEqual(rv_json[u'meta'][u'total'], 1)
        self.assertEqual(rv_json[u'meta'][u'pages'], 1)
        self.assertEqual(rv_json[u'meta'][u'page'], 1)
        self.assertEqual(rv_json[u'results'][0][u'title'], u"Test Title")

    def test_post_document_no_tags(self):
        data = {u"title": u"Test Title", u"text": u"Test Text"}
        rv = self.app.post(u'/api/v1.0/document', data=json.dumps(data),
                           content_type=u'application/json')
        rv_json = json.loads(rv.data)
        # Check Return Values
        self.assertEqual(rv_json[u'title'], u"Test Title")
        self.assertEqual(rv_json[u'text'], u"Test Text")
        self.assertEqual(rv_json[u'uri'], u"/api/v1.0/document/1")
        # Check Database Values
        doc = Document.query.get(1)
        self.assertTrue(doc)
        self.assertEqual(doc.title, u"Test Title")
        self.assertEqual(doc.text, u"Test Text")


    def test_post_document_with_tags(self):
        self._add_default_tag()
        data = {u"title": u"Test Title", u"text": u"Test Text", "tags": [1]}
        rv = self.app.post(u'/api/v1.0/document', data=json.dumps(data),
                           content_type=u'application/json')
        rv_json = json.loads(rv.data)
        # Check Return Values
        self.assertEqual(rv_json[u'title'], u"Test Title")
        self.assertEqual(rv_json[u'text'], u"Test Text")
        self.assertEqual(rv_json[u'uri'], u"/api/v1.0/document/1")
        self.assertEqual(rv_json[u'tags'][0][u'id'], 1)
        # Check Database Values
        doc = Document.query.get(1)
        self.assertTrue(doc)
        self.assertEqual(doc.title, u"Test Title")
        self.assertEqual(doc.text, u"Test Text")
        self.assertEqual(len(doc.tags), 1)
        self.assertEqual(doc.tags[0].id, 1)


#-----------------------------------------------------------------------------#
class TagAPITestCase(BaseTestCase):
    def test_get_tag_with_empty_db(self):
        rv = self.app.get(u'/api/v1.0/tag/1')
        self.assertEqual(rv.status_code, 404)

    def test_get_tag(self):
        self._add_default_tag()
        rv = self.app.get(u'/api/v1.0/tag/1')
        rv_json = json.loads(rv.data)
        self.assertEqual(rv_json[u'title'], u'Test Title')
        self.assertEqual(rv_json[u'description'], u'Test Description')

    def test_add_tag_with_id(self):
        data = {u"title": u"Test Title", u"description": u"Test Description"}
        rv = self.app.post(u'/api/v1.0/tag/10', data=json.dumps(data),
                           content_type=u'application/json')
        rv_json = json.loads(rv.data)
        # Check returned Data
        self.assertEqual(rv_json[u'title'], u"Test Title")
        self.assertEqual(rv_json[u'description'], u'Test Description')
        self.assertEqual(rv_json['uri'], "/api/v1.0/tag/10")
        # Check Database Values
        tag = Tag.query.get(10)
        self.assertEqual(tag.title, u"Test Title")
        self.assertEqual(tag.description, u"Test Description")
        
    def test_update_tag(self):
        self._add_default_tag()
        updated_data = {"title": "Test Update Title", 
                        "description": "Test Update"}
        rv = self.app.put('/api/v1.0/tag/1', data=json.dumps(updated_data),
                           content_type='application/json')
        rv_json = json.loads(rv.data)
        # Check returned Data
        self.assertEqual(rv_json['title'], "Test Update Title")
        self.assertEqual(rv_json['description'], "Test Update")
        self.assertEqual(rv_json['uri'], "/api/v1.0/tag/1")
        # Check Database Values
        tag = Tag.query.get(1)
        self.assertEqual(tag.title, u"Test Update Title")
        self.assertEqual(tag.description, u"Test Update")


#-----------------------------------------------------------------------------#
class TagListAPITestCase(BaseTestCase):
    def test_get_tag_with_empty_db(self):
        rv = self.app.get(u'/api/v1.0/tag')
        rv_json = json.loads(rv.data)
        self.assertEqual(rv_json[u'meta'][u'per_page'], 25)
        self.assertEqual(rv_json[u'meta'][u'total'], 0)
        self.assertEqual(rv_json[u'meta'][u'pages'], 0)
        self.assertEqual(rv_json[u'meta'][u'page'], 1)
        self.assertEqual(len(rv_json[u'results']), 0)
    
    def test_post_tag(self):
        data = {u"title": u"Test Title", 
                u"description": u"Test Description"}
        rv = self.app.post(u'/api/v1.0/tag', data=json.dumps(data),
                           content_type=u'application/json')
        rv_json = json.loads(rv.data)
        # Check Return Values
        self.assertEqual(rv_json[u'title'], u"Test Title")
        self.assertEqual(rv_json[u'description'], u"Test Description")
        # Check Database Values
        tag = Tag.query.get(1)
        self.assertEqual(tag.title, u"Test Title")
        self.assertEqual(tag.description, u"Test Description")

    def test_get_tag(self):
        self._add_default_tag()
        rv = self.app.get(u'/api/v1.0/tag')
        rv_json = json.loads(rv.data)
        self.assertEqual(rv_json[u'meta'][u'per_page'], 25)
        self.assertEqual(rv_json[u'meta'][u'total'], 1)
        self.assertEqual(rv_json[u'meta'][u'pages'], 1)
        self.assertEqual(rv_json[u'meta'][u'page'], 1)
        self.assertEqual(rv_json[u'results'][0][u'title'], u"Test Title")

 
#-----------------------------------------------------------------------------#
class DocumentSearchAPITestCase(BaseTestCase):
    def test_required_params(self):
        rv = self.app.get(u'/api/v1.0/document/search')
        rv_json = json.loads(rv.data)
        self.assertTrue(rv_json[u'message'], u'query is required in args')

    def test_params_params(self):
        rv = self.app.get(u'/api/v1.0/document/search?query=test&per_page=3&reverse=true')
        rv_json = json.loads(rv.data)
        self.assertEqual(rv_json[u'meta'][u'per_page'], 3)
        self.assertEqual(rv_json[u'meta'][u'reverse'], True)

    def test_broken_query(self):
        doc = self._add_default_doc()
        self._index_doc(doc)
        rv = self.app.get(u'/api/v1.0/document/search?query=id:1')
        rv_json = json.loads(rv.data)
        self.assertEqual(rv_json[u'query'], u':(')

    def test_query(self):
        doc = self._add_default_doc()
        self._index_doc(doc)
        rv = self.app.get(u'/api/v1.0/document/search?query=test')
        rv_json = json.loads(rv.data)
        self.assertEqual(rv_json[u'meta'][u'per_page'], 25)
        self.assertEqual(rv_json[u'meta'][u'page'], 1)
        self.assertEqual(rv_json[u'meta'][u'total'], 1)
        self.assertEqual(rv_json[u'hits'][0][u'id'], 1)
        self.assertEqual(rv_json[u'query'], u'text:test')
