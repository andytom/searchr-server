"""
   Searchr Server index deamon
   ---------------------------

   The Searchr index deamon ... # TODO - Write some better docs this

"""
from whoosh.writing import BufferedWriter
from hotqueue import HotQueue

from app.model.document import get_index, Document
from app.config import main as main_config


def write_doc(doc, writer):
    if doc.deleted:
        print "deleting {}".format(doc.id)
        writer.delete_by_term('id', unicode(doc.id))
    else:
        print "updating {}".format(doc.id)
        writer.update_document(**doc.prepare())


def main():
    queue = HotQueue(main_config.INDEX_QUEUE, 
                     host=main_config.REDIS_HOST, 
                     port=main_config.REDIS_PORT)
    index = get_index(main_config.WHOOSH_INDEX_DIR)
    writer = BufferedWriter(index, limit=10)
    try:
        for doc_id in queue.consume():
            print "looking at {}".format(doc_id)
            doc = Document.query.get(doc_id)
            if doc:
                write_doc(doc, writer)
            else:
                print "no doc with doc_id {}".format(doc_id)
    finally:
       writer.close()


if __name__ == '__main__':
    main()
