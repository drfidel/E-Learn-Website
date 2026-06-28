from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from .forms import CourseForm
from .models import Certificate, Course, Enrollment, Progress, Wishlist
from payments.models import Payment
from reviews.models import Review


def _enrollment_progress(enrollment):
    total_lessons = sum(module.lessons.count() for module in enrollment.course.modules.all())
    completed_lessons = enrollment.progress.filter(completed=True).count()
    progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons else 0
    return total_lessons, completed_lessons, progress_percent


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
    courses = courses.annotate(students=Count('enrollments'), avg_rating=Avg('reviews__rating')).order_by('-created_at')

    paginator = Paginator(courses, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    wishlisted_ids = []
    if request.user.is_authenticated:
        wishlisted_ids = list(Wishlist.objects.filter(user=request.user, course__in=page_obj.object_list).values_list('course_id', flat=True))

    return render(request, 'courses/course_list.html', {'courses': page_obj.object_list, 'page_obj': page_obj, 'wishlisted_ids': wishlisted_ids})


@login_required
def toggle_wishlist(request, course_id):
    if request.method != 'POST':
        return redirect('courses:course_list')

    course = get_object_or_404(Course, pk=course_id)
    existing = Wishlist.objects.filter(user=request.user, course=course).first()
    if existing:
        existing.delete()
        messages.info(request, f'"{course.title}" removed from your wishlist.')
    else:
        Wishlist.objects.create(user=request.user, course=course)
        messages.success(request, f'"{course.title}" added to your wishlist.')

    return redirect(request.META.get('HTTP_REFERER', 'courses:course_list'))


@login_required
def wishlist_list(request):
    courses = (
        Course.objects.filter(wishlisted_by__user=request.user)
        .select_related('category', 'instructor')
        .annotate(students=Count('enrollments'), avg_rating=Avg('reviews__rating'))
        .order_by('-wishlisted_by__created_at')
    )
    return render(request, 'courses/wishlist.html', {'courses': courses})


def about(request):
    return render(request, 'courses/about.html')


def cookies(request):
    return render(request, 'courses/cookies.html')


def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.select_related('instructor', 'category').prefetch_related('modules__lessons'),
        pk=pk,
    )
    can_manage_structure = request.user.is_authenticated and (
        request.user.is_superuser
        or request.user.is_staff
        or request.user.role == User.Role.ADMIN
        or course.instructor_id == request.user.id
    )
    enrollment = None
    completed_lesson_ids = set()
    total_lessons = sum(module.lessons.count() for module in course.modules.all())
    completed_lessons = 0
    progress_percent = 0
    modules_data = []
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        if enrollment:
            completed_qs = Progress.objects.filter(
                enrollment=enrollment,
                completed=True,
                lesson__module__course=course,
            )
            completed_lesson_ids = set(completed_qs.values_list('lesson_id', flat=True))
            completed_lessons = len(completed_lesson_ids)
            progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons else 0
    for module in course.modules.all():
        module_total = module.lessons.count()
        module_done = len([lesson.id for lesson in module.lessons.all() if lesson.id in completed_lesson_ids])
        modules_data.append(
            {
                'module': module,
                'total': module_total,
                'done': module_done,
                'percent': int((module_done / module_total) * 100) if module_total else 0,
            }
        )
    can_access_lessons = bool(enrollment) or can_manage_structure
    
    # Fetch reviews and user's rating
    reviews = course.reviews.select_related('student').order_by('-created_at')
    user_review = None
    if request.user.is_authenticated:
        user_review = course.reviews.filter(student=request.user).first()
    
    return render(
        request,
        'courses/course_detail.html',
        {
            'course': course,
            'can_manage_structure': can_manage_structure,
            'enrollment': enrollment,
            'can_access_lessons': can_access_lessons,
            'completed_lesson_ids': completed_lesson_ids,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percent': progress_percent,
            'modules_data': modules_data,
            'reviews': reviews,
            'user_review': user_review,
        },
    )


