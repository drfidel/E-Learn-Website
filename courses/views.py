from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CourseForm
from .models import Course, Enrollment


def course_list(request):
    courses = Course.objects.filter(is_published=True).select_related('instructor', 'category')
    q = request.GET.get('q')
    if q:
        courses = courses.filter(title__icontains=q)
    pricing = request.GET.get('pricing')
    if pricing == 'free':
        courses = courses.filter(price=0)
    elif pricing == 'paid':
        courses = courses.exclude(price=0)
    courses = courses.annotate(students=Count('enrollments'), avg_rating=Avg('reviews__rating'))
    return render(request, 'courses/course_list.html', {'courses': courses})


def course_detail(request, pk):
    course = get_object_or_404(Course.objects.select_related('instructor'), pk=pk)
    return render(request, 'courses/course_detail.html', {'course': course})


@login_required
def instructor_dashboard(request):
    courses = Course.objects.filter(instructor=request.user)
    total_students = Enrollment.objects.filter(course__instructor=request.user).count()
    earnings = sum(e.course.price for e in Enrollment.objects.filter(course__instructor=request.user).select_related('course'))
    return render(request, 'dashboards/instructor_dashboard.html', {
        'courses': courses,
        'total_students': total_students,
        'earnings': earnings,
    })


@login_required
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    return render(request, 'dashboards/student_dashboard.html', {'enrollments': enrollments})


@login_required
def course_create(request):
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.instructor = request.user
        course.save()
        return redirect('courses:instructor_dashboard')
    return render(request, 'courses/course_form.html', {'form': form})
