from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .service import calculate_score
from .models import (
    Difficulty,
    Level,
    Programme,
    Course,
    Quiz, 
    QuizAttempt, 
    Question, 
    UserAnswer, 
    AnswerOption
)
from .serializers import (
    DifficultySerializer,
    LevelSerializer,
    ProgrammeSerializer,
    CourseSerializer,
    CreateQuestionSerializer,
    CreateAnswerSerializer,
    QuizSerializer,
    QuizStartSerializer, 
    QuizSubmitSerializer,
)
from .permissions import CanAttemptQuiz
from accounts.permissions import IsAdmin

class DifficultyView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow all users (no authentication required)
            return [IsAuthenticated()]
        # For POST and other methods, require authentication and admin
        return [IsAuthenticated(), IsAdmin()]

    def get(self, request):
        difficulties = Difficulty.objects.all()
        serializer = DifficultySerializer(difficulties, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DifficultySerializer(data=request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Difficulty created", "data": serializer.data}, status=status.HTTP_201_CREATED)

    def put(self, request):
        pk = request.data.get("pk")
        diffculty = get_object_or_404(Difficulty, pk=pk)
        serializer = DifficultySerializer(diffculty, data=request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Difficulty updated", "data": serializer.data}, status=status.HTTP_200_OK)


    def delete(self, request):
        name = request.query_params.get("name")
        difficulty = get_object_or_404(Difficulty, name=name)
        difficulty.delete()
        return Response({"message": "Difficulty deleted"}, status=status.HTTP_204_NO_CONTENT)


class LevelView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get(self, request):
        difficulty = request.query_params.get("difficulty")
        if difficulty:
            levels = Level.objects.filter(difficulty=get_object_or_404(Difficulty, name=difficulty))
            serializer = LevelSerializer(levels, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Difficulty is required"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        serializer = LevelSerializer(data=request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Level created", "data": serializer.data}, status=status.HTTP_201_CREATED)

    def put(self, request):
        pk = request.data.get("pk")
        level = get_object_or_404(Level, pk=pk)
        serializer = LevelSerializer(level, data=request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Level updated", "data": serializer.data})

    def delete(self, request):
        difficulty = request.query_params.get("difficulty")
        if difficulty:
            levels = Level.objects.filter(difficulty=get_object_or_404(Difficulty, name=difficulty))
            for level in levels:
                level.delete()
            return Response({"message": "Levels deleted"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "Difficulty is required"}, status=status.HTTP_400_BAD_REQUEST)

class ProgrammeView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get(self, request):
        difficulty = request.query_params.get("difficulty")
        level = request.query_params.get("level")
        if difficulty and level:
            levels = get_object_or_404(Level, name=level, difficulty=get_object_or_404(Difficulty, name=difficulty))
            programme = Programme.objects.filter(level=levels)
            serializer = ProgrammeSerializer(programme, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Difficulty is required"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        serializer = ProgrammeSerializer(data=request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Programme created", "data": serializer.data}, status=status.HTTP_201_CREATED)

    def put(self, request):
        pk = request.data.get("pk")
        programme = get_object_or_404(Programme, pk=pk)
        serializer = ProgrammeSerializer(programme, data=request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Programme updated", "data": serializer.data})



    def delete(self, request):
        difficulty = request.query_params.get("difficulty")
        levels = request.query_params.get("level")
        programme_name = request.query_params.get("programme")
        programme = get_object_or_404(Programme, name = programme_name, level= get_object_or_404(Level, name=levels, difficulty=get_object_or_404(Difficulty, name=difficulty)))
        programme.delete()
        return Response({"message": "Programme deleted"}, status=status.HTTP_204_NO_CONTENT)

class CourseView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get(self, request):
        difficulty = request.query_params.get("difficulty")
        level = request.query_params.get("level")
        programme = request.query_params.get("programme")
        if difficulty and level and programme:
            levels = get_object_or_404(Level, name=level, difficulty=get_object_or_404(Difficulty, name=difficulty))
            programme = get_object_or_404(Programme, name=programme, level=levels)
            course = Course.objects.filter(programme=programme)
            serializer = CourseSerializer(course, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Difficulty is required"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        serializer = CourseSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Course created", "data": serializer.data}, status=status.HTTP_201_CREATED)

    def put(self, request):
        pk = request.data.get("pk")
        course = get_object_or_404(Course, pk=pk)
        serializer = CourseSerializer(course, data=request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Course updated", "data": serializer.data})


    def delete(self, request):
        difficulty = request.query_params.get("difficulty")
        levels = request.query_params.get("level")
        programme = request.query_params.get("programme")
        course_name = request.query_params.get("course")
        course = get_object_or_404(Course, name=course_name, programme=get_object_or_404(Programme, name=programme, level=get_object_or_404(Level, name= levels, difficulty=get_object_or_404(Difficulty, name=difficulty))))
        course.delete()
        return Response({"message": "Course deleted"}, status=status.HTTP_204_NO_CONTENT)


class QuizView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get(self, request):
        difficulty = request.query_params.get("difficulty")
        level = request.query_params.get("level")
        programme = request.query_params.get("programme")
        course = request.query_params.get("course")
        if difficulty and level and programme:
            course = get_object_or_404(Course, name=course, programme__level__name=level, programme__level__difficulty__name=difficulty, programme__name=programme)
            quiz = Quiz.objects.filter(course=course)
            serializer = QuizSerializer(quiz, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Difficulty is required"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        difficulty= get_object_or_404(Difficulty, name= request.POST.get("difficulty"))
        level= get_object_or_404(Level, name=request.POST.get("level"), difficulty=difficulty)
        programme= get_object_or_404(Programme, name=request.POST.get("programme"), level=level)
        course= get_object_or_404(Course, name=request.POST.get("course"), programme=programme)
        serilaizer = QuizSerializer(data= request.data, context={"request": request,"course": course})
        serilaizer.is_valid(raise_exception= True)
        serilaizer.save()
        return Response({"message":"Quiz created", "data": serilaizer.data}, status=status.HTTP_201_CREATED)

    def put(self, request):
        quiz_id = request.data.get("quiz_id")
        quiz = get_object_or_404(Quiz, uuid=quiz_id)
        serializer = QuizSerializer(quiz, data=request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Quiz updated", "data": serializer.data})


    def delete(self, request):
        quiz_id = request.query_params.get("quiz_id")
        quiz = get_object_or_404(Quiz, uuid=quiz_id)
        quiz.delete()
        return Response({"message": "Quiz deleted"}, status=status.HTTP_204_NO_CONTENT)

class CreateQuestionView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        quiz = get_object_or_404(Quiz, uuid= request.query_params.get("quiz_uuid"))
        questions = quiz.questions.all()
        serializer = CreateQuestionSerializer(questions, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


    def post(self, request):
        quiz = get_object_or_404(Quiz, uuid= request.POST.get("quiz_uuid"))
        serilaizer = CreateQuestionSerializer(data= request.data, context={"request": request,"quiz": quiz})
        serilaizer.is_valid(raise_exception= True)
        serilaizer.save()
        return Response({"message":"Question created", "data": serilaizer.data}, status=status.HTTP_201_CREATED)

    def put(self, request):
        question_id = request.data.get("question_id")
        question = get_object_or_404(Question, uuid=question_id)
        serializer = CreateQuestionSerializer(question, data= request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Question updated", "data": serializer.data})


    def delete(self, request):
        question_uuid = request.query_params.get("question_uuid")
        question = get_object_or_404(Question, uuid=question_uuid)
        question.delete()
        return Response({"message": "Question deleted"}, status=status.HTTP_204_NO_CONTENT)

class CreateAnswersView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        question_uuid = request.query_params.get("question_uuid")
        question = get_object_or_404(Question, uuid=question_uuid)
        answers = AnswerOption.objects.filter(question=question)
        serializer = CreateAnswerSerializer(answers, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        question = get_object_or_404(Question, uuid= request.POST.get("question_uuid"))
        serializer = CreateAnswerSerializer(data=request.data, context={"request": request,"question": question})
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message":"Answer created", "data": serializer.data}, status=status.HTTP_201_CREATED)

    def put(self, request):
        answer_id = request.data.get("uuid")
        answer = get_object_or_404(AnswerOption, uuid=answer_id)
        serializer = CreateAnswerSerializer(answer, data=request.data)
        serializer.is_valid(raise_exception= True)
        serializer.save()
        return Response({"message": "Answer updated", "data": serializer.data})


    def delete(self, request):
        answer_uuid = request.query_params.get("answer_uuid")
        answer = get_object_or_404(AnswerOption, uuid=answer_uuid)
        answer.delete()
        return Response({"message": "Answer deleted"}, status=status.HTTP_204_NO_CONTENT)

class StartQuizAttemptView(APIView):
    permission_classes = [IsAuthenticated, CanAttemptQuiz]

    def post(self, request, quiz_id):

        quiz = get_object_or_404(Quiz, uuid=quiz_id)

        attempt, created = QuizAttempt.objects.get_or_create(
            user=request.user,
            quiz=quiz
        )

        quiz_data = QuizStartSerializer(quiz).data

        return Response({
            "attempt_id": attempt.id,
            "quiz": quiz_data
        })
    
    def delete(self, request):
        attempt_id = request.query_params.get("attempt_id")
        attempt = get_object_or_404(QuizAttempt, id=attempt_id)
        attempt.delete()
        return Response({"message": "Attempt deleted"}, status=status.HTTP_204_NO_CONTENT)

class SubmitQuizView(APIView):
    permission_classes = [IsAuthenticated, CanAttemptQuiz]

    def post(self, request):

        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt = get_object_or_404(
            QuizAttempt,
            id=serializer.validated_data["attempt_id"],
            user=request.user,
            # is_completed=False
        )

        answers_data = serializer.validated_data["answers"]

        # total_questions = attempt.quiz.questions.count()
        # correct_count = 0

        response = calculate_score(request, attempt, answers_data)
        # for answer in answers_data:

        #     question = get_object_or_404(
        #         Question,
        #         uuid=answer["question_id"],
        #         quiz=attempt.quiz
        #     )

        #     selected = AnswerOption.objects.filter(
        #         uuid__in=answer["selected_options"],
        #         question=question
        #     )

        #     correct_options = question.options.filter(is_correct=True)

        #     is_correct = set(selected) == set(correct_options)

        #     # user_answer = UserAnswer.objects.create(
        #     #     user=request.user,
        #     #     attempt=attempt,
        #     #     question=question,
        #     #     is_correct=is_correct
        #     # )
        #     # user_answer.selected_options.set(selected)
        #     # user_answer.save() # Create a new object to save user answers even though old one exist

        #     if is_correct:
        #         correct_count += 1

        # percentage = (correct_count / total_questions) * 100
        return Response(response)





# Create your views here.
# if quiz.attempts.exists():
#     quiz.locked = True
#     quiz.save(update_fields=["locked"])
