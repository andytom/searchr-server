import os
from app.model.tag import Tag
# TODO - Add doctrings


#-----------------------------------------------------------------------------#
# Internal methods
#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#
# File System related
#-----------------------------------------------------------------------------#
def ensure_dir(dir):
    "Make sure that the passed directory exists, create it if it does not."
    if not os.path.exists(dir):
        os.makedirs(dir)


#-----------------------------------------------------------------------------#
# Custom Validators
#-----------------------------------------------------------------------------#
def string_length(minimum=0, maximum=None):
    def _string_length(value, name):
        if not isinstance(value, unicode):
            raise ValueError("{} needs to be a string".format(name))
        if len(value) < minimum:
            raise ValueError("{} is less than {} characters ({})".format(name,\
                             minimum, len(value)))
        if maximum is not None and len(value) > maximum:
            raise ValueError("{} is longer than {} characters ({})".format(name,\
                             maximum, len(value)))
        return value
    return _string_length


def tag_list(value, name):
    value = set(value)
    if len(value) == 0:
        return []
    tags = Tag.query.filter(Tag.id.in_(value)).all()

    if tags is not None and (len(tags) == len(value)):
        return tags

    tag_ids = set(tag.id for tag in tags)
    invalid_ids = value.difference(tag_ids)

    if len(invalid_ids):
        raise ValueError("{} is not a valid Tag id".format(invalid_ids.pop()))
    return []
