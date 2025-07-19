from datetime import datetime, timezone
from bson import ObjectId
from app import db
from app.models.user import User
from app.utils.validation import html_tags_unconverter

courses_collection = db.courses

'''
Course Model.
This model represents a course in the system.
It includes fields, such as title, description, category,
prerequisites, content, and timestamps for creating and
updating courses. Additionally, it includes methods for
course management as well.
'''
class Course:
    '''A static method that creates a new course.
    Args:
        title (str): Title of the course.
        description (str): Description of the course.
        category (str): Category of the course. Examples: "Programming", "Data Science", etc.
        prerequisites (list): List of prerequisite courses. E.g. ["course_id1", "course_id2"].
        content (dict): Content of the course.
        difficulty (str): Difficulty level of the course.
        tags (list): Tags associated with the course.
    Returns:
        dict: Created course object.
    '''
    @staticmethod
    def create(title, description, category, prerequisites=None, difficulty=None, tags=None):
        """Create a new course"""
        course = {
            'title': title,
            'description': description,
            'category': category,
            'prerequisites': prerequisites or [],
            'content': {
                'sections': [],
                'tags': tags or []
            },
            'difficulty': difficulty or 'beginner',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'enrollment_count': 0,
            'enrolled_users': [],
            'completed_users': [],
        }
        result = courses_collection.insert_one(course)
        course['_id'] = str(result.inserted_id)
        return course
    
    '''
    A static method that finds all available courses in the system.
    Args:
        limit (int): Number of courses to return.
        skip (int): Number of courses to skip.
        filters (dict): Filters to apply to the query.
    Returns:
        list: List of courses matching the filters.
    '''
    @staticmethod
    def find_all(limit=20, skip=0, filters=None):
        limit = int(limit)
        skip = int(skip)
        """Find all courses with optional filtering"""
        query = filters or {}
        cursor = courses_collection.find(query).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    '''
    A static method that finds a specific course by its ID.
    Args:
        course_id (str): ID of the course to find.
    Returns:
        dict: Course object if found, None otherwise.
    '''
    @staticmethod
    def find_by_id(course_id):
        """Find a course by ID"""
        if isinstance(course_id, str):
            try:
                course_id = ObjectId(course_id)
            except:
                return None
        return courses_collection.find_one({'_id': ObjectId(course_id)})
    
    '''
    A static method that finds courses by category.
    Args:
        category (str): Category to filter courses by.
        limit (int): Number of courses to return.
        skip (int): Number of courses to skip.
    Returns:
        list: List of courses in the specified category.
    '''
    @staticmethod
    def find_by_category(category, limit=20, skip=0):
        """Find courses by category"""
        limit = int(limit)
        skip = int(skip)
        cursor = courses_collection.find(
            {'category': category}
        ).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    '''
    A static method that finds popular courses.
    Args:
        limit (int): Number of courses to return.
    Returns:
        list: List of popular courses.
    '''
    @staticmethod
    def find_popular_courses(limit=10):
        limit = int(limit)
        """Find popular courses based on enrollment count"""
        # We will use the enrollment_count field to determine popularity
        cursor = courses_collection.find().sort('enrollment_count', -1).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    '''
    A static method that finds courses by tags.
    Args:
        tags (list): List of tags to filter courses by.
        limit (int): Number of courses to return.
        skip (int): Number of courses to skip.
    Returns:
        list: List of courses with the specified tags.
    '''
    @staticmethod
    def find_by_tags(tags, limit=10, skip=0):
        """Find courses by tags"""
        limit = int(limit)
        skip = int(skip)
        cursor = courses_collection.find(
            {'content.tags': {'$in': tags}}
        ).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    '''
    A static method that finds courses by difficulty level.
    Args:
        difficulty (str): Difficulty level to filter courses by.
        limit (int): Number of courses to return.
        skip (int): Number of courses to skip.
    Returns:
        list: List of courses with the specified difficulty level.
    '''
    @staticmethod
    def find_by_difficulty(difficulty, limit=10, skip=0):
        """Find courses by difficulty level"""
        limit = int(limit)
        skip = int(skip)
        cursor = courses_collection.find(
            {'difficulty': difficulty}
        ).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    @staticmethod
    def get_user_by_id(user_id, limit=10, skip=0):
        """Finds courses by user's id"""
        limit = int(limit)
        skip = int(skip)
        cursor = courses_collection.find(
            {'enrolled_users': {'$in': user_id}}
        ).skip(skip).limit(limit)

        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results

    '''
    A static method that updates a course by its ID.
    Args:
        course_id (str): ID of the course to update.
        update_data (dict): Data to update the course with.
    Returns:
        dict: Updated course object.
    '''
    @staticmethod
    def update(course_id, update_data):
        """Update a course"""
        if isinstance(course_id, str):
            try:
                course_id = ObjectId(course_id)
            except:
                return None
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        courses_collection.update_one(
            {'_id': ObjectId(course_id)},
            {'$set': update_data}
        )
        updated_course = courses_collection.find_one({'_id': ObjectId(course_id)})
        return {**updated_course, '_id': str(updated_course['_id'])}
    
    '''
    A static method that deletes a course whose ID is given
    Args:
        course_id (str): ID of the course to delete from the database
    Returns:
        bool: True if the course was successfully, False otherwise
    '''
    @staticmethod
    def remove_course(course_id):
        """Update a course id"""
        if isinstance(course_id, str):
            try:
                course_id = ObjectId(course_id)
            except:
                return None

        # Ensure the course exists
        if not Course.find_by_id(course_id):
            return None
        
        deleted_course = courses_collection.delete_one({'_id': course_id})

        return deleted_course.deleted_count > 0

    
    '''
    A static method that adds a new section to a course.
    Args:
        course_id (str): ID of the course to add the section to.
        title (str): Title of the section.
        order (int): Order of the section.
    Returns:
        str: ID of the created section.
    '''
    @staticmethod
    def add_section(course_id, title, order=None):
        """Add a new section to a course"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        # Get the current highest order if not specified
        if order is None:
            course = courses_collection.find_one({'_id': ObjectId(course_id)})
            if course and 'content' in course and 'sections' in course['content']:
                sections = course['content']['sections']
                order = max([s.get('order', 0) for s in sections] + [0]) + 1
            else:
                order = 1
        
        section_id = str(ObjectId())
        
        # Add the new section
        courses_collection.update_one(
            {'_id': ObjectId(course_id)},
            {
                '$push': {
                    'content.sections': {
                        'section_id': section_id,
                        'title': title,
                        'order': order,
                        'sub_sections': []
                    }
                },
                '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}
            }
        )
        return section_id
    
    '''
    A static method that updates a section by its ID.
    Args:
        course_id (str): ID of the course to update the section in.
        section_id (str): ID of the section to update.
        update_data (dict): Data to update the section with.
    Returns:
        dict: Updated course object.
    '''
    @staticmethod
    def update_section(course_id, section_id, update_data):
        """Update a section"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()

        if 'title' in update_data and 'order' in update_data:          
            courses_collection.update_one(
                {'_id': ObjectId(course_id), 'content.sections.section_id': section_id},
                {'$set': {
                    'content.sections.$.title': update_data.get('title'),   # $ - placeholder for the matched section
                    'content.sections.$.order': update_data.get('order'),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }}
            )
        if 'title' in update_data and 'order' not in update_data:          
            courses_collection.update_one(
                {'_id': ObjectId(course_id), 'content.sections.section_id': section_id},
                {'$set': {
                    'content.sections.$.title': update_data.get('title'),   # $ - placeholder for the matched section
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }}
            )
        return courses_collection.find_one({'_id': ObjectId(course_id)})
    
    '''
    A static method that deletes a section by its ID.
    Args:
        course_id (str): ID of the course to delete the section from.
        section_id (str): ID of the section to delete.
    Returns:
        dict: Updated course object.
    '''
    @staticmethod
    def delete_section(course_id, section_id):
        """Delete a section"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        courses_collection.update_one(
            {'_id': ObjectId(course_id)},
            {
                '$pull': {
                    'content.sections': {'section_id': section_id}
                }, # $pull removes the section from the array
                '$set': {'updated_at': datetime.now(timezone.utc).isoformat()} # $set updates the updated_at field of the course
            }
        )
        return courses_collection.find_one({'_id': ObjectId(course_id)})
    
    '''
    A static method that adds a new subsection to a section.
    Args:
        course_id (str): ID of the course to add the subsection to.
        section_id (str): ID of the section to add the subsection to.
        title (str): Title of the subsection.
        order (int): Order of the subsection.
    Returns:
        str: ID of the created subsection.
    '''
    @staticmethod
    def add_subsection(course_id, section_id, title, order=None):
        """Add a new subsection to a section"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        # Get the current highest order if not specified
        if order is None:
            course = courses_collection.find_one(
                {'_id': ObjectId(course_id), 'content.sections.section_id': section_id}
            )
            if course:
                for section in course.get('content', {}).get('sections', []):
                    if section.get('section_id') == section_id:
                        sub_sections = section.get('sub_sections', [])
                        order = max([s.get('order', 0) for s in sub_sections] + [0]) + 1
                        break
            else:
                order = 1
        
        subsection_id = str(ObjectId())
        
        # Add the new subsection
        courses_collection.update_one(
            {'_id': ObjectId(course_id), 'content.sections.section_id': section_id},
            {
                '$push': {
                    'content.sections.$.sub_sections': {
                        'subsection_id': subsection_id,
                        'title': title,
                        'order': order,
                        'data': []
                    }
                }, # $push adds the subsection to the array
                '$set': {'updated_at': datetime.now(timezone.utc).isoformat()} # $set updates the updated_at field of the course
            }
        )
        return subsection_id
    
    '''
    A static method that updates a subsection by its ID.
    Args:
        course_id (str): ID of the course to update the subsection in.
        section_id (str): ID of the section to update the subsection in.
        subsection_id (str): ID of the subsection to update.
        update_data (dict): Data to update the subsection with.
    Returns:
        dict: Updated course object.
    '''
    @staticmethod
    def update_subsection(course_id, section_id, subsection_id, update_data):
        """Updates a subsection"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        if 'order' in update_data:
            courses_collection.update_one(
                {
                    '_id': ObjectId(course_id),
                    'content.sections.section_id': section_id,
                    'content.sections.sub_sections.subsection_id': subsection_id
                },
                {
                    '$set': {
                        'content.sections.$[section].sub_sections.$[subsection].title': update_data.get('title'),
                        'content.sections.$[section].sub_sections.$[subsection].order': update_data.get('order'),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                },
                array_filters=[
                    {'section.section_id': section_id},
                    {'subsection.subsection_id': subsection_id}
                ]
            )
        else:
            courses_collection.update_one(
                {
                    '_id': ObjectId(course_id),
                    'content.sections.section_id': section_id,
                    'content.sections.sub_sections.subsection_id': subsection_id
                },
                {
                    '$set': {
                        'content.sections.$[section].sub_sections.$[subsection].title': update_data.get('title'),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                },
                array_filters=[
                    {'section.section_id': section_id},
                    {'subsection.subsection_id': subsection_id}
                ]
            )
        '''array_filters allows us to filter the array elements that we want to update.
        Both $[section] and $[subsection] are placeholders that reference the two objects,
        specified in the array_filters (i.e {'section.section_id': section_id} and 
        {'subsection.subsection_id': subsection_id}).
        This allows us to update the specific subsection in the array without having to pull
        it out and push it back in.
        This is a MongoDB feature that allows us to update array elements in place.'''
        return courses_collection.find_one({'_id': ObjectId(course_id)})
    
    '''
    A static method that deletes a subsection by its ID.
    Args:
        course_id (str): ID of the course to delete the subsection from.
        section_id (str): ID of the section to delete the subsection from.
        subsection_id (str): ID of the subsection to delete.
    Returns:
        dict: Updated course object.
    '''
    @staticmethod
    def delete_subsection(course_id, section_id, subsection_id):
        """Delete a subsection"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        courses_collection.update_one(
            {'_id': ObjectId(course_id), 'content.sections.section_id': section_id},
            {
                '$pull': {
                    'content.sections.$.sub_sections': {'subsection_id': subsection_id}
                },
                '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}
            }
        )
        return courses_collection.find_one({'_id': ObjectId(course_id)})
    
    '''
    A static method that adds a data object to a subsection.
    Args:
        course_id (str): ID of the course to add the data object to.
        section_id (str): ID of the section to add the data object to.
        subsection_id (str): ID of the subsection to add the data object to.
        data_object (dict): Data object to add.
    Returns:
        bool: True if the data object was added successfully, False otherwise.
    '''
    @staticmethod
    def add_content_data(course_id, section_id, subsection_id, data_object):
        """Add a data object to a subsection"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        # Find the section and subsection
        course = courses_collection.find_one({
            '_id': ObjectId(course_id),
            'content.sections.section_id': section_id
        })
        
        if not course:
            return False
        
        # Find the highest order in the data array
        order = 1
        for section in course.get('content', {}).get('sections', []):
            if section.get('section_id') == section_id:
                for subsection in section.get('sub_sections', []):
                    if subsection.get('subsection_id') == subsection_id:
                        data = subsection.get('data', [])
                        if data:
                            order = max([d.get('order', 0) for d in data]) + 1
                        break
                break
        
        # Set the order if not already specified
        if 'order' not in data_object:
            data_object['order'] = order
        
        # Add a unique ID to the data object
        data_object['data_id'] = str(ObjectId())
        
        # Add the data object
        result = courses_collection.update_one(
            {
                '_id': ObjectId(course_id),
                'content.sections.section_id': section_id,
                'content.sections.sub_sections.subsection_id': subsection_id
            },
            {
                '$push': {
                    'content.sections.$[section].sub_sections.$[subsection].data': data_object
                },
                '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}
            },
            array_filters=[
                {'section.section_id': section_id},
                {'subsection.subsection_id': subsection_id}
            ]
        )
        
        return result.modified_count > 0
    
    '''
    A static method that updates a data object in a subsection.
    Args:
        course_id (str): ID of the course to update the data object in.
        section_id (str): ID of the section to update the data object in.
        subsection_id (str): ID of the subsection to update the data object in.
        data_id (str): ID of the data object to update.
        update_data (dict): Data to update the data object with.
    Returns:
        bool: True if the data object was updated successfully, False otherwise.
    '''
    @staticmethod
    def update_content_data(course_id, section_id, subsection_id, data_id, update_data):
        """Update a data object"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        # Update the data object
        if 'order' in update_data and\
            'alt_text' in update_data and\
            'caption' in update_data and\
            'url' in update_data:
            result = courses_collection.update_one(
                {
                    '_id': ObjectId(course_id),
                    'content.sections.section_id': section_id,
                    'content.sections.sub_sections.subsection_id': subsection_id,
                    'content.sections.sub_sections.data.data_id': data_id
                },
                {
                    '$set': {
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].content': update_data.get('content'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].order': update_data.get('order'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].type': update_data.get('type'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].alt_text': update_data.get('alt_text'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].caption': update_data.get('caption'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].url': update_data.get('url'),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                },
                array_filters=[
                    {'section.section_id': section_id},
                    {'subsection.subsection_id': subsection_id},
                    {'data.data_id': data_id}
                ]
            )
        elif 'order' in update_data and\
            'language' in update_data:
            result = courses_collection.update_one(
                {
                    '_id': ObjectId(course_id),
                    'content.sections.section_id': section_id,
                    'content.sections.sub_sections.subsection_id': subsection_id,
                    'content.sections.sub_sections.data.data_id': data_id
                },
                {
                    '$set': {
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].content': update_data.get('content'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].order': update_data.get('order'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].type': update_data.get('type'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].language': update_data.get('language'),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                },
                array_filters=[
                    {'section.section_id': section_id},
                    {'subsection.subsection_id': subsection_id},
                    {'data.data_id': data_id}
                ]
            )
        elif 'order' in update_data:
            result = courses_collection.update_one(
                {
                    '_id': ObjectId(course_id),
                    'content.sections.section_id': section_id,
                    'content.sections.sub_sections.subsection_id': subsection_id,
                    'content.sections.sub_sections.data.data_id': data_id
                },
                {
                    '$set': {
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].content': update_data.get('content'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].order': update_data.get('order'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].type': update_data.get('type'),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                },
                array_filters=[
                    {'section.section_id': section_id},
                    {'subsection.subsection_id': subsection_id},
                    {'data.data_id': data_id}
                ]
            )
        elif 'order' not in update_data and\
            'alt_text' in update_data and\
            'caption' in update_data and\
            'url' in update_data:
            result = courses_collection.update_one(
                {
                    '_id': ObjectId(course_id),
                    'content.sections.section_id': section_id,
                    'content.sections.sub_sections.subsection_id': subsection_id,
                    'content.sections.sub_sections.data.data_id': data_id
                },
                {
                    '$set': {
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].content': update_data.get('content'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].order': update_data.get('order'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].type': update_data.get('type'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].alt_text': update_data.get('alt_text'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].caption': update_data.get('caption'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].url': update_data.get('url'),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                },
                array_filters=[
                    {'section.section_id': section_id},
                    {'subsection.subsection_id': subsection_id},
                    {'data.data_id': data_id}
                ]
            )
        elif 'order' not in update_data and\
            'language' in update_data:
            result = courses_collection.update_one(
                {
                    '_id': ObjectId(course_id),
                    'content.sections.section_id': section_id,
                    'content.sections.sub_sections.subsection_id': subsection_id,
                    'content.sections.sub_sections.data.data_id': data_id
                },
                {
                    '$set': {
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].content': update_data.get('content'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].order': update_data.get('order'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].type': update_data.get('type'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].language': update_data.get('language'),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                },
                array_filters=[
                    {'section.section_id': section_id},
                    {'subsection.subsection_id': subsection_id},
                    {'data.data_id': data_id}
                ]
            )
        elif 'order' not in update_data:
            result = courses_collection.update_one(
                {
                    '_id': ObjectId(course_id),
                    'content.sections.section_id': section_id,
                    'content.sections.sub_sections.subsection_id': subsection_id,
                    'content.sections.sub_sections.data.data_id': data_id
                },
                {
                    '$set': {
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].content': update_data.get('content'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].order': update_data.get('order'),
                        'content.sections.$[section].sub_sections.$[subsection].data.$[data].type': update_data.get('type'),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                },
                array_filters=[
                    {'section.section_id': section_id},
                    {'subsection.subsection_id': subsection_id},
                    {'data.data_id': data_id}
                ]
            )
        
        return result.modified_count > 0
    
    '''
    A static method that deletes a data object from a subsection.
    Args:
        course_id (str): ID of the course to delete the data object from.
        section_id (str): ID of the section to delete the data object from.
        subsection_id (str): ID of the subsection to delete the data object from.
        data_id (str): ID of the data object to delete.
    Returns:
        bool: True if the data object was deleted successfully, False otherwise.
    '''
    @staticmethod
    def delete_content_data(course_id, section_id, subsection_id, data_id):
        """Delete a data object"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        # Delete the data object
        result = courses_collection.update_one(
            {
                '_id': ObjectId(course_id),
                'content.sections.section_id': section_id,
                'content.sections.sub_sections.subsection_id': subsection_id
            },
            {
                '$pull': {
                    'content.sections.$[section].sub_sections.$[subsection].data': {'data_id': data_id}
                },
                '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}
            },
            array_filters=[
                {'section.section_id': section_id},
                {'subsection.subsection_id': subsection_id}
            ]
        )
        
        return result.modified_count > 0
    
    '''
    A static method that retrieves a specific section by its ID.
    Args:
        course_id (str): ID of the course to retrieve the section from.
        section_id (str): ID of the section to retrieve.
    Returns:
        dict: Section object if found, None otherwise.
    '''
    @staticmethod
    def get_section(course_id, section_id):
        """Get a specific section"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        course = courses_collection.find_one(
            {'_id': ObjectId(course_id), 'content.sections.section_id': section_id},
            {'content.sections.$': 1}
        )
        
        if course and 'content' in course and 'sections' in course['content'] and len(course['content']['sections']) > 0:
            return course['content']['sections'][0]
        
        return None
    
    '''
    A static method that retrieves a specific subsection by its ID.
    Args:
        course_id (str): ID of the course to retrieve the subsection from.
        section_id (str): ID of the section to retrieve the subsection from.
        subsection_id (str): ID of the subsection to retrieve.
    Returns:
        dict: Subsection object if found, None otherwise.
    '''
    @staticmethod
    def get_subsection(course_id, section_id, subsection_id):
        """Get a specific subsection"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
            
        # This requires MongoDB 3.6+ for the aggregation pipeline
        pipeline = [
            {'$match': {'_id': ObjectId(course_id)}},
            {'$unwind': '$content.sections'},
            {'$match': {'content.sections.section_id': section_id}},
            {'$unwind': '$content.sections.sub_sections'},
            {'$match': {'content.sections.sub_sections.subsection_id': subsection_id}},
            {'$project': {'subsection': '$content.sections.sub_sections'}}
        ]
        
        result = list(courses_collection.aggregate(pipeline))
        
        if result and len(result) > 0:
            return result[0]['subsection']
        
        return None
    
    '''
    A static method that enrolls a user in a course.
    Args:
        course_id (str): ID of the course to enroll the user in.
        user_id (str): ID of the user to enroll.
    Returns:
        bool: True if the user was enrolled successfully, False otherwise.
    '''
    @staticmethod
    def enroll_user(course_id, user_id):
        """Enroll a user in a course"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
        
        # Increment the enrollment count
        courses_collection.update_one(
            {'_id': ObjectId(course_id)},
            {'$inc': {'enrollment_count': 1}}
        )
        
        # Add the user to the course's enrolled users
        courses_collection.update_one(
            {'_id': ObjectId(course_id)},
            {'$addToSet': {'enrolled_users': str(user_id)}},
        )

        # Check if the user was enrolled successfully
        course = courses_collection.find_one({'_id': ObjectId(course_id)})

        if course is not None and 'enrolled_users' not in course:
            return False
        
        if str(user_id) not in course['enrolled_users']:
            return False

        updated_user = User.update_course_progress(
            user_id=user_id,
            progress_data={
                'course_id': str(course_id),
                'percentage': 0
            }
        )

        if updated_user is None:
            return False
        
        return True

    '''
    A static method that marks a course as completed for a user, only if 
    the user has not completed the course before. If the user has completed
    the course before, it will not be marked again and it will return nothing.
    This method also inserts the user's ID in to the course's completed_users array.
    Args:
        course_id (str): ID of the course to mark as completed.
        user_id (str): ID of the user who completed the course.
    Returns:
        bool: True if the course was marked as completed successfully, False otherwise.
    '''
    @staticmethod
    def mark_course_as_completed(course_id, user_id):
        """Mark a course as completed for a user"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
        
        # Check if the user has already completed the course
        course = courses_collection.find_one(
            {'_id': ObjectId(course_id), 'completed_users': user_id}
        )
        
        if course is not None:
            return  # User has already completed the course before, do nothing
        
        # Updates and checks if the course update was successful
        result = courses_collection.update_one(
            {'_id': ObjectId(course_id)},
            {'$addToSet': {'completed_users': user_id}}
        )
        if result.modified_count == 0:
            return False

        updated_user = User.update_course_progress(
            user_id=user_id,
            progress_data={
                'completed_course_id': str(course_id) 
            }
        )

        if updated_user.modified_count == 0:
            return False

        return True

    @staticmethod
    def find_popular(limit=20, sort='popular'):
        """
        Fetch popular courses based on the sort value and limit.

        Args:
            limit (int): Maximum number of courses to return. Default is 20.
            sort (str): Sorting criteria. Default is 'popular'. Popularity is
            based on number of enrollments. Other possible values could be
            'recent', etc.

        Returns:
            list: A list of popular courses.
        """
        limit = int(limit)
        # Determine the sorting field based on the sort parameter
        sort_field = 'enrollment_count' if sort == 'popular' else 'created_at'

        # Query the database to fetch courses sorted by the specified field
        cursor = courses_collection.find().sort(sort_field, -1).limit(limit)

        # Convert the cursor to a list and return it
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    @staticmethod
    def find_by_category_and_title(
        category, title, limit=10, skip=0
    ):
        cursor = courses_collection.find(
            {
                'category': html_tags_unconverter(category),
                'title': {
                    '$regex': html_tags_unconverter(title)
                }
            }
        ).limit(limit).skip(skip)
        # Convert the cursor to a list and return it
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    @staticmethod
    def find_by_title(
        title, limit=10, skip=0
    ):
        cursor = courses_collection.find(
            {
                'title': {
                    '$regex': html_tags_unconverter(title)
                }
            }
        ).limit(limit).skip(skip)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
