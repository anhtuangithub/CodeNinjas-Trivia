from contextlib import contextmanager
import os
import unittest
import json

from flaskr import create_app
from models import db, Question, Category


DB_HOST = os.getenv('DB_HOST', 'localhost:5432')
DB_USER = os.getenv('DB_USER', 'tuanla')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'trivia_test')


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.database_path = 'postgresql+psycopg2://{}:{}@{}/{}'.format(DB_USER, DB_PASSWORD, DB_HOST, DB_NAME)
        self.app = create_app(self.database_path)
        self.client = self.app.test_client
        # self.database_name = DB_NAME
        
        # setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            # self.db = SQLAlchemy()
            # self.db.init_app(self.app)
            # create all tables
            db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        with self.app.app_context():
            # db.drop_all()
            pass
        
    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data.decode('utf-8'))

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['categories'])
        self.assertEqual(data['total_categories'], 6)
        self.assertEqual(data['total_categories'],
                         len(data['categories'].keys()))

    def test_get_paginated_questions(self):
        with self.app.app_context():
            res = self.client().get('/questions')
            data = json.loads(res.data.decode('utf-8'))
            questions = Question.query.all()

            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['categories'])
            self.assertEqual(len(data['categories'].keys()), 6)
            self.assertTrue(data['questions'])
            self.assertEqual(len(data['questions']), 10)
            self.assertEqual(data['total_questions'], len(questions))

    def test_404_sent_requesting_beyond_valid_page(self):
        res = self.client().get('/questions?page=10000')
        data = json.loads(res.data.decode('utf-8'))

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_get_specific_questions_by_category(self):
        with self.app.app_context():
            res = self.client().get('/categories/1/questions')
            data = json.loads(res.data.decode('utf-8'))
            questions = Question.query.all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(data['current_category']['id'], 1)
            self.assertTrue(data['questions'])
            self.assertTrue(len(data['questions']), 3)
            self.assertEqual(data['total_questions'], len(questions))

    def test_404_sent_requesting_questions_for_invalid_category(self):
        res = self.client().get('/categories/1000/questions')
        data = json.loads(res.data.decode('utf-8'))

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_delete_specific_question(self):
        with self.app.app_context():
            total_questions_before_deleting = len(Question.query.all())

            res = self.client().delete('/questions/10')
            data = json.loads(res.data.decode('utf-8'))

            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['question'])
            self.assertEqual(data['question'], 10)
            self.assertEqual(data['total_questions'],
                            total_questions_before_deleting-1)

    def test_404_sent_deleting_non_existant_questions(self):
        res = self.client().delete('/questions/1000')
        data = json.loads(res.data.decode('utf-8'))

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_create_question(self):
        with self.app.app_context():
            total_questions_before_creating_new_question = len(
                Question.query.all())
            res = self.client().post('/questions/create', json = {
                'question': 'test question',
                'answer': 'answer',
                'difficulty': 1,
                'category': 1
            })
            data = json.loads(res.data.decode('utf-8'))

            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['questions'])
            self.assertEqual(data['total_questions'],
                            total_questions_before_creating_new_question + 1)

    def test_search_question(self):
        with self.app.app_context():
            res = self.client().post('/questions', json = {'searchTerm': 'title'})
            data = json.loads(res.data.decode('utf-8'))

            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['questions'])
            self.assertEqual(len(data['questions']), len(Question.query.order_by(
                Question.id).filter(Question.question.ilike(
                    '%{}%'.format('title'))).all()))

    def test_get_quizzes(self):
        res = self.client().post('/quizzes',json = {
            'previous_questions': [20],
            'quiz_category': {
                'id': '1',
                'type': 'Science'
            }
        })
        data = json.loads(res.data.decode('utf-8'))

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['question'])
        self.assertEqual(data['question']['category'], 1)

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()