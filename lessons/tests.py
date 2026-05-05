from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Course, Enrollment, Progress
from .models import Lesson, Module, Question, Quiz


class LessonTest(TestCase):
    def test_module_ordering(self):
        instructor = User.objects.create_user(email='t@example.com', username='t', password='secret123', role='instructor')
        course = Course.objects.create(instructor=instructor, title='Python', description='desc', price=0)
        m1 = Module.objects.create(course=course, title='B', order=2)
        m2 = Module.objects.create(course=course, title='A', order=1)
        self.assertEqual(list(Module.objects.filter(course=course))[0], m2)
        Lesson.objects.create(module=m1, title='L1', content_type='text', text_content='Hello')

    def test_instructor_can_create_module(self):
        instructor = User.objects.create_user(email='inst@example.com', username='inst', password='secret123', role='instructor')
        course = Course.objects.create(instructor=instructor, title='Django', description='desc', price=0)
        self.client.force_login(instructor)

        response = self.client.post(reverse('lessons:module_create', args=[course.id]), {'title': 'Module 1', 'order': 1})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Module.objects.filter(course=course, title='Module 1').exists())

    def test_non_owner_cannot_create_module(self):
        instructor = User.objects.create_user(email='owner@example.com', username='owner', password='secret123', role='instructor')
        other_user = User.objects.create_user(email='other@example.com', username='other', password='secret123', role='instructor')
        course = Course.objects.create(instructor=instructor, title='Django', description='desc', price=0)
        self.client.force_login(other_user)

        response = self.client.post(reverse('lessons:module_create', args=[course.id]), {'title': 'Blocked Module', 'order': 1})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Module.objects.filter(course=course, title='Blocked Module').exists())

    def test_instructor_can_create_lesson(self):
        instructor = User.objects.create_user(email='inst2@example.com', username='inst2', password='secret123', role='instructor')
        course = Course.objects.create(instructor=instructor, title='Python', description='desc', price=0)
        module = Module.objects.create(course=course, title='Basics', order=1)
        self.client.force_login(instructor)

        response = self.client.post(
            reverse('lessons:lesson_create', args=[module.id]),
            {'title': 'Intro', 'content_type': 'text', 'text_content': 'Welcome', 'order': 1},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Lesson.objects.filter(module=module, title='Intro').exists())

    def test_instructor_can_create_quiz(self):
        instructor = User.objects.create_user(email='inst3@example.com', username='inst3', password='secret123', role='instructor')
        course = Course.objects.create(instructor=instructor, title='React', description='desc', price=0)
        module = Module.objects.create(course=course, title='Setup', order=1)
        lesson = Lesson.objects.create(module=module, title='Install', content_type='text', text_content='x', order=1)
        self.client.force_login(instructor)

        response = self.client.post(reverse('lessons:quiz_create', args=[lesson.id]), {'title': 'Lesson Quiz', 'pass_mark': 60})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Quiz.objects.filter(lesson=lesson, title='Lesson Quiz').exists())

    def test_instructor_can_add_question(self):
        instructor = User.objects.create_user(email='inst4@example.com', username='inst4', password='secret123', role='instructor')
        course = Course.objects.create(instructor=instructor, title='Node', description='desc', price=0)
        module = Module.objects.create(course=course, title='Runtime', order=1)
        lesson = Lesson.objects.create(module=module, title='Event Loop', content_type='text', text_content='x', order=1)
        quiz = Quiz.objects.create(lesson=lesson, title='Node Quiz', pass_mark=50)
        self.client.force_login(instructor)

        response = self.client.post(
            reverse('lessons:question_create', args=[quiz.id]),
            {
                'text': 'What does Node.js run on?',
                'option_a': 'JVM',
                'option_b': 'V8',
                'option_c': 'CLR',
                'option_d': 'SpiderMonkey',
                'correct_option': 'B',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Question.objects.filter(quiz=quiz, correct_option='B').exists())

    def test_student_can_mark_lesson_complete(self):
        instructor = User.objects.create_user(email='inst5@example.com', username='inst5', password='secret123', role='instructor')
        student = User.objects.create_user(email='stud2@example.com', username='stud2', password='secret123', role='student')
        course = Course.objects.create(instructor=instructor, title='Python', description='desc', price=0)
        module = Module.objects.create(course=course, title='Basics', order=1)
        lesson = Lesson.objects.create(module=module, title='Intro', content_type='text', text_content='Hello', order=1)
        enrollment = Enrollment.objects.create(student=student, course=course)
        self.client.force_login(student)

        response = self.client.post(reverse('lessons:toggle_progress', args=[lesson.id]), {'completed': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Progress.objects.filter(enrollment=enrollment, lesson=lesson, completed=True).exists())
