from collections.abc import Iterable
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    EmailValidator,
)
from .forms import cvut_email

from django.utils import timezone


def more_than_one_word(value: str):
    if len(value.strip().split()) == 0:
        raise ValidationError("Téma musí obsahovat alespoň jedno slovo", code="invalid")


# Create your models here.
class LabTopic(models.Model):
    title = models.TextField(
        max_length=200, blank=False, validators=[more_than_one_word], unique=True
    )
    created_by = models.ForeignKey(
        "CustomUser", related_name="topics_created", on_delete=models.CASCADE
    )

    def json(self):
        return {"id": self.id, "title": self.title, "created_by": self.created_by.email}  # type: ignore


class LabEvent(models.Model):
    lab_datetime = models.DateTimeField(null=False)
    close_login = models.DateTimeField(null=False)
    close_logout = models.DateTimeField(null=False)

    capacity = models.PositiveIntegerField(
        default=4, validators=[MinValueValidator(1), MaxValueValidator(1_000)]
    )

    topics = models.ManyToManyField(LabTopic, through="LinkTopicEvent")

    created_by = models.ForeignKey(
        "CustomUser",
        related_name="events_created",
        on_delete=models.SET_NULL,
        null=True,
    )

    def get_number_applied_users(self) -> int:
        return LinkTopicEvent.objects.filter(~models.Q(user=None), event=self).count()

    def get_free_topics(self):
        return LabTopic.objects.filter(links__user=None, links__event=self).all()

    def get_user_topic(self, user) -> LabTopic | None:
        return LabTopic.objects.filter(links__user=user, links__event=self).first()

    def is_full(self) -> bool:
        return self.capacity == self.get_number_applied_users()

    def save(self, *args, **kwargs) -> None:
        if self.lab_datetime < timezone.now():
            raise ValidationError("Date of Lab cannot be in the past", code="invalid")

        if self.close_login is None:
            raise ValidationError("Close login date must be specified", code="invalid")
        if self.close_logout is None:
            raise ValidationError("Close logout date must be specified", code="invalid")

        if self.close_login > self.lab_datetime:
            raise ValidationError(
                "Lab log in closing date cannot be greater than lab date",
                code="invalid",
            )

        if self.close_logout > self.lab_datetime:
            raise ValidationError(
                "Lab log out closing date cannot be greater than lab date",
                code="invalid",
            )

        super().save(*args, **kwargs)

    @classmethod
    def get_user_events(cls, user: "CustomUser"):
        return (
            cls.objects.filter(links__user=user, lab_datetime__gte=timezone.now())
            .order_by("lab_datetime")
            .all()
        )

    def json(self):
        return {
            "id": self.id,  # type: ignore
            "lab_date": self.lab_datetime.strftime("%d.%m.%Y %H:%M"),
            "close_login": self.close_login.strftime("%d.%m.%Y %H:%M"),
            "close_logout": self.close_logout.strftime("%d.%m.%Y %H:%M"),
            "capacity": self.capacity,
            "num_topics": self.topics.count(),
            "num_users": self.get_number_applied_users(),
        }


class LinkTopicEvent(models.Model):
    event = models.ForeignKey(
        "LabEvent", on_delete=models.CASCADE, related_name="links"
    )
    topic = models.ForeignKey(
        "LabTopic", on_delete=models.CASCADE, related_name="links"
    )

    # user
    user = models.ForeignKey(
        "CustomUser", related_name="labs", on_delete=models.CASCADE, null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "topic", "user"], name="unique link"
            )
        ]


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    id = models.BigAutoField(primary_key=True)
    username = None
    first_name = None
    last_name = None

    email = models.EmailField(
        unique=True,
        validators=[cvut_email],
    )

    fullname = models.CharField(max_length=55)
    approved = models.BooleanField(default=True)
    cancelled = models.BooleanField(default=False)
    # student_id = models.CharField(null=False, max_length=10)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def json(self):
        return {"fullname": self.fullname, "email": self.email}
