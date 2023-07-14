from datetime import date

from django.shortcuts import render, get_object_or_404, reverse
from django.urls import reverse_lazy
from django.views import generic, View
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import User

from allauth.account.views import PasswordChangeView

from .models import Course, CourseRegistration, UserProfile
from . import forms

CURRENT_DATE = date.today()


class CourseList(generic.ListView):
    """Displays a list of all courses"""

    model = Course
    queryset = Course.objects.all()
    template_name = "course_list.html"


class RegisterCourse(LoginRequiredMixin, View):
    """Displays a registration form or a message"""

    def get(self, request, slug):
        courses = Course.objects.filter(registration_status=1)
        course = get_object_or_404(courses, slug=slug)
        user_registered = CourseRegistration.objects.filter(
            user=request.user, course=course
        )
        if user_registered:
            messages.warning(
                request, "You are already registered for this course."
            )
            return HttpResponseRedirect(reverse("course_list"))

        registration_form = forms.CourseRegistrationForm(course=course)

        return render(
            request,
            "register_course.html",
            {"course": course, "form": registration_form},
        )

    def post(self, request, slug):
        queryset = Course.objects.filter(registration_status=1)
        course = get_object_or_404(queryset, slug=slug)
        registration_form = forms.CourseRegistrationForm(
            data=request.POST, course=course
        )
        if registration_form.is_valid():
            registration = registration_form.save(commit=False)
            registration.course = course
            registration.user = request.user
            queryset = UserProfile.objects.filter(user=request.user)
            user_profile = get_object_or_404(queryset, user=request.user)
            registration.exam_grade = user_profile.grade + 1
            registration.save()

            # Update the registration to include the selected sessions.
            # Instructions on how to save objects with a many-
            # to-many field: https://docs.djangoproject.com/en/4.2/ref
            # /models/relations/#django.db.models.fields.related.Relat
            # edManager.set
            selected_sessions = registration_form.cleaned_data.get(
                "selected_sessions"
            )
            registration.selected_sessions.set(selected_sessions)

            messages.info(
                request, f"You have successfully signed up for {course.title}"
            )
        else:
            if not registration_form.cleaned_data.get("selected_sessions"):
                messages.warning(
                    request,
                    "Registration not submitted. "
                    "Please select at least one session.",
                )
            registration_form = forms.CourseRegistrationForm(course=course)
            return render(
                request,
                "register_course.html",
                {"course": course, "form": registration_form},
            )

        return HttpResponseRedirect(reverse("courseregistration_list"))


class CourseRegistrationList(View):
    """Displays a list of a users course registrations"""

    def get(self, request):
        user_registrations = CourseRegistration.objects.filter(
            user=request.user
        )
        current_date = date.today()
        past_registrations = [
            registration
            for registration in user_registrations
            if registration.course.end_date <= current_date
        ]
        upcoming_registrations = [
            registration
            for registration in user_registrations
            if registration.course.end_date > current_date
        ]

        return render(
            request,
            "courseregistration_list.html",
            {
                "past_registrations": past_registrations,
                "upcoming_registrations": upcoming_registrations,
            },
        )


class CancelCourseRegistration(SuccessMessageMixin, generic.edit.DeleteView):
    """Deletes a course registration instance
    Documentation for DeleteView:
    https://docs.djangoproject.com/en/3.2/ref/class-based-views/generic
    -editing/#deleteview
    """

    model = CourseRegistration
    success_url = reverse_lazy("courseregistration_list")
    template_name = "courseregistration_confirm_delete.html"

    # Get success message:
    # https://stackoverflow.com/questions/74756918/django-deleteview-
    # successmessagemixin-how-to-pass-data-to-message
    def get_success_message(self, cleaned_data):
        return (
            f"Your registration for {self.object.course.title}"
            " has been cancelled."
        )


class UpdateCourseRegistration(LoginRequiredMixin, View):
    """Updates a course registration"""

    def get(self, request, pk):
        registration = get_object_or_404(CourseRegistration, pk=pk)
        registration_form = forms.CourseRegistrationForm(
            instance=registration, course=registration.course
        )

        return render(
            request,
            "update_courseregistration.html",
            {"course": registration.course, "form": registration_form},
        )

    def post(self, request, pk):
        registration = get_object_or_404(CourseRegistration, pk=pk)
        registration_form = forms.CourseRegistrationForm(
            data=request.POST,
            instance=registration,
            course=registration.course,
        )
        if registration_form.is_valid():
            registration = registration_form.save(commit=False)
            registration.save()

            # Update the registration to include the selected sessions.
            selected_sessions = registration_form.cleaned_data.get(
                "selected_sessions"
            )
            registration.selected_sessions.set(selected_sessions)

            messages.info(
                request,
                "You have successfully signed up for "
                f"{registration.course.title}",
            )
        else:
            if not registration_form.cleaned_data.get("selected_sessions"):
                messages.warning(
                    request,
                    "Registration not submitted. "
                    "Please select at least one session.",
                )
            registration_form = forms.CourseRegistrationForm(
                instance=registration, course=registration.course
            )

            return render(
                request,
                "update_courseregistration.html",
                {"course": registration.course, "form": registration_form},
            )

        return HttpResponseRedirect(reverse("courseregistration_list"))


