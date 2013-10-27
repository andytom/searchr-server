from datetime import datetime
from whoosh import analysis
from whoosh.fields import TEXT, DATETIME, KEYWORD, Schema, NUMERIC
from whoosh import index

from app import db
from app import lib


#-----------------------------------------------------------------------------#
# DB Models
#-----------------------------------------------------------------------------#
tags_to_documents = db.Table('tags_to_documents',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('document_id', db.Integer, db.ForeignKey('document.id'),
              primary_key=True)
)

class Document(db.Model):
    """Class for documents to be searched over"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    created = db.Column(db.DateTime())
    updated = db.Column(db.DateTime())
    text = db.Column(db.Text())
    deleted = db.Column(db.Boolean())
    tags = db.relationship('Tag', secondary=tags_to_documents,
                           backref=db.backref('documents', lazy='dynamic'))
    schema = Schema(id=NUMERIC(stored=True, unique=True),
                    title=TEXT(stored=True),
                    text=TEXT(stored=True,
                              analyzer=analysis.NgramWordAnalyzer(3, 10)),
                    created=DATETIME(sortable=True),
                    updated=DATETIME(sortable=True),
                    tags=KEYWORD(scorable=True))

    def __init__(self, title, text, tags=[]):
        now = datetime.utcnow()
        self.created = now
        self.deleted = False
        self.update(title, text, tags, now)
        
    def update(self, title, text, tags=[], now=None):
        """Update the document"""
        if now is None:
            now = datetime.utcnow()
        self.updated = now
        self.title = title
        self.text = text
        for tag in tags:
            if type(tag) == int:
                tag = Tag.query.get(tag_id)
            self.add_tag(tag)

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)

    def delete(self):
        self.updated = datetime.utcnow()
        self.deleted = True

    def prepare(self):
        prepared_doc = {"id": self.id,
                        "title": self.title,
                        "text": self.text,
                        "created": self.created,
                        "updated": self.updated,
                        }
        if len(self.tags):
            prepared_doc["tags"] = [unicode(i.id) for i in self.tags]
        return prepared_doc

    @classmethod
    def get_index(cls, index_dir):
        lib.ensure_dir(index_dir)
        if index.exists_in(index_dir):
            ix = index.open_dir(index_dir)
        else:
            ix = index.create_in(index_dir, cls.schema)
        return ix
