import random
import logging
import os
from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from sqlalchemy.sql.expression import func
from models import Category, Question
#import random

from models import setup_db

QUESTIONS_PER_PAGE = 10

def paginate(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(db_URI="", test_config=None):
    # create and configure the app
    app = Flask(__name__)
    if db_URI:
        setup_db(app,db_URI)
    else:
        setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r'*': {'origins': '*'}})
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories', methods=['GET'])
    def get_categories():
        try:
            categories = Category.query.all()
            if (len(categories) == 0):
                abort(404)

            rsCategories = {
                category.id: category.type for category in categories}

            return jsonify({
                'success': True,
                'categories': rsCategories,
                'total_categories': len(categories)
            })

        except Exception as e:
            logging.exception("message")
            abort(422)

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate(request, selection)

        print(len(current_questions))

        if (len(current_questions) == 0):
            abort(404)

        categories = {
            category.id: category.type for category in Category.query.all()}

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'current_category': [],
            'categories': categories
        })
    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:questionId>', methods=['DELETE'])
    def delete_question(questionId):
        question = Question.query.filter(Question.id == questionId).one_or_none()
        if (question is None):
            abort(404)

        try:
            question.delete()

            return jsonify({
                'success': True,
                'question': question.id,
                'total_questions': len(Question.query.all())
            })

        except Exception:
            abort(422)
    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions/create', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)

        try:
            question = Question(question=new_question,
                                    answer=new_answer,
                                    difficulty=new_difficulty,
                                    category=new_category)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            questions = paginate(request, selection)

            return jsonify({
                'success': True,
                'questions': questions,
                'created': question.id,
                'total_questions': len(Question.query.all())
            })

        except Exception:
            abort(422)
    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions', methods=['POST'])
    def get_question_search_term():
        body = request.get_json()
        search_term = body.get('searchTerm', None)
        try:
            selection = Question.query.order_by(Question.id).filter(
                        Question.question.ilike('%{}%'.format(search_term)))
            current_questions = paginate(request, selection)

            if (len(current_questions) == 0):
                abort(404)
            else:
                return jsonify({
                    'questions': current_questions,
                    'total_questions': len(Question.query.all()),
                    'current_category': [(question['category'])
                                            for question in current_questions]
                })
        except Exception:
            abort(422)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_categories(category_id):
        category = Category.query.filter(
            Category.id == category_id).one_or_none()

        if (category is None):
            abort(404)

        selection = Question.query.filter(
            Question.category == category_id).all()
        questions = paginate(request, selection)
        total = Question.query.all()

        if (len(questions) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'questions': questions,
            'total_questions': len(total),
            'current_category': category_id
        })
    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    def random_question(category, previous_questions):
        if category == 0:
            questions = Question.query.filter(
                Question.id.notin_((previous_questions))).all()
        else:
            questions = Question.query.filter_by(
                category=category).filter(
                Question.id.notin_((previous_questions))).all()

        if len(questions) == 0:
            return None
        else:
            return questions[random.randrange(0, len(questions))]
    
    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():
        try:
            body = request.get_json()
            previous_questions = body.get('previous_questions')
            quiz_category = body.get('quiz_category')

            question = random_question(quiz_category['id'], previous_questions)

            if question is None:
                return jsonify({
                    'success': True
                })

            return jsonify({
                'success': True,
                'question': question.format()
            })

        except Exception:
            abort(422)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(422)
    def unprocessable_error_handler(error):
        '''
        Error handler for status code 422.
        '''
        return jsonify({
            'success': False,
            'message': 'unprocessable'
        }), 422

    @app.errorhandler(404)
    def resource_not_found_error_handler(error):
        '''
        Error handler for status code 404.
        '''
        return jsonify({
            'success': False,
            'message': 'resource not found'
        }), 404
    
    return app

