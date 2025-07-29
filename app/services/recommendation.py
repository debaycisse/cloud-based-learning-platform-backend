from flask import jsonify
import requests
from app.models.assessment import AssessmentResult, Assessment
from app.models.course import Course
from app.models.learning_path import LearningPath
from app.models.user import User
from collections import Counter
from app.utils.validation import html_tags_unconverter


'''
RecommendationService class for generating personalized course and learning path recommendations.
This class includes methods for:
- Course recommendations based on assessment results, knowledge gaps, user progress, and preferences.
- Learning path recommendations based on assessment results, user progress, and career goals.
- Similar course recommendations based on course categories and tags.
- Personalized recommendations based on user preferences.
'''
class RecommendationService:
    '''
    Generates personalized course recommendations based on:
    - Assessment results
    - Knowledge gaps
    - User progress
    - User preferences
    - Similar users' course consumption
    Args:
        user_id: The ID of the user
        limit: Maximum number of recommendations to return
    Returns:
        list: Recommended courses
    '''
    @staticmethod
    def get_course_recommendations(user_id, limit=5):
        try:
            # Get user data
            user = User.find_by_id(user_id)

            if not user:
                return []

            # Get user's assessment results
            results = AssessmentResult.find_by_user(user_id)

            if not results:
                return []

            # Extract knowledge gaps from failed assessments
            knowledge_gaps = []
            for result in results:
                if not result.get('passed', False):
                    knowledge_gaps.extend(result.get('knowledge_gaps', []))

            # Get user's completed and in-progress courses
            completed_courses = user.get('progress', {}).get('completed_courses', [])

            in_progress_courses = user.get('progress', {}).get('in_progress_courses', [])
            
            # Combine different recommendation strategies
            knowledge_based_recs = RecommendationService._get_knowledge_gap_recommendations(
                knowledge_gaps, limit=limit
            )
            
            collaborative_recs = RecommendationService._get_collaborative_recommendations(
                user_id, completed_courses, in_progress_courses, limit=limit
            )
            
            content_based_recs = RecommendationService._get_content_based_recommendations(
                user_id, completed_courses, in_progress_courses, limit=limit
            )
            
            # Combine and rank recommendations
            all_recommendations = []
            
            # Add knowledge-based recommendations with highest priority
            all_recommendations.extend([(course, 3) for course in knowledge_based_recs])
            
            # Add collaborative recommendations with medium priority
            all_recommendations.extend([(course, 2) for course in collaborative_recs])
            
            # Add content-based recommendations with lower priority
            all_recommendations.extend([(course, 1) for course in content_based_recs])

            # Remove duplicates, keeping the highest priority
            unique_recommendations = {}
            for course, priority in all_recommendations:
                course_id = str(course.get('_id'))
                if course_id not in unique_recommendations or priority > unique_recommendations[course_id][1]:
                    unique_recommendations[course_id] = (course, priority)

            # Sort by priority (descending) and return the courses
            sorted_recommendations = sorted(
                unique_recommendations.values(), 
                key=lambda x: x[1], 
                reverse=True
            )

            # Extract just the courses from the (course, priority) tuples
            recommended_courses = [rec[0] for rec in sorted_recommendations]

            # Filter out courses the user has already completed or is taking
            completed_courses_list = [
                field 
                for course_progress in completed_courses 
                for field in course_progress if isinstance(field, str)
            ]

            filtered_recommendations = [
                course for course in recommended_courses 
                if str(course.get('_id')) not in completed_courses_list
                and str(course.get('_id')) not in in_progress_courses
            ]

            return filtered_recommendations[:limit]
        except Exception as e:
            raise e

    
    '''
    Recommends courses that address specific knowledge gaps.
    Args:
        knowledge_gaps: List of knowledge gaps
        limit: Maximum number of recommendations to return
    Returns:
        list: Recommended courses
    '''
    def _get_knowledge_gap_recommendations(knowledge_gaps, limit=3):
        try:

            if not knowledge_gaps:
                return []
            
            # Remove duplicates from knowledge gaps
            unique_gaps = list(set(knowledge_gaps))
            
            # Find courses that address these knowledge gaps
            # In a real implementation, you would have tags or concepts
            # associated with courses to enable this matching
            recommended_courses = []
            
            # Query courses that match the knowledge gaps
            # This assumes you have a 'tags' or 'concepts' field in your courses
            for gap in unique_gaps:
                matching_courses = Course.find_all(
                    filters={'content.tags': {'$in': [gap]}},
                    limit=2
                )
                recommended_courses.extend(matching_courses)
                
                if len(recommended_courses) >= limit:
                    break
            
            return recommended_courses[:limit]
        except Exception as e:
            raise e

    '''
    Recommends courses based on collaborative filtering.
    Collaborative filtering finds users with similar course consumption patterns
    and recommends courses they have taken that the current user has not.
    Args:
        user_id: The ID of the user
        completed_courses: List of completed course IDs
        in_progress_courses: List of in-progress course IDs
        limit: Maximum number of recommendations to return
    Returns:
        list: Recommended courses
    '''
    @staticmethod
    def _get_collaborative_recommendations(user_id, completed_courses, in_progress_courses, limit=3):
        try:
            # Find users who have taken similar courses
            similar_users = []

            # Combine completed and in-progress courses
            user_courses = completed_courses + [in_progress_courses]
            
            unique_user_courses = None

            if len(user_courses) > 1:
                unique_user_courses = set(user_courses)
            
            if not unique_user_courses:
                return []

            # Find users who have completed or are taking the same courses
            for course_id in unique_user_courses:
                users_with_course = User.find_all_users(
                    filters={
                        '$or': [
                            {'progress.completed_courses': course_id},
                            {'progress.in_progress_courses': course_id}
                        ],
                        '_id': {'$ne': user_id}  # Exclude the current user
                    },
                    limit=20
                )
                similar_users.extend(users_with_course)
            
            if not similar_users:
                return []
            
            # Count how many times each user appears (more overlap = more similar)
            user_counts = Counter([str(user.get('_id')) for user in similar_users])
            
            # Get the most similar users
            most_similar_users = [
                user_id for user_id, count in user_counts.most_common(10)
            ]
            
            # Find courses these similar users have taken that this user hasn't yet
            recommended_course_ids = set()
            
            for similar_user_id in most_similar_users:
                similar_user = User.find_by_id(similar_user_id)
                if not similar_user:
                    continue                
                    
                similar_user_courses = (
                    similar_user.get('progress', {}).get('completed_courses', []) +
                    [similar_user.get('progress', {}).get('in_progress_courses', '')]
                )
                
                # Add courses, which the similar user has taken but this user hasn't yet
                for course_id in similar_user_courses:
                    if course_id and course_id not in unique_user_courses:
                        recommended_course_ids.add(course_id)
                        
                        if len(recommended_course_ids) >= limit:
                            break
                
                if len(recommended_course_ids) >= limit:
                    break
            
            # Fetch the full course objects
            recommended_courses = []
            for course_id in recommended_course_ids:
                course = Course.find_by_id(course_id)
                if course is not None:
                    course['_id'] = str(course['_id'])
                    recommended_courses.append(course)
            
            return recommended_courses[:limit]

        except Exception as e:
            raise e
    
    '''
    Recommends courses based on content-based filtering.
    Content-based filtering recommends courses similar to those the user has already taken.
    Args:
        user_id: The ID of the user
        completed_courses: List of completed course IDs
        in_progress_courses: List of in-progress course IDs
        limit: Maximum number of recommendations to return
    Returns:
        list: Recommended courses
    '''
    @staticmethod
    def _get_content_based_recommendations(user_id, completed_courses, in_progress_courses, limit=3):
        try:
            # Combine completed and in-progress courses
            user_courses = completed_courses + [in_progress_courses]
            
            if not user_courses:
                return []
            
            # Get the full course objects for the user's courses
            user_course_objects = []
            for course_id in user_courses:
                course = Course.find_by_id(course_id)
                if course:
                    user_course_objects.append(course)
            
            if not user_course_objects:
                return []
            
            # Extract categories and tags from the user's courses
            categories = [course.get('category') for course in user_course_objects if 'category' in course]
            
            # Find courses in the same categories
            recommended_courses = []
            
            for category in categories:
                similar_courses = Course.find_by_category(category, limit=3)
                
                # Filter out courses the user has already taken
                similar_courses = [
                    course for course in similar_courses 
                    if str(course.get('_id')) not in user_courses
                ]
                
                recommended_courses.extend(similar_courses)
                
                if len(recommended_courses) >= limit:
                    break
            
            # If we don't have enough recommendations, add some popular courses
            if len(recommended_courses) < limit:
                # Get some popular courses
                popular_courses = Course.find_all(limit=limit-len(recommended_courses))
                
                # Filter out courses the user has already taken
                popular_courses = [
                    course for course in popular_courses 
                    if str(course.get('_id')) not in user_courses
                    and course not in recommended_courses
                ]
                
                recommended_courses.extend(popular_courses)
            
            return recommended_courses[:limit]

        except Exception as e:
            raise e
    
    '''
    Generates personalized learning path recommendations based on:
    - Assessment results (both strengths and knowledge gaps)
    - User progress
    Args:
        user_id: The ID of the user
        limit: Maximum number of recommendations to return
    Returns:
        list: Recommended learning paths
    '''
    @staticmethod
    def get_learning_path_recommendations(user_id, limit=3):

        try:

            # Get user data
            user = User.find_by_id(user_id)
            if not user:
                return []
            
            # Get user's assessment results
            results = AssessmentResult.find_by_user(user_id)
            
            # Extract knowledge gaps and strengths
            knowledge_gaps = []
            strengths = []
            
            for result in results:
                # Extract knowledge gaps from failed assessments
                for question, answer in zip(result.get('questions', []), result.get('answers', [])):
                    if answer != question.get('correct_answer'):
                        for concept in question.get('tags', []):
                            if len(concept) > 0:
                                knowledge_gaps.append(html_tags_unconverter(concept))
                    else:
                        for concept in question.get('tags', []):
                            if len(concept) > 0:
                                strengths.append(html_tags_unconverter(concept))

            # Remove duplicates
            knowledge_gaps = list(set(knowledge_gaps))
            strengths = list(set(strengths))
            
            # Get user's goals from preferences
            user_goals = user.get('preferences', {}).get('goals', [])
            
            # Find learning paths that address these knowledge gaps
            # or build on strengths or match goals
            recommended_paths = []
            
            # Find paths that match the knowledge gaps (highest priority)
            if len(knowledge_gaps) > 0:
                for gap in knowledge_gaps:
                    matching_paths = LearningPath.find_by_skill(gap, limit=2)
                    recommended_paths.extend(matching_paths)
                    
                    if len(recommended_paths) >= limit:
                        break
            
            # Find paths that build on user strengths (medium priority)
            if strengths and len(recommended_paths) < limit:
                # Get paths that build on the user's strengths
                # These are paths that have the user's strengths as prerequisites
                # and include advanced topics in those areas
                for strength in strengths:
                    # Find paths that have this strength as a prerequisite
                    # and include advanced topics in this area
                    advanced_paths = LearningPath.find_all(
                        filters={
                            'prerequisites.skills': strength,
                            'target_skills': {'$ne': strength}  # Exclude paths that only teach the basics
                        },
                        limit=2
                    )
                    
                    # Add paths that aren't already in the recommendations
                    for path in advanced_paths:
                        if path not in recommended_paths:
                            recommended_paths.append(path)
                            
                            if len(recommended_paths) >= limit:
                                break
                    
                    if len(recommended_paths) >= limit:
                        break
            
            # Find paths that match user goals (lower priority)
            if user_goals and len(recommended_paths) < limit:
                for goal in user_goals:
                    # Assuming you have a way to find paths by goal
                    # This could be implemented in the LearningPath model
                    matching_paths = LearningPath.find_by_skill(goal, limit=2)
                    
                    # Add paths that aren't already in the recommendations
                    for path in matching_paths:
                        if path not in recommended_paths:
                            recommended_paths.append(path)
                            
                            if len(recommended_paths) >= limit:
                                break
                    
                    if len(recommended_paths) >= limit:
                        break
            
            # If we don't have enough recommendations, add some popular paths
            if len(recommended_paths) < limit:
                popular_paths = LearningPath.find_all(limit=limit-len(recommended_paths))
                for path in popular_paths:
                    if path not in recommended_paths:
                        recommended_paths.append(path)
            
            return recommended_paths[:limit]

        except Exception as e:
            raise e
    '''
    Generates personalized course recommendations based on user preferences.
    Args:
        user_id: The ID of the user
        preference_data: Optional dictionary of user preferences
        limit: Maximum number of recommendations to return
    Returns:
        list: Recommended courses
    '''
    @staticmethod
    def get_personalized_recommendations(user_id, preference_data=None, limit=4):

        try:
                
            # Get user data
            user = User.find_by_id(user_id)
            if not user:
                return []
            
            # If preference data is provided, use it for recommendations
            if preference_data:
                return RecommendationService._get_preference_based_recommendations(
                    user_id, preference_data, limit
                )
            
            # If no explicit preferences are provided, use the user's stored preferences
            user_preferences = user.get('preferences', {})
            if user_preferences and (user_preferences.get('categories') or user_preferences.get('skills')):
                return RecommendationService._get_preference_based_recommendations(
                    user_id, user_preferences, limit
                )
            
            # Otherwise, use a combination of collaborative and content-based filtering
            completed_courses = user.get('progress', {}).get('completed_courses', [])
            in_progress_courses = user.get('progress', {}).get('in_progress_courses', [])
            
            # If the user has no course history, return popular courses
            if not completed_courses and not in_progress_courses:
                return Course.find_all(limit=limit)
            
            # Get recommendations based on course history
            return RecommendationService.get_course_recommendations(user_id, limit)

        except Exception as e:
            raise e
    
    @staticmethod
    def _get_preference_based_recommendations(user_id, preference_data, limit=4):
        """
        Recommend courses based on explicit user preferences
        
        Args:
            user_id: The ID of the user
            preference_data: Dictionary of user preferences
            limit: Maximum number of recommendations to return
            
        Returns:
            list: Recommended courses
        """

        try:                
            # Get user data for additional context
            user = User.find_by_id(user_id)
            if not user:
                return []
                
            # Get user's completed and in-progress courses to filter them out
            completed_courses = user.get('progress', {}).get('completed_courses', [])
            in_progress_courses = user.get('progress', {}).get('in_progress_courses', [])
            user_courses = completed_courses + in_progress_courses
            
            # Extract preferences
            preferred_categories = preference_data.get('categories', [])
            preferred_skills = preference_data.get('skills', [])
            difficulty_level = preference_data.get('difficulty', 'beginner')
            
            # Build query filters based on preferences
            filters = {}
            
            if preferred_categories:
                filters['category'] = {'$in': preferred_categories}
            
            if preferred_skills:
                filters['content.tags'] = {'$in': preferred_skills}
            
            if difficulty_level:
                filters['difficulty'] = difficulty_level
            
            # Get courses matching the preferences
            recommended_courses = Course.find_all(filters=filters, limit=limit+len(user_courses))
            
            # Filter out courses the user has already taken
            recommended_courses = [
                course for course in recommended_courses 
                if str(course.get('_id')) not in user_courses
            ]
            
            # If we don't have enough recommendations, relax the filters
            if len(recommended_courses) < limit:
                # Try with just categories
                if preferred_categories:
                    category_courses = Course.find_all(
                        filters={'category': {'$in': preferred_categories}},
                        limit=limit - len(recommended_courses) + len(user_courses)
                    )
                    
                    # Filter out courses the user has already taken
                    category_courses = [
                        course for course in category_courses 
                        if str(course.get('_id')) not in user_courses
                    ]
                    
                    # Add courses that aren't already in the recommendations
                    for course in category_courses:
                        if course not in recommended_courses:
                            recommended_courses.append(course)
                            
                            if len(recommended_courses) >= limit:
                                break
            
            # If we still don't have enough, add popular courses
            if len(recommended_courses) < limit:
                popular_courses = Course.find_all(limit=limit - len(recommended_courses) + len(user_courses))
                
                # Filter out courses the user has already taken
                popular_courses = [
                    course for course in popular_courses 
                    if str(course.get('_id')) not in user_courses
                ]
                
                for course in popular_courses:
                    if course not in recommended_courses:
                        recommended_courses.append(course)
                        
                        if len(recommended_courses) >= limit:
                            break
            
            return recommended_courses[:limit]

        except Exception as e:
            raise e
    
    @staticmethod
    def get_similar_courses(course_id, limit=3):
        """
        Find courses similar to a given course
        
        Args:
            course_id: The ID of the course
            limit: Maximum number of similar courses to return
            
        Returns:
            list: Similar courses
        """

        try :
                
            course = Course.find_by_id(course_id)
            if not course:
                return []
            
            # Get courses in the same category
            category = course.get('category')
            similar_courses = Course.find_by_category(category, limit=limit+1)
            
            # Remove the original course from the results
            similar_courses = [c for c in similar_courses if str(c.get('_id')) != str(course_id)]
            
            # If we need more recommendations, look at courses with similar tags
            if len(similar_courses) < limit and 'content' in course and 'tags' in course['content']:
                tags = course['content']['tags']
                
                if tags:
                    tag_courses = Course.find_all(
                        filters={'content.tags': {'$in': tags}, '_id': {'$ne': course_id}},
                        limit=limit - len(similar_courses)
                    )
                    
                    for tag_course in tag_courses:
                        if tag_course not in similar_courses:
                            similar_courses.append(tag_course)
                            
                            if len(similar_courses) >= limit:
                                break
            
            return similar_courses[:limit]

        except Exception as e:
            raise e
