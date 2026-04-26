from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Lesson


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    return render(request, 'courses/lesson_detail.html', {'lesson': lesson})
