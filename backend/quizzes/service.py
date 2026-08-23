from .models import Question, AnswerOption, UserAnswer
from django.shortcuts import get_object_or_404
from django.utils import timezone

def calculate_score(request, attempt, user_answers): # Attempt object is passed to the calculate score function
    questions = attempt.quiz.questions.all() # Get all questions that belong to the quiz the attempt was made on using its related name set by the Questions model
    total = questions.count() #Count all the questions received
    correct = 0


    for answer in user_answers: # loop through all user answers using its related name answers set by useranswermodel
        question = get_object_or_404(
                Question,
                uuid= answer["question_id"],
                quiz=attempt.quiz
            )
        correct_options = set( # Create a set of correct options for comparison
            question.options.filter(is_correct=True)
        )

        selected = set(
            AnswerOption.objects.filter(
                uuid__in= answer["selected_options"],
                question= question
            )
        ) # Create a set of the selected options for comparison

        is_correct = set(selected) == set(correct_options)
        if not attempt.is_completed:
            user_answer = UserAnswer.objects.create(
                user=request.user,
                attempt=attempt,
                question=question,
                is_correct=is_correct
            )
            user_answer.selected_options.set(selected)
            user_answer.save() # Create a new object to save user answers even though old one exist
        if is_correct:
            correct += 1
    percentage = (correct / total) * 100 if total else 0

    attempt.score = correct
    attempt.percentage = percentage
    attempt.is_completed = True
    attempt.submitted_at = timezone.now()
    attempt.save()
    return {
            "score": correct,
            "total": total,
            "percentage": percentage,
        }
    
