from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from courses.models import CourseSession, InternalCourse
from danbw_website import constants
from users.models import User, UserProfile


class CourseRegistration(models.Model):
    """Represents a registration for a course by a user or guest"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name=_("Participant"),
        null=True,
        blank=True
    )
    email = models.EmailField(
        _("Email"),
        null=True,
        blank=True
    )
    first_name = models.CharField(
        _("First Name"),
        max_length=100,
        null=True,
        blank=True
    )
    last_name = models.CharField(
        _("Last Name"),
        max_length=100,
        null=True,
        blank=True
    )
    course = models.ForeignKey(
        InternalCourse,
        on_delete=models.CASCADE,
        verbose_name=_("Course"),
    )
    selected_sessions = models.ManyToManyField(
        CourseSession,
        blank=False,
        verbose_name=_("Selected sessions"),
    )
    registration_date = models.DateTimeField(
        _("Registration date"),
        auto_now_add=True,
    )
    dojo = models.CharField(
        _("Dojo"),
        max_length=100,
        blank=True,
        null=True,
    )
    grade = models.IntegerField(
        _("Grade"),
        choices=constants.GRADE_CHOICES,
        default=constants.RED_BELT,
        blank=True,
        null=True,
    )
    exam = models.BooleanField(
        _("Exam"),
        default=False,
        null=True,
    )
    exam_grade = models.IntegerField(
        _("Exam Grade"),
        choices=constants.EXAM_GRADE_CHOICES,
        blank=True,
        null=True,
    )
    exam_passed = models.BooleanField(
        _("Exam Passed"),
        null=True,
    )
    grade_updated = models.BooleanField(
        _("Grade Updated"),
        default=False,
    )
    accept_terms = models.BooleanField(
        _("Accept terms"),
        default=False,
    )
    discount = models.BooleanField(
        _("Discount"),
        default=False,
    )
    final_fee = models.IntegerField(
        _("Final Fee"),
        default=0,
    )
    payment_status = models.IntegerField(
        _("Payment status"),
        choices=constants.PAYMENT_STATUS,
        default=0,
    )
    payment_method = models.IntegerField(
        _("Payment method"),
        choices=constants.PAYMENT_METHODS,
        default=0,
    )
    comment = models.TextField(
        _("Comment"),
        blank=True,
    )
    dinner = models.BooleanField(
        _("Dinner"),
        blank=True,
        null=True,
    )
    overnight_stay = models.BooleanField(
        _("Overnight stay"),
        blank=True,
        null=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="unique_user_registration",
                condition=models.Q(user__isnull=False)
            ),
            models.UniqueConstraint(
                fields=["email", "course"],
                name="unique_guest_registration",
                condition=models.Q(email__isnull=False)
            )
        ]
        verbose_name = _("Course Registration")
        verbose_name_plural = _("Course Registrations")

    def calculate_fees(self, course, selected_sessions):
        final_fee = 0
        if len(selected_sessions) == len(course.sessions.all()):
            final_fee = course.course_fee if self.payment_method == 0 else course.course_fee_cash
        else:
            for session in selected_sessions:
                final_fee += session.session_fee if self.payment_method == 0 else session.session_fee_cash
        return final_fee * course.discount_percentage / 100 if self.discount else final_fee

    def set_exam(self, user=None):
        if self.exam:
            if self.user:
                user_profile = get_object_or_404(UserProfile, user=user)
                if user_profile.grade < 6:
                    self.exam_grade = user_profile.grade + 1
                else:
                    self.exam = False
            else:
                if self.grade < 6:
                    self.exam_grade = self.grade + 1
                else:
                    self.exam = False

    def save(self, *args, **kwargs):
        if not self.course.course_type == "international":
            self.dinner = None
            self.overnight_stay = None

        if self.user:
            self.email = self.user.email
            self.first_name = self.user.first_name
            self.last_name = self.user.last_name
            user_profile = get_object_or_404(UserProfile, user=self.user)
            self.dojo = user_profile.dojo
            self.grade = user_profile.grade
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
