from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from courses.models import Course
from .models import Review


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
