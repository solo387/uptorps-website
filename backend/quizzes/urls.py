from django.urls import path
from .views import (
    DifficultyView,
    LevelView,
    ProgrammeView,
    CourseView,
    CreateQuestionView,
    CreateAnswersView,
    QuizView,
    StartQuizAttemptView, 
    SubmitQuizView
)

urlpatterns = [
    path("difficulty/", DifficultyView.as_view()),
    path("level/", LevelView.as_view()),
    path("programme/", ProgrammeView.as_view()),
    path("course/", CourseView.as_view()),
    path("quiz/", QuizView.as_view()),
    path("question/", CreateQuestionView.as_view()),
    path("answer/", CreateAnswersView.as_view()),
    path("attempt/start/<uuid:quiz_id>/", StartQuizAttemptView.as_view()),
    path("attempt/submit/", SubmitQuizView.as_view()),
    # path("attempt/submit/<uuid:attempt_id>/", SubmitQuizView.as_view()),
]
