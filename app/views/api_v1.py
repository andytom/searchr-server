from flask import current_app
from datetime import datetime
from whoosh import index, qparser, highlight
from whoosh.qparser.dateparse import DateParserPlugin
from hotqueue import HotQueue
from flask.ext.restful import Resource, reqparse, fields, marshal, marshal_with,\
    types

from app import db
from app.model.document import Document
from app.model.tag import Tag
from app.lib import tag_list, string_length


# TODO - Add Auth (see http://flask-httpauth.readthedocs.org/en/latest/)

#-----------------------------------------------------------------------------#
# Setup 
#-----------------------------------------------------------------------------#


#-----------------------------------------------------------------------------#
# Constant Field Sets for Data export
#-----------------------------------------------------------------------------#
DOCUMENT_FIELDS_MIN = {
    'id': fields.Integer,
    'uri': fields.Url('document'),
    'title': fields.String
}


TAG_FIELDS_MIN = {
    'id': fields.Integer,
    'uri': fields.Url('tag'),
    'title': fields.String
}


DOCUMENT_FIELDS_ALL = {
    'id': fields.Integer,
    'uri': fields.Url('document'),
    'title': fields.String,
    'text': fields.String,
    'deleted': fields.Boolean,
    'created': fields.DateTime,
    'updated': fields.DateTime,
    'tags': fields.List(fields.Nested(TAG_FIELDS_MIN))
}


TAG_FIELDS_ALL = {
    'id': fields.Integer,
    'uri': fields.Url('tag'),
    'title': fields.String,
    'description': fields.String,
    'documents': fields.List(fields.Nested(DOCUMENT_FIELDS_MIN))
}


PAGINATE_FIELDS = {
    'total': fields.Integer,
    'pages': fields.Integer,
    'page': fields.Integer,
    'per_page': fields.Integer
}

IX_FIELDS = {
    'doc_count': fields.Integer,
    'last_modified': fields.DateTime,
    'is_empty': fields.Boolean
}


#-----------------------------------------------------------------------------#
# Helper functions
#-----------------------------------------------------------------------------#
def _get_index_queue():
    return HotQueue(current_app.config['INDEX_QUEUE'],
                    host=current_app.config['REDIS_HOST'],
                    port=current_app.config['REDIS_PORT'])


def _index_document(doc_id):
    queue = _get_index_queue()
    queue.put(doc_id)


def _parse_query(query, schema, default_field):
    qp = qparser.QueryParser(default_field, schema)
    qp.add_plugin(DateParserPlugin())
    qp.add_plugin(qparser.GtLtPlugin())
    return qp.parse(query)


def _process_results(results):
    collated_results = []
    for hit in results:
        res = {'id': hit['id'],
               'title': hit['title'],
               'snippet': hit.highlights(u"text"),
               'score': hit.score,
               'rank': hit.rank
               }
        collated_results.append(res)
    return collated_results


#-----------------------------------------------------------------------------#
# Request Parsers
#-----------------------------------------------------------------------------#
doc_parse = reqparse.RequestParser()
doc_parse.add_argument('title', type=string_length(maximum=64), required=True,
                       location='json')
doc_parse.add_argument('text', type=unicode, required=True, location='json')
doc_parse.add_argument('tags', type=tag_list, location='json', default=[])


filter_parse = reqparse.RequestParser()
filter_parse.add_argument('page', type=types.natural, location='args',
                           default=1)
filter_parse.add_argument('per_page', type=types.natural, location='args',
                          default=25)
filter_parse.add_argument('details', type=str, location='args', default='min')
                         


tag_parse = reqparse.RequestParser()
tag_parse.add_argument('title', type=string_length(maximum=64), location='json',
                       required=True)
tag_parse.add_argument('description', type=string_length(maximum=256),
                       location='json')


query_parse = reqparse.RequestParser()
query_parse.add_argument('page', type=types.natural, location='args', default=1)
query_parse.add_argument('per_page', type=types.natural, location='args',
                          default=25)
query_parse.add_argument('details', type=str, location='args', default='min')
query_parse.add_argument('query', type=string_length(minimum=3), 
                         location='args', required=True)
query_parse.add_argument('sort_field', type=unicode, location='args',
                         default=None)
query_parse.add_argument('reverse', type=types.boolean, location='args',
                         default=False)


#-----------------------------------------------------------------------------#
# Classes
#-----------------------------------------------------------------------------#
class PingAPI(Resource):
    def get(self):
        return {'message': 'Connection tested ok'}


#-----------------------------------------------------------------------------#
class DocumentAPI(Resource):
    """ DocumentAPI

        Implements Retrieve, Update and Delete for individual Documents.
        POST and PUT can be used for Updates or Insert with an ID.
    """
    @marshal_with(DOCUMENT_FIELDS_ALL)
    def _insert(self, id):
        args = doc_parse.parse_args()
        doc = Document.query.get(id)
        if doc:
            doc.update(**args)
        else:
            doc = Document(**args)
            doc.id = id
            db.session.add(doc)
        db.session.commit()
        _index_document(doc.id)
        return doc

    @marshal_with(DOCUMENT_FIELDS_ALL)
    def get(self, id):
        return Document.query.get_or_404(id)

    def post(self, id):
        return self._insert(id)

    def put(self, id):
        return self._insert(id)

    def delete(self, id):
        doc = Document.query.get_or_404(id)
        doc.delete()
        db.session.commit()
        _index_document(doc.id)
        return {"message": "Document {} has been deleted".format(id)}


