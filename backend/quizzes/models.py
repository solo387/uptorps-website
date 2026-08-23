from django.db import models
from django.conf import settings
import uuid

# User model from account
User = settings.AUTH_USER_MODEL

# Difficulty Model
class Difficulty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

# Level Model
class Level(models.Model):
    difficulty = models.ForeignKey(
        Difficulty,
        on_delete=models.CASCADE,
        related_name="levels",
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("difficulty", "name")
        ordering = ["difficulty", "name"]

    def __str__(self):
        return f"{self.difficulty.name} - {self.name}"

# Programme Model
class Programme(models.Model):
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name="programmes",
    )
    name = models.CharField(max_length=150)

    class Meta:
        unique_together = ("level", "name")
        ordering = ["level", "name"]

    def __str__(self):
        return f"{self.level} - {self.name}"

# Course Model
class Course(models.Model):
    programme = models.ForeignKey(
        Programme,
        on_delete=models.CASCADE,
        related_name="courses",
    )
    name = models.CharField(max_length=200)

    # Ownership / assignment
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT, # prevent deleting owner of the course
        related_name="created_courses",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("programme", "name")
        ordering = ["programme", "name"]

    def __str__(self):
        return f"{self.programme} - {self.name}"

# Quiz Model
class Quiz(models.Model):
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="quizzes",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_quizzes",
    )

    is_paid = models.BooleanField(default=False)

    # Future support
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    locked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
# Question Model
class Question(models.Model):
    class QuestionType(models.TextChoices):
        TRUE_FALSE = "TF", "True/False"
        MULTIPLE_CHOICE = "MC", "Multiple Choice"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    text = models.TextField()
    question_type = models.CharField(max_length=2, choices=QuestionType.choices)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.quiz.course} - {self.quiz} - {self.text[:50]}'
    
# Answer Model
class AnswerOption(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
    )

    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f' {self.question.quiz.course} - {self.question.quiz} - {self.question.text[:15]}..... - {self.text}'
    
# Quiz Attempt Model
class QuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quiz_attempts"
    )

    quiz = models.ForeignKey(
        "Quiz",
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    score = models.FloatField(default=0)
    percentage = models.FloatField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "quiz")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f'{self.user} --- {self.quiz} --- {self.score}'


# User Answer Model
class UserAnswer(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        # related_name="quiz_attempts"
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers"
    )

    question = models.ForeignKey(
        "Question",
        on_delete=models.CASCADE
    )

    selected_options = models.ManyToManyField(
        "AnswerOption",
        blank=True
    )

    is_correct = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     unique_together = ("attempt", "question")

    def __str__(self):
        options_text = ", ".join([opt.text for opt in self.selected_options.all()[:3]])
        if self.selected_options.count() > 3:
            options_text += "..."
        return f'{self.question} ---- {self.user} ---- {options_text}'
