from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from courses.models import Course
from .models import Review
from django.shortcuts import render
from django.contrib import messages


@login_required
def add_review(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '')
        Review.objects.update_or_create(
            course=course,
            student=request.user,
            defaults={'rating': rating, 'comment': comment},
        )
    return redirect('course_detail', pk=course_id)


@login_required
def manage_reviews(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # only instructor of course, staff or superuser may manage
    if not (request.user == course.instructor or request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You are not authorized to manage reviews for this course.')
        return redirect('courses:instructor_dashboard')

    reviews = course.reviews.select_related('student').order_by('-created_at')
    return render(request, 'reviews/manage_reviews.html', {'course': course, 'reviews': reviews})


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    course = review.course
    # only instructor of course, staff or superuser may delete
    if not (request.user == course.instructor or request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You are not authorized to delete this review.')
        return redirect('courses:instructor_dashboard')

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted.')
    return redirect('reviews:manage_reviews', course_id=course.id)