class DocumentListAPI(Resource):
    """ DocumentListAPI

        Provides a list of all documents. Also provides for the ability
        to Insert without an ID using POST.
    """
    def get(self):
        args = filter_parse.parse_args()
        docs = Document.query.filter_by(deleted=False)
        docs = docs.paginate(args['page'], args['per_page'], False)
        marshal_fields = DOCUMENT_FIELDS_MIN
        if args['details'].lower() == 'all':
            marshal_fields = DOCUMENT_FIELDS_ALL
        results = [marshal(i, marshal_fields) for i in docs.items]
        return {'results': results, 'meta': marshal(docs, PAGINATE_FIELDS)}

    @marshal_with(DOCUMENT_FIELDS_ALL)
    def post(self):
        args = doc_parse.parse_args()
        doc = Document(**args)
        db.session.add(doc)
        db.session.commit()
        _index_document(doc.id)
        return doc


class DocumentTagAPI(Resource):
    """ DocumentTagAPI
        
        Provides the ability to add or removed individual tags to a document
        via the POST and DELETE methods.
    """
    @marshal_with(DOCUMENT_FIELDS_ALL)
    def post(self, doc_id, tag_id):
        tag = Tag.query.get_or_404(tag_id)
        doc = Document.query.get_or_404(doc_id)
        doc.add_tag(tag)
        db.session.commit()
        _index_document(doc.id)
        return doc
   
    @marshal_with(DOCUMENT_FIELDS_ALL)
    def delete(self, doc_id, tag_id):
        tag = Tag.query.get_or_404(tag_id)
        doc = Document.query.get_or_404(doc_id)
        doc.remove_tag(tag)
        db.session.commit()
        _index_document(doc.id)
        return doc


#-----------------------------------------------------------------------------#
class TagAPI(Resource):
    """ TagAPI

        Provides retrival, create with an id and update via GET, PUT and POST
    """
    @marshal_with(TAG_FIELDS_ALL)
    def get(self, id):
        return Tag.query.get_or_404(id)

    @marshal_with(TAG_FIELDS_ALL)
    def _insert(self, id):
        args = tag_parse.parse_args()
        tag = Tag.query.get(id)
        if tag:
            tag.update(**args)
        else:
            tag = Tag(**args)
            tag.id = id
            db.session.add(tag)
        db.session.commit()
        return tag

    def post(self, id):
        return self._insert(id)

    def put(self, id):
        return self._insert(id)

    def delete(self, id):
       return {"message": "Not Implemented"}, 501


class TagListAPI(Resource):
    """ TagListAPI

        Provides retrival of a list of all tags via GET and create without an
        if via POST.
    """
    def get(self):
        args = filter_parse.parse_args()
        tags = Tag.query.paginate(args['page'], args['per_page'], False)
        results = [marshal(i, TAG_FIELDS_MIN) for i in tags.items]
        return {'results': results, 'meta': marshal(tags, PAGINATE_FIELDS)}

    @marshal_with(TAG_FIELDS_ALL)
    def post(self):
        args = tag_parse.parse_args()
        d = Tag(**args)
        db.session.add(d)
        db.session.commit()
        return d


#-----------------------------------------------------------------------------#
class IndexAPI(Resource):
    """ IndexAPI

        Provide ability to index documents and get details about the
        current index.
    """
    @marshal_with(IX_FIELDS)
    def get(self):
        ix = Document.get_index(current_app.config['WHOOSH_INDEX_DIR'])
        return {'doc_count': ix.doc_count(), 
                'last_modified': datetime.fromtimestamp(ix.last_modified()),
                'is_empty': ix.is_empty()
                }

    # TODO - Is this even needed anymore. We run a deamon in the background
    def post(self):
        queue = _get_index_queue()
        ids = [i.id for i in Document.query.all()]
        queue.put(*ids)
        return {'message': 'Full Index command issued', 'ids': ids,
                'total': len(ids)}


#-----------------------------------------------------------------------------#
class SearchAPI(Resource):
    def get(self):
        args = query_parse.parse_args()
        ix = Document.get_index(current_app.config['WHOOSH_INDEX_DIR'])
        # TODO - Should check that the query is valid and parses at the moment
        # we just care if it is a unicode string or not.
        query = _parse_query(args['query'], ix.schema, u'text')

        # TODO - Sort this out it is a bit of a mess
        with ix.searcher() as searcher:
            results = searcher.search_page(query,
                                           args['page'],
                                           pagelen=args['per_page'],
                                           terms=True,
                                           sortedby=args['sort_field'],
                                           reverse=args['reverse'])
            result_dict = {'meta':{ 
                               'page': results.pagenum,
                               'pages': results.pagecount,
                               'per_page': args['per_page'],
                               'total': results.total,
                               'reverse': bool(args['reverse']),
                               'sort_field': args['sort_field']
                               },
                           'hits': _process_results(results)
                           }
            # There are issues converting the parsed query to a unicode string
            # if it contains the id (a NUMERIC column).
            # This should be fixed in the next version of Whoosh.
            try: 
                result_dict['query'] = unicode(query)
            except:
                result_dict['query'] = u':('
            return result_dict
