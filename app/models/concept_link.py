from datetime import datetime, timezone
from bson import ObjectId
from app import db
from app.utils.validation import validate_website_link, html_tags_converter

concept_links_collection = db.concepts

'''
This is a model for concept links in the application.
It provides methods to create, retrieve, update, and delete concept
link objects. Concept links are used to associate concepts with
external links and provide a description.
'''
class ConceptLinks:
    
    '''
    Creates a new concept link object
    Args:
        concepts - list of the concepts, discussed at the link location
        links - list of links that discuss the concepts
        description - the short description of the concepts
    Returns:
        The created concept link object
    '''
    @staticmethod
    def create(concepts, links, description):
        '''
        Creates a new concept link object
        Args:
            concept - list of the concepts, discussed at the link
            location
            links - list of links that discuss the concepts
            description - the short description of the concepts
        Returns:
            The created concept link object 
        '''
        if not isinstance(concepts, list):
            concepts = [concepts]
        
        if not isinstance(links, list):
            links = [links]
        
        for link in links:
            if not validate_website_link(link):
                return None

        try:
            concept = {
                'concepts': concepts,
                'links': links,
                'description': description,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            result = concept_links_collection.insert_one(concept)
            concept['_id'] = str(result.inserted_id)
            return concept
        except Exception as e:
            return None

    '''
    Retrieves the concept link object whose id is given
    Args:
        concept_link_id - the ID of the given concept link
    Returns:
        the retrieved concept link object
    '''
    @staticmethod
    def get_by_id(concept_link_id):
        '''
        Retrieves the concept link object whose id is given

        Args:
            concept_link_id - the ID of the given concept link
        Returns:
            the retrieved concept link object
        '''
        try:
            return concept_links_collection.find_one({
                '_id': ObjectId(concept_link_id)
            })
        except Exception as e:
            return None
        
    '''
    Retrieves all concept link objects
    Args:
        skip - number of documents to skip (for pagination)
        limit - maximum number of documents to return
    Returns:
        a list of all retrieved concept link objects
    '''
    @staticmethod
    def get_concepts(skip=0, limit=10):
        try:
            return concept_links_collection.find({}).limit(limit).skip(skip)
        except Exception as e:
            return None

    '''
    Retrieves the concept link object whose one of its concept is given
    Args:
        concept - concept, which must be among the ones in the list of
        the concept field of a typical concept link object.
    Returns:
        the concept link object whose one of the concept in its list of
        concept matches the given concept.
    '''
    @staticmethod
    def get_by_concept(concept):
        try:
            return concept_links_collection.find_one({
                'concepts': {'$in': [concept]}
            })
        except Exception as e:
            return None
    
    '''
    Updates the concept link object whose ID is given
    Args:
        concept_link_id - the ID of the concept link object to be updated.
        updated_data - the updated data, which is to be used for
        updating the concept link object.
    Returns:
        true if the update was successful without error, otherwise None
    '''
    @staticmethod
    def update(concept_link_id, updated_data):
        try:
            if isinstance(concept_link_id, str):
                concept_link_id = ObjectId(concept_link_id)

            if not isinstance(updated_data.get('concepts'), list):
                concepts = [updated_data.get('concepts')]
            else:
                concepts = updated_data.get('concepts')

            if not isinstance(updated_data.get('links'), list):
                links = [updated_data.get('links')]
            else:
                links = updated_data.get('links')

            for link in links:
                if not validate_website_link(link):
                    return None

            data = {
                'concepts': concepts,
                'links': links,
                'description': str(updated_data.get('description'))
            }

            result = concept_links_collection.update_one(
                {'_id': concept_link_id},
                {
                    '$set': {
                        **data,
                        'updated_at': datetime.now(
                            timezone.utc).isoformat()
                    },
                }
            )

            return result.matched_count > 0
        except Exception as e:
            return None

    '''
    Removes a concept object whose ID is given.
    Args:
        concept_link_id - the ID of the concept link object
    Returns:
        True, if successfully removed, False, otherwise, but
        if error, None
    '''
    @staticmethod
    def remove(concept_link_id):
        '''
        Removes a concept object whose ID is given.

        Args:
            concept_link_id - the ID of the concept link object
        Returns:
            True, if successfully removed, False, otherwise,
            but if error, None
        '''
        try:
            if not isinstance(concept_link_id, ObjectId):
                concept_link_id = ObjectId(concept_link_id)

            result = concept_links_collection.delete_one({
                '_id': concept_link_id
            })

            return result.deleted_count > 0
        
        except Exception as e:
            return None

    '''
    Gets the count of concept link documents in the collection.
    Args:
        query - optional query to filter the documents
    Returns:
        The count of concept link documents matching the query.
        If no query is provided, returns the total count
        of documents.
        If query is a string, it searches for documents where
        the 'concepts' field matches the string using a
        regular expression.
    '''
    @staticmethod
    def get_document_count(query=None):
        if not query:
            return concept_links_collection.count_documents(
                {}
            )
        elif isinstance(query, str):
            return concept_links_collection.count_documents({
                'concepts': {'$regex': html_tags_converter(query)}
            })
    
    '''
    Searches for concept links based on a query string.
    Args:
        query - the search query string
        skip - number of documents to skip (for pagination)
        limit - maximum number of documents to return
    Returns:
        A list of concept links matching the query.
    '''
    @staticmethod
    def search(query, skip=0, limit=10):
        '''
        Searches for concept links based on a query string.

        Args:
            query - the search query string
            skip - number of documents to skip (for pagination)
            limit - maximum number of documents to return
        Returns:
            A list of concept links matching the query.
        '''
        try:
            return concept_links_collection.find({
                'concepts': {'$regex': html_tags_converter(query)},
            }).limit(limit).skip(skip)
        except Exception as e:
            return None
