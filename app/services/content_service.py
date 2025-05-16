from app.models.course import Course


'''
ContentService class for managing course content.
This includes creating courses with predefined content structures,
reordering sections, subsections, and content data.
It also includes retrieving the full content structure of a course.
This class is designed to work with the Course model and its methods.
REMINDER: It is important to ensure that the content structure is
validated before creating or updating courses.
The class methods are static and can be called without instantiating the class.
'''
class ContentService:
    '''
    This method allows for the creation of a new course with a title,
    description, category, and optional prerequisites.
    It also allows for the addition of a predefined content structure,
    which includes sections, subsections, and content data.
    The content structure must be validated before being passed to this method.
    The method returns the created course object.
    Args:
        title (str): Course title
        description (str): Course description
        category (str): Course category
        prerequisites (list): List of prerequisite courses
        content_structure (dict): Optional predefined content structure
    Returns:
        dict: The created course object
    Raises:
        ValueError: If the content structure is invalid
    '''
    @staticmethod
    def create_course_with_content(title, description, category, prerequisites=None,
                                   content_structure=None, difficulty=None, tags=None):
        # Create the course with basic structure
        course = Course.create(
            title=title,
            description=description,
            category=category,
            prerequisites=prerequisites or [],
            difficulty=difficulty,
            tags=tags or [],
        )
        
        # If content structure is provided, populate the course with sections, subsections, and content
        if content_structure and isinstance(content_structure, list):
            for section_data in content_structure:
                # Add section
                section_id = Course.add_section(
                    course_id=course['_id'],
                    title=section_data.get('title'),
                    order=section_data.get('order')
                )
                
                # Add subsections
                for subsection_data in section_data.get('sub_sections', []):
                    subsection_id = Course.add_subsection(
                        course_id=course['_id'],
                        section_id=section_id,
                        title=subsection_data.get('title'),
                        order=subsection_data.get('order')
                    )
                    
                    # Add content data
                    for data_obj in subsection_data.get('data', []):
                        Course.add_content_data(
                            course_id=course['_id'],
                            section_id=section_id,
                            subsection_id=subsection_id,
                            data_object=data_obj
                        )
        course['_id'] = str(course['_id'])
        return course
    
    '''
    This method retrieves the full content structure of a course.
    It returns a dictionary containing the sections, subsections,
    and content data of the course.
    Args:
        course_id (str): The ID of the course
    Returns:
        dict: The course content structure
    '''
    @staticmethod
    def get_course_content_structure(course_id):
        course = Course.find_by_id(course_id)
        if not course:
            return None
        
        return course.get('content', {'sections': []})
    
    '''
    This method allows for the reordering of sections, subsections,
    and content data within a course.
    It takes the course ID, section ID, subsection ID, and a list
    of dictionaries containing the IDs and new order values.
    The method updates the order of the specified sections,
    subsections, or content data in the course.
    Args:
        course_id (str): The ID of the course
        section_id (str): The ID of the section
        subsection_id (str): The ID of the subsection
        data_order (list): List of dictionaries with data_id and new order
    Returns:
        bool: Success status
    '''
    @staticmethod
    def reorder_sections(course_id, section_order):
        course = Course.find_by_id(course_id)
        if not course:
            return False
        
        for order_item in section_order:
            Course.update_section(
                course_id=course_id,
                section_id=order_item.get('section_id'),
                update_data={'order': order_item.get('order')}
            )
        
        return True
    
    '''
    This method allows for the reordering of subsections within a section.
    It takes the course ID, section ID, and a list of dictionaries
    containing the subsection IDs and new order values.
    The method updates the order of the specified subsections
    in the section.
    Args:
        course_id (str): The ID of the course
        section_id (str): The ID of the section
        subsection_order (list): List of dictionaries with subsection_id and new order
    Returns:
        bool: Success status
    '''
    @staticmethod
    def reorder_subsections(course_id, section_id, subsection_order):
        section = Course.get_section(course_id, section_id)
        if not section:
            return False
        
        for order_item in subsection_order:
            Course.update_subsection(
                course_id=course_id,
                section_id=section_id,
                subsection_id=order_item.get('subsection_id'),
                update_data={'order': order_item.get('order')}
            )
        
        return True
    
    '''
    This method allows for the reordering of content data within a subsection.
    It takes the course ID, section ID, subsection ID, and a list
    of dictionaries containing the content data IDs and new order values.
    The method updates the order of the specified content data
    in the subsection.
    Args:
        course_id (str): The ID of the course
        section_id (str): The ID of the section
        subsection_id (str): The ID of the subsection
        data_order (list): List of dictionaries with data_id and new order
    Returns:
        bool: Success status
    '''
    @staticmethod
    def reorder_content_data(course_id, section_id, subsection_id, data_order):
        subsection = Course.get_subsection(course_id, section_id, subsection_id)
        if not subsection:
            return False
        
        for order_item in data_order:
            Course.update_content_data(
                course_id=course_id,
                section_id=section_id,
                subsection_id=subsection_id,
                data_id=order_item.get('data_id'),
                update_data={'order': order_item.get('order')}
            )
        
        return True