class UserProfileView(LoginRequiredMixin, View):
    """Displays a user profile or a form to create a new profile.
    Documentation for LoginRequiredMixin: https://docs.djangoproject
    .com/en/4.2/topics/auth/default/#the-loginrequiredmixin-mixin
    """

    def get(self, request):
        user = request.user
        profiles = UserProfile.objects.filter(user=user)
        if profiles:
            profile = get_object_or_404(profiles, user=user)
            return render(request, "userprofile.html", {"profile": profile})

        else:
            profile_form = forms.UserProfileForm()
            return render(
                request,
                "create_userprofile.html",
                {"form": profile_form},
            )

    def post(self, request):
        profile_form = forms.UserProfileForm(data=request.POST)
        if profile_form.is_valid():
            user_profile = UserProfile.objects.create(
                user=request.user,
                grade=profile_form.cleaned_data["grade"],
            )
            user_profile.user.first_name = profile_form.cleaned_data[
                "first_name"
            ]
            user_profile.user.last_name = profile_form.cleaned_data[
                "last_name"
            ]
            user_profile.user.save()
            user_profile.save()
            messages.info(
                request, "You have successfully created a user profile."
            )
        else:
            profile_form = forms.UserProfileForm()

        return HttpResponseRedirect(reverse("userprofile"))


class UpdateUserProfile(LoginRequiredMixin, View):
    """Displays a form to update user information"""

    def get(self, request):
        queryset = UserProfile.objects.filter(user=request.user)
        user_profile = get_object_or_404(queryset, user=request.user)

        profile_form = forms.UpdateUserProfileForm(
            initial={
                "username": request.user.username,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
                "grade": user_profile.grade,
            }
        )
        return render(
            request,
            "update_userprofile.html",
            {"form": profile_form},
        )

    def post(self, request):
        queryset = UserProfile.objects.filter(user=request.user)
        user_profile = get_object_or_404(queryset, user=request.user)
        profile_form = forms.UpdateUserProfileForm(data=request.POST)
        if profile_form.is_valid():
            user_profile.user.username = profile_form.cleaned_data["username"]
            user_profile.user.first_name = profile_form.cleaned_data[
                "first_name"
            ]
            user_profile.user.last_name = profile_form.cleaned_data[
                "last_name"
            ]
            user_profile.user.email = profile_form.cleaned_data["email"]
            user_profile.grade = profile_form.cleaned_data["grade"]
            user_profile.user.save()
            user_profile.save()
            messages.info(
                request, "You have successfully updated your user profile."
            )
        else:
            profile_form = forms.UpdateUserProfileForm()

        return HttpResponseRedirect(reverse("userprofile"))


class UpdateGrade(View):
    """Updates a user's grade"""

    def get(self, request):
        exam_registration = CourseRegistration.objects.filter(
            user=request.user, grade_updated=False
        ).first()
        if (
            exam_registration
            and exam_registration.course.end_date <= date.today()
        ):
            return render(
                request,
                "update_grade.html",
                {"exam_registration": exam_registration},
            )

        else:
            return HttpResponseRedirect(reverse("userprofile"))

    def post(self, request):
        answer = request.POST.get("answer")
        exam_registration = CourseRegistration.objects.filter(
            user=request.user, grade_updated=False
        ).first()
        if answer == "yes":
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.grade = exam_registration.exam_grade
            user_profile.save()
            exam_registration.grade_updated = True
            exam_registration.save()
            messages.info(
                request,
                "Congratulations! Your grade has been updated to"
                f" {user_profile.get_grade_display()}.",
            )
        else:
            exam_registration.grade_updated = True
            exam_registration.save()
            messages.info(request, "Your grade has not been updated.")

        return HttpResponseRedirect(reverse("userprofile"))


class DeactivateUser(LoginRequiredMixin, View):
    """Deactivates a user accounts
    The Django docs recommend to deactivate user accounts instead
    of deleting them to avoid breaking foreign keys:
    https://docs.djangoproject.com/en/4.2/ref/contrib/auth/#django
    .contrib.auth.models.User.is_active
    """

    def get(self, request):
        return render(request, "user_confirm_deactivate.html")

    def post(self, request):
        if not request.user.is_staff:
            user = User.objects.get(pk=request.user.pk)
            user.is_active = False
            user.save()
            messages.info(
                request, "You have successfully deactivated your account."
            )
            return HttpResponseRedirect(reverse("course_list"))
        else:
            messages.warning(
                request,
                "Staff accounts can not be deactivated."
                " Please contact us if you want to deactivate your account.",
            )
            return HttpResponseRedirect(reverse("userprofile"))


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Overrides the redirect URL for the allauth PasswordChangeView
    Instructions from: https://stackoverflow.com/a/56599071
    """

    success_url = reverse_lazy("userprofile")
