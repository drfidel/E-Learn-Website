from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from courses.models import Certificate, Course, Enrollment, Progress
from .forms import LessonForm, ModuleForm, QuestionForm, QuizForm
from .models import Lesson, Module, Question, Quiz


def _can_manage_course(user, course):
    return user.is_authenticated and (
        user.is_superuser or user.is_staff or user.role == User.Role.ADMIN or course.instructor_id == user.id
    )


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course').prefetch_related('quiz__questions'), pk=pk)
    can_manage_structure = _can_manage_course(request.user, lesson.module.course)
    enrollment = Enrollment.objects.filter(student=request.user, course=lesson.module.course).first()
    can_access_lesson = bool(enrollment) or can_manage_structure
    if not can_access_lesson:
        messages.error(request, 'Please enroll in this course to access lessons.')
        return redirect('course_detail', pk=lesson.module.course.id)

    progress_record = None
    if enrollment:
        progress_record = Progress.objects.filter(enrollment=enrollment, lesson=lesson).first()
    return render(
        request,
        'courses/lesson_detail.html',
        {
            'lesson': lesson,
            'can_manage_structure': can_manage_structure,
            'enrollment': enrollment,
            'progress_record': progress_record,
        },
    )


@login_required
def module_create(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if not _can_manage_course(request.user, course):
        messages.error(request, 'You are not allowed to manage this course.')
        return redirect('course_detail', pk=course.id)

    form = ModuleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        module = form.save(commit=False)
        module.course = course
        module.save()
        messages.success(request, 'Module created successfully.')
        return redirect('course_detail', pk=course.id)
    return render(request, 'courses/module_form.html', {'form': form, 'course': course})


@login_required
def lesson_create(request, module_id):
    module = get_object_or_404(Module.objects.select_related('course'), pk=module_id)
    if not _can_manage_course(request.user, module.course):
        messages.error(request, 'You are not allowed to manage this course.')
        return redirect('course_detail', pk=module.course.id)

    form = LessonForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        lesson = form.save(commit=False)
        lesson.module = module
        lesson.save()
        messages.success(request, 'Lesson created successfully.')
        return redirect('course_detail', pk=module.course.id)
    return render(request, 'courses/lesson_form.html', {'form': form, 'module': module, 'course': module.course})


@login_required
def quiz_create(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), pk=lesson_id)
    if not _can_manage_course(request.user, lesson.module.course):
        messages.error(request, 'You are not allowed to manage this course.')
        return redirect('lessons:detail', pk=lesson.id)

    if hasattr(lesson, 'quiz'):
        messages.info(request, 'This lesson already has a quiz.')
        return redirect('lessons:detail', pk=lesson.id)

    form = QuizForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        quiz = form.save(commit=False)
        quiz.lesson = lesson
        quiz.save()
        messages.success(request, 'Quiz created successfully.')
        return redirect('lessons:detail', pk=lesson.id)
    return render(request, 'courses/quiz_form.html', {'form': form, 'lesson': lesson})


@login_required
def question_create(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.select_related('lesson__module__course'), pk=quiz_id)
    if not _can_manage_course(request.user, quiz.lesson.module.course):
        messages.error(request, 'You are not allowed to manage this course.')
        return redirect('lessons:detail', pk=quiz.lesson.id)

    form = QuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        question = form.save(commit=False)
        question.quiz = quiz
        question.save()
        messages.success(request, 'Question added successfully.')
        return redirect('lessons:detail', pk=quiz.lesson.id)
    return render(request, 'courses/question_form.html', {'form': form, 'quiz': quiz, 'lesson': quiz.lesson})


@login_required
def toggle_lesson_progress(request, lesson_id):
    if request.method != 'POST':
        return redirect('lessons:detail', pk=lesson_id)

    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), pk=lesson_id)
    enrollment = Enrollment.objects.filter(student=request.user, course=lesson.module.course).first()
    if not enrollment:
        messages.error(request, 'You must be enrolled to track progress.')
        return redirect('course_detail', pk=lesson.module.course.id)

    progress, _ = Progress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    mark_complete = request.POST.get('completed') == '1'
    progress.completed = mark_complete
    progress.completed_at = timezone.now() if mark_complete else None
    progress.save(update_fields=['completed', 'completed_at'])

    if mark_complete:
        total_lessons = sum(module.lessons.count() for module in lesson.module.course.modules.all())
        completed_lessons = enrollment.progress.filter(completed=True).count()
        if total_lessons > 0 and completed_lessons == total_lessons:
            Certificate.objects.get_or_create(enrollment=enrollment)

    messages.success(request, 'Progress updated.')
    return redirect('lessons:detail', pk=lesson.id)
