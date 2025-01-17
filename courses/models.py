import re
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from danbw_website import constants


class Course(models.Model):
    """Represents a course a user can sign up for"""

    title = models.CharField(
        _("Title"),
        max_length=200,
    )
    slug = models.SlugField(
        max_length=200,
        unique=True
    )
    start_date = models.DateField(
        _("Start Date"),
        default=date.today,
    )
    end_date = models.DateField(
        _("End Date"),
        default=date.today,
    )
    teacher = models.CharField(
        _("Teacher(s)"),
        max_length=200,
        blank=True,
    )

    class Meta:
        ordering = ["start_date"]
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")

    def _generate_unique_slug(self):
        slug = slugify(self.title)

        if self.slug and self.slug.startswith(slug):
                return self.slug

        unique_slug = slug
        num = 1

        while Course.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
            unique_slug = f'{slug}-{num}'
            num += 1

        return unique_slug

    def __str__(self):
        return self.title

    def get_course_type(self):
        return self.__class__.__name__

    def clean(self):
        """Custom validation for Course model"""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(
                _("Start date cannot be later than end date."))

    def save(self, *args, **kwargs):
        self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)


class InternalCourse(Course):
    """Represents a course organized by the organization"""

    REGISTRATION_STATUS = (
        (0, _("closed")),
        (1, _("open")),
    )

    COURSE_TYPE = (
        ("specialized", _("Specialized Course")),
        ("dan_preparation_seminar", _("Dan Preparation/Dan Seminar")),
        ("international", _("International Course")),
        ("family_reunion", _("Family Reunion")),
        ("no_registration", _("Course without Registration")),
    )

    STATUS_CHOICES = (
        (0, _("Preview")),
        (1, _("Published")),
    )

    status = models.IntegerField(
        _("Status"),
        choices=STATUS_CHOICES,
        default=0,
    )
    publication_date = models.DateField(
        _("Publication Date"),
        blank=True,
        null=True,
    )
    registration_status = models.IntegerField(
        _("Registration Status"),
        choices=REGISTRATION_STATUS,
        default=0,
    )
    description = models.TextField(
        _("Description"),
        blank=True,
    )
    location = models.CharField(
        _("Location"),
        max_length=200,
        blank=True,
    )
    registration_start_date = models.DateField(
        _("Registration Start Date"),
        blank=True,
        null=True,
    )
    registration_end_date = models.DateField(
        _("Registration End Date"),
        blank=True,
        null=True,
    )
    organizer = models.CharField(
        _("Organizer"),
        max_length=200,
        blank=True,
        default="D.A.N. BW",
    )
    course_fee = models.IntegerField(
        _("Course Fee"),
        default=0,
    )
    course_fee_cash = models.IntegerField(
        _("Course Fee (Cash)"),
        default=0,
    )
    course_fee_with_dan_preparation = models.IntegerField(
        _("Course Fee with Dan Preparation"),
        default=0,
        blank=True,
    )
    course_fee_with_dan_preparation_cash = models.IntegerField(
        _("Course Fee with Dan Preparation (Cash)"),
        default=0,
        blank=True,
    )
    discount_percentage = models.IntegerField(
        _("Discount Percentage"),
        default=50,
    )
    bank_transfer_until = models.DateField(
        _("Bank Transfer Until"),
        default=date.today,
        blank=True,
        null=True,
    )
    course_type = models.CharField(
        _("Course Type"),
        choices=COURSE_TYPE,
        max_length=100,
    )
    flyer = models.ImageField(
        _("Flyer"),
        upload_to="images/",
        blank=True,
        null=True,
    )
    additional_info = models.TextField(
        _("Additional Information"),
        blank=True,
    )

    def clean(self):
        """Custom validation for Internal Course model"""
        super().clean()
        if self.registration_start_date and self.registration_end_date:
            if self.registration_start_date > self.registration_end_date:
                raise ValidationError(
                    _("Registration start date cannot be later than registration end date."))

        if self.course_type == "international":
            if not self.course_fee_with_dan_preparation or not self.course_fee_with_dan_preparation_cash:
                raise ValidationError(
                    _("For courses of type 'International Course', the fields for course fees with dan preparation must be filled out."))

    def save(self, *args, **kwargs):
        if self.registration_start_date or self.registration_end_date:
            start_ok = self.registration_start_date is None or self.registration_start_date <= date.today()
            end_ok = self.registration_end_date is None or date.today() <= self.registration_end_date

            if start_ok and end_ok:
                self.registration_status = 1
            else:
                self.registration_status = 0

        if self.publication_date and self.publication_date <= date.today():
            self.status = 1

        if self.end_date < date.today():
            self.status = 0

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Internal Course")
        verbose_name_plural = _("Internal Courses")


class ExternalCourse(Course):
    """Represents a course organized by an external organization"""

    organizer = models.CharField(
        _("Organizer"),
        max_length=200,
        blank=True,
    )
    url = models.URLField(_("URL"), blank=True)

    class Meta:
        verbose_name = _("External Course")
        verbose_name_plural = _("External Courses")


class CourseSession(models.Model):
    """Represents a session within a course"""

    title = models.CharField(
        _("Title"),
        max_length=200,
    )
    course = models.ForeignKey(
        InternalCourse,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("Course"),
    )
    date = models.DateField(
        _("Date"),
        default=date.today,
    )
    start_time = models.TimeField(
        _("Start Time"),
        default="00:00",
    )
    end_time = models.TimeField(
        _("End Time"),
        default="00:00",
    )
    session_fee = models.IntegerField(
        _("Session Fee"),
        default=0,
    )
    session_fee_cash = models.IntegerField(
        _("Session Fee (Cash)"),
        default=0,
    )
    is_dan_preparation = models.BooleanField(
        _("Dan Preparation"),
        default=False,
    )

    def __str__(self):
        return f"{constants.WEEKDAYS[self.date.weekday()][1]}, {self.date.strftime('%d.%m.%Y')}, {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}: {self.title}"

    def clean(self):
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValidationError(
                _("Start time cannot be later than end time."))

    class Meta:
        verbose_name = _("Course Session")
        verbose_name_plural = _("Course Sessions")
