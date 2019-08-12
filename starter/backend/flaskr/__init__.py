import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from  sqlalchemy.sql.expression import func
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={r'*': {'origins': '*'}})

  
  @app.after_request
  def after_request(response):
    '''
    Use the after_request decorator to set Access-Control-Allow
    '''
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

  
  @app.route('/categories', methods=['GET'])
  def get_categories():
    '''
    Create an endpoint to handle GET requests 
    for all available categories.
    '''
    try:
      categories = Category.query.all()
      if (len(categories) == 0): 
        abort(404)
      
      formatted_categories = {category.id: category.type for category in categories}

      return jsonify({
        'success': True,
        'categories': formatted_categories,
        'total_categories': len(Category.query.all())
      })
    
    except:
      abort(422)

  
  @app.route('/questions', methods=['GET'])
  def get_questions():
    '''
    Create an endpoint to handle GET requests for questions, 
    including pagination (every 10 questions). 
    This endpoint should return a list of questions, 
    number of total questions, current category, categories. 

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions. 
    '''

    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate(request, selection)

    print(len(current_questions))

    if (len(current_questions) == 0):
      abort(404)

    categories = {category.id: category.type for category in Category.query.all()}

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(Question.query.all()),
      'current_category': [],
      'categories': categories
    })


  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    '''
    Create an endpoint to DELETE question using a question ID. 

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page. 
    '''
    
    question_to_del = Question.query.filter(Question.id == question_id).one_or_none()
    if (question_to_del is None):
      abort(404)

    try:      
      question_to_del.delete()

      return jsonify({
        'success': True,
        'question': question_to_del.id,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)

  
  @app.route('/questions', methods=['POST'])
  def create_question():
    '''
    Create an endpoint to POST a new question, 
    which will require the question and answer text, 
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab, 
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.  

    Create a POST endpoint to get questions based on a search term. 
    It should return any questions for whom the search term 
    is a substring of the question. 

    TEST: Search by any phrase. The questions list will update to include 
    only question that include that string within their question. 
    Try using the word "title" to start. 
    '''
    # try:
    body = request.get_json()

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None)
    new_category = body.get('category', None)
    search_term = body.get('searchTerm', None)

    try:
      if search_term:  # handles search
        selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search_term)))
        current_questions = paginate(request, selection)

        if (len(current_questions) == 0):
          abort(404)
        else:
          return jsonify({
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'current_category': [question['category'] for question in current_questions] 
          })
      else:  # handles creation of new question
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

    except:
      abort(422)

  
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions_categories(category_id):
    '''
    Create a GET endpoint to get questions based on category. 

    TEST: In the "List" tab / main screen, clicking on one of the 
    categories in the left column will cause only questions of that 
    category to be shown. 
    '''
    current_category = Category.query.filter(Category.id == category_id).one_or_none()

    if (current_category is None):
      abort(404)

    selection = Question.query.filter(Question.category == category_id).all()
    current_questions = paginate(request, selection)

    if (len(current_questions) == 0):
      abort(404)
    
    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(Question.query.all()),
      'current_category': [current_category.format()]
    })

 
  @app.route('/quizzes', methods=['POST'])
  def get_quizzes():
    '''
    Create a POST endpoint to get questions to play the quiz. 
    This endpoint should take category and previous question parameters 
    and return a random questions within the given category, 
    if provided, and that is not one of the previous questions. 

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not. 
    '''
    try:
      body = request.get_json()
      previous_questions = body.get('previous_questions', None)
      quiz_category = body.get('quiz_category', None)

      category_id = int(quiz_category['id'])

      if (len(previous_questions) > 0):
        if (category_id > 0):  # if category was selected and not the first question in quiz
          current_question = Question.query.filter(Question.category == category_id)\
                .filter(~Question.id.in_(previous_questions)).order_by(func.random()).first()
        else:  # if ALL was selected and not the first question in quiz
          current_question = Question.query.filter(~Question.id.in_(previous_questions)).order_by(func.random()).first()
      else:
        if (category_id > 0):  # if category was selected and the first question in quiz
          current_question = Question.query.filter(Question.category == quiz_category['id']).order_by(func.random()).first()
        else:  # if ALL was selected and the first question in quiz
          current_question = Question.query.order_by(func.random()).first()
      
      if current_question is not None:
        formatted_question = current_question.format()
      else:
        formatted_question = None

      return jsonify({
        'success': True,
        'question': formatted_question
      })

    except:
      abort(422)

  
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
  

  @app.errorhandler(400)
  def bad_request_error_handler(error):
    '''
    Error handler for status code 400. 
    '''
    return jsonify({
      'success': False,
      'message': 'bad request'
    }), 400
  

  @app.errorhandler(405)
  def method_not_allowed_error_handler(error):
    '''
    Error handler for status code 405. 
    '''
    return jsonify({
      'success': False,
      'message': 'method not allowed'
    }), 405


  @app.errorhandler(500)
  def internal_server_error_handler(error):
    '''
    Error handler for status code 500. 
    '''
    return jsonify({
      'success': False,
      'message': 'internal server error'
    }), 500

  return app