@login_required
def instructor_dashboard(request):
    if not (request.user.role == User.Role.INSTRUCTOR or request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You are not authorized to access the instructor dashboard.')
        return redirect('home')

    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', 'all')

    courses = (
        Course.objects.filter(instructor=request.user)
        .select_related('category')
        .annotate(
            students_count=Count('enrollments', distinct=True),
            avg_rating=Avg('reviews__rating'),
        )
        .order_by('-created_at')
    )

    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if status == 'published':
        courses = courses.filter(is_published=True)
    elif status == 'draft':
        courses = courses.filter(is_published=False)

    all_courses = Course.objects.filter(instructor=request.user)
    total_students = Enrollment.objects.filter(course__instructor=request.user).count()
    published_courses = all_courses.filter(is_published=True).count()
    draft_courses = all_courses.filter(is_published=False).count()
    total_courses = all_courses.count()
    total_revenue = (
        Enrollment.objects.filter(course__instructor=request.user)
        .aggregate(total=Sum('course__price'))
        .get('total')
        or 0
    )

    return render(request, 'dashboards/instructor_dashboard.html', {
        'courses': courses,
        'total_students': total_students,
        'earnings': total_revenue,
        'total_courses': total_courses,
        'published_courses': published_courses,
        'draft_courses': draft_courses,
        'query': query,
        'status': status,
    })


@login_required
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course').prefetch_related('course__modules__lessons', 'progress')
    enrollment_rows = []
    for enrollment in enrollments:
        total_lessons, completed_lessons, progress_percent = _enrollment_progress(enrollment)
        certificate = getattr(enrollment, 'certificate', None)
        enrollment_rows.append(
            {
                'enrollment': enrollment,
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'progress_percent': progress_percent,
                'is_completed': total_lessons > 0 and completed_lessons == total_lessons,
                'certificate': certificate,
            }
        )
    wishlist_preview = (
        Course.objects.filter(wishlisted_by__user=request.user)
        .select_related('category')
        .annotate(students=Count('enrollments'), avg_rating=Avg('reviews__rating'))
        .order_by('-wishlisted_by__created_at')[:4]
    )
    return render(request, 'dashboards/student_dashboard.html', {'enrollment_rows': enrollment_rows, 'wishlist_preview': wishlist_preview})


@login_required
def enroll_course(request, course_id):
    if request.method != 'POST':
        return redirect('course_detail', pk=course_id)

    course = get_object_or_404(Course, pk=course_id)
    existing = Enrollment.objects.filter(student=request.user, course=course).first()
    if existing:
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('course_detail', pk=course.id)

    if course.price > 0:
        return redirect('payments:initiate_payment', course_id=course.id)

    Enrollment.objects.create(student=request.user, course=course)
    messages.success(request, 'Enrollment successful. You can now start learning.')
    return redirect('course_detail', pk=course.id)


@login_required
def issue_certificate(request, enrollment_id):
    if request.method != 'POST':
        return redirect('courses:student_dashboard')

    enrollment = get_object_or_404(
        Enrollment.objects.select_related('course').prefetch_related('course__modules__lessons', 'progress'),
        id=enrollment_id,
        student=request.user,
    )
    total_lessons, completed_lessons, _ = _enrollment_progress(enrollment)
    if total_lessons == 0 or completed_lessons < total_lessons:
        messages.error(request, 'Certificate is available only after completing all lessons in this course.')
        return redirect('courses:student_dashboard')

    certificate, _ = Certificate.objects.get_or_create(enrollment=enrollment)
    messages.success(request, 'Congratulations. Your certificate is ready.')
    return redirect('courses:view_certificate', certificate_id=certificate.certificate_id)


@login_required
def view_certificate(request, certificate_id):
    certificate = get_object_or_404(
        Certificate.objects.select_related('enrollment__student', 'enrollment__course__instructor'),
        certificate_id=certificate_id,
        enrollment__student=request.user,
    )
    return render(request, 'courses/certificate.html', {'certificate': certificate})


def verify_certificate(request, certificate_id):
    certificate = get_object_or_404(
        Certificate.objects.select_related('enrollment__student', 'enrollment__course__instructor'),
        certificate_id=certificate_id,
    )
    return render(request, 'courses/certificate_verify.html', {'certificate': certificate})


@login_required
def admin_dashboard(request):
    if not (request.user.role == User.Role.ADMIN or request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You are not authorized to access the admin dashboard.')
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        course_id = request.POST.get('course_id')
        if course_id:
            course = get_object_or_404(Course, pk=course_id)
            if action == 'publish':
                course.is_published = True
                course.save(update_fields=['is_published'])
                messages.success(request, f'"{course.title}" has been published.')
            elif action == 'unpublish':
                course.is_published = False
                course.save(update_fields=['is_published'])
                messages.success(request, f'"{course.title}" has been moved to draft.')
            elif action == 'delete':
                title = course.title
                course.delete()
                messages.warning(request, f'"{title}" has been deleted.')
        return redirect('courses:admin_dashboard')

    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', 'all')

    courses = (
        Course.objects.select_related('instructor', 'category')
        .annotate(
            students_count=Count('enrollments', distinct=True),
            avg_rating=Avg('reviews__rating'),
        )
        .order_by('-created_at')
    )
    if query:
        courses = courses.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(instructor__email__icontains=query)
        )
    if status == 'published':
        courses = courses.filter(is_published=True)
    elif status == 'draft':
        courses = courses.filter(is_published=False)

    metrics = {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role=User.Role.STUDENT).count(),
        'total_instructors': User.objects.filter(role=User.Role.INSTRUCTOR).count(),
        'total_courses': Course.objects.count(),
        'published_courses': Course.objects.filter(is_published=True).count(),
        'draft_courses': Course.objects.filter(is_published=False).count(),
        'total_enrollments': Enrollment.objects.count(),
        'average_rating': (Review.objects.aggregate(avg=Avg('rating')).get('avg') or 0),
        'successful_payments': Payment.objects.filter(status=Payment.Status.SUCCESS).count(),
        'total_revenue': (Payment.objects.filter(status=Payment.Status.SUCCESS).aggregate(total=Sum('amount')).get('total') or 0),
    }

    return render(request, 'dashboards/admin_dashboard.html', {
        'courses': courses,
        'query': query,
        'status': status,
        **metrics,
    })


@login_required
def course_create(request):
    if not (request.user.role == User.Role.INSTRUCTOR or request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only instructors can create courses.')
        return redirect('home')
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.instructor = request.user
        course.save()
        return redirect('courses:instructor_dashboard')
    return render(request, 'courses/course_form.html', {'form': form})
