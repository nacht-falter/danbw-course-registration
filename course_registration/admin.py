from django.contrib import admin
from .models import Course, CourseRegistration


class RegistrationInline(admin.TabularInline):
    """
    Adds all registrations for a course to the course view.

    Django documentation for inline models:
    https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#inlinemodeladmin-objects
    """

    model = CourseRegistration
    extra = 0  # Set number of additional rows to 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "registration_status",
        "description",
        "start_date",
        "end_date",
        "course_fee",
    )
    search_fields = ["title", "description"]
    list_filter = ("registration_status",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [RegistrationInline]
    actions = [
        "duplicate_selected_courses",
    ]

    def duplicate_selected_courses(self, request, queryset):
        """Action for duplicating existing courses"""
        for course in queryset:
            new_title = f"Copy of {course.title}"
            new_slug = f"copy-of-{course.slug}"
            counter = 2
            while Course.objects.filter(title=new_title).exists():
                new_title = f"Copy {counter} of {course.title}"
                new_slug = f"copy-{counter}-of-{course.slug}"
                counter += 1

            Course.objects.create(
                title=new_title,
                slug=new_slug,
                description=course.description,
                registration_status=0,
                start_date=course.start_date,
                end_date=course.end_date,
                course_fee=course.course_fee,
            )
