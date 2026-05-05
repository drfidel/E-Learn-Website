from datetime import timedelta
from decimal import Decimal

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum, Q, Value
from django.db.models.functions import Coalesce, TruncDate
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone


class ElearnAdminSite(AdminSite):
    site_header = "E-Learn Administration"
    site_title = "E-Learn Admin"
    index_title = "Platform Overview"
    index_template = "admin/index.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "analytics/",
                self.admin_view(self.analytics_view),
                name="analytics",
            ),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        context = extra_context or {}
        context.update(self._dashboard_context())
        return super().index(request, context)

    def analytics_view(self, request):
        context = dict(
            self.each_context(request),
            **self._dashboard_context(days=30),
        )
        return TemplateResponse(request, "admin/analytics_dashboard.html", context)

    def _build_daily_series(self, queryset, date_field, days, aggregate="count"):
        end = timezone.localdate()
        start = end - timedelta(days=days - 1)
        date_lookup = {f"{date_field}__date__range": (start, end)}
        filtered = queryset.filter(**date_lookup)

        if aggregate == "sum_amount":
            rows = (
                filtered.annotate(day=TruncDate(date_field))
                .values("day")
                .annotate(total=Coalesce(Sum("amount"), Value(Decimal("0.00"))))
                .order_by("day")
            )
        else:
            rows = (
                filtered.annotate(day=TruncDate(date_field))
                .values("day")
                .annotate(total=Count("id"))
                .order_by("day")
            )

        totals_by_day = {
            row["day"]: float(row["total"]) if aggregate == "sum_amount" else int(row["total"])
            for row in rows
        }

        data = []
        for offset in range(days):
            day = start + timedelta(days=offset)
            value = totals_by_day.get(day, 0.0 if aggregate == "sum_amount" else 0)
            data.append({"label": day.strftime("%b %d"), "value": value})
        return data

    def _dashboard_context(self, days=14):
        from courses.models import Course, Enrollment, Progress
        from payments.models import Payment
        from reviews.models import Review

        User = get_user_model()
        now = timezone.now()
        previous_window_start = now - timedelta(days=days * 2)
        current_window_start = now - timedelta(days=days)

        total_users = User.objects.count()
        total_students = User.objects.filter(role=User.Role.STUDENT).count()
        total_instructors = User.objects.filter(role=User.Role.INSTRUCTOR).count()
        pending_instructors = User.objects.filter(
            role=User.Role.INSTRUCTOR,
            is_instructor_approved=False,
        ).count()

        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(is_published=True).count()
        total_enrollments = Enrollment.objects.count()

        successful_payments = Payment.objects.filter(status=Payment.Status.SUCCESS)
        total_revenue = (
            successful_payments.aggregate(
                total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
            )["total"]
            or Decimal("0.00")
        )

        previous_revenue = (
            successful_payments.filter(
                created_at__gte=previous_window_start,
                created_at__lt=current_window_start,
            )
            .aggregate(total=Coalesce(Sum("amount"), Value(Decimal("0.00"))))
            .get("total")
            or Decimal("0.00")
        )
        current_revenue = (
            successful_payments.filter(created_at__gte=current_window_start)
            .aggregate(total=Coalesce(Sum("amount"), Value(Decimal("0.00"))))
            .get("total")
            or Decimal("0.00")
        )

        previous_enrollments = Enrollment.objects.filter(
            created_at__gte=previous_window_start,
            created_at__lt=current_window_start,
        ).count()
        current_enrollments = Enrollment.objects.filter(
            created_at__gte=current_window_start
        ).count()

        total_progress = Progress.objects.count()
        completed_progress = Progress.objects.filter(completed=True).count()
        completion_rate = (
            round((completed_progress / total_progress) * 100, 1) if total_progress else 0.0
        )

        average_rating = (
            Review.objects.aggregate(avg=Avg("rating")).get("avg") or 0.0
        )

        top_courses = (
            Course.objects.select_related("instructor", "category")
            .annotate(
                enrollments_total=Count("enrollments", distinct=True),
                revenue_total=Coalesce(
                    Sum(
                        "payments__amount",
                        filter=Q(payments__status=Payment.Status.SUCCESS),
                    ),
                    Value(Decimal("0.00")),
                ),
                avg_rating=Avg("reviews__rating"),
            )
            .order_by("-enrollments_total", "-created_at")[:6]
        )

        def growth_percent(current_value, previous_value):
            if previous_value == 0:
                return 100.0 if current_value > 0 else 0.0
            return round(((current_value - previous_value) / previous_value) * 100, 1)

        return {
            "admin_metrics": {
                "total_users": total_users,
                "total_students": total_students,
                "total_instructors": total_instructors,
                "pending_instructors": pending_instructors,
                "total_courses": total_courses,
                "published_courses": published_courses,
                "draft_courses": total_courses - published_courses,
                "total_enrollments": total_enrollments,
                "completion_rate": completion_rate,
                "successful_payments": successful_payments.count(),
                "total_revenue": total_revenue,
                "average_rating": round(float(average_rating), 1) if average_rating else 0.0,
                "enrollment_growth": growth_percent(current_enrollments, previous_enrollments),
                "revenue_growth": growth_percent(float(current_revenue), float(previous_revenue)),
            },
            "admin_series": {
                "enrollments": self._build_daily_series(Enrollment.objects.all(), "created_at", days),
                "revenue": self._build_daily_series(successful_payments, "created_at", days, aggregate="sum_amount"),
            },
            "top_courses": top_courses,
            "window_days": days,
        }
