from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from courses.models import Course, Enrollment
from .models import Payment
from .services import verify_payment


@login_required
def initiate_payment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    payment = Payment.objects.create(
        student=request.user,
        course=course,
        provider=Payment.Provider.STRIPE,
        amount=course.price,
        external_reference='demo-reference',
    )
    if verify_payment(payment):
        payment.status = Payment.Status.SUCCESS
        payment.save(update_fields=['status'])
        Enrollment.objects.get_or_create(student=request.user, course=course)
    return redirect('courses:student_dashboard')
