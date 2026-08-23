from django.urls import path
from .views import (
    auth_docs,
    quiz_docs
)


urlpatterns = [
    path("auth/", auth_docs, name="auth_docs"),
    path("quiz/", quiz_docs, name="quiz_docs"),
]


