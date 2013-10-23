from app import db


#-----------------------------------------------------------------------------#
# Models
#-----------------------------------------------------------------------------#
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.String(256))

    def __init__(self, title, description=None):
        self.update(title, description)

    def update(self, title, description=None):
        self.title = title
        self.description = description
