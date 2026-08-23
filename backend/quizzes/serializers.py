from rest_framework import serializers
from .models import (
    Difficulty,
    Level, 
    Programme, 
    Course, 
    AnswerOption, 
    Question, 
    Quiz
)

class DifficultySerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)

    class Meta:
        model = Difficulty
        fields = ["name","description", "pk"]

    def create(self, validated_data):
        description = validated_data.get("description")
        name = validated_data.get("name")
        if Difficulty.objects.filter(name=name).exists():
            raise serializers.ValidationError
        Difficulty.objects.create(
            name=name,
            description=description
        )
        return Difficulty.objects.get(name=name)
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save()
        return instance
    
    
class LevelSerializer(serializers.ModelSerializer):
    difficulty = serializers.SlugRelatedField(
        slug_field="name",
        queryset= Difficulty.objects.all()
    )

    class Meta:
        model = Level
        fields = ["name", "difficulty", "pk"]

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.difficulty = validated_data.get("difficulty", instance.difficulty)
        instance.save()
        return instance
    

    # Handled automatically that's why it's commented but for personal logic exitence uncoment and make tweaks
    # def create(self, validated_data):
    #     return Level.objects.create(**validated_data)
    

class ProgrammeSerializer(serializers.ModelSerializer):
    level = serializers.CharField(write_only=True)
    difficulty = serializers.SlugRelatedField(
        slug_field="name",
        queryset= Difficulty.objects.all(),
        write_only=True
    )
    level_name = serializers.CharField(source="level.name", read_only=True)
    difficulty_name = serializers.CharField(source="level.difficulty.name", read_only=True)


    class Meta:
        model = Programme
        fields = ["name", "level", "level_name", "difficulty", "difficulty_name", "pk"]

    def validate(self, attrs):
        difficulty = attrs.pop("difficulty")
        level_name = attrs.pop("level")

        try:
            attrs["level"] = Level.objects.get(
                name=level_name,
                difficulty=difficulty
            )
        except Level.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "level": (
                        f"Level '{level_name}' does not exist under"
                        f" difficulty '{difficulty.name}'."
                    )
                }
            )
        
        return attrs
    
class CourseSerializer(serializers.ModelSerializer):
    programme = serializers.CharField(write_only=True)
    level = serializers.CharField(write_only=True)
    difficulty = serializers.SlugRelatedField(
        slug_field="name",
        queryset= Difficulty.objects.all(),
        write_only=True
    )
    level_name = serializers.CharField(source="programme.level.name", read_only=True)
    difficulty_name = serializers.CharField(source="programme.level.difficulty.name", read_only=True)
    programme_name = serializers.CharField(source="programme.name", read_only=True)

    class Meta:
        model = Course
        fields = ["pk", "name", "programme", "programme_name", "level", "level_name", "difficulty", "difficulty_name"]

    def create(self, validated_data):
        # Get the user from the request context
        request = self.context.get("request")
        validated_data["created_by"] = request.user
        return super().create(validated_data)

    def validate(self, attrs):
        difficulty = attrs.pop("difficulty")
        level_name = attrs.pop("level")
        programme_name = attrs.pop("programme")

        try:
            # First get the Level object using difficulty and level_name
            level = Level.objects.get(
                name=level_name,
                difficulty=difficulty
            )
            
            # Then get the Programme using the resolved Level object
            attrs["programme"] = Programme.objects.get(
                name=programme_name,
                level=level
            )
        except Level.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "level": (
                        f"Level '{level_name}' does not exist under"
                        f" difficulty '{difficulty.name}'."
                    )
                }
            )
        except Programme.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "programme": (
                        f"Programme '{programme_name}' does not exist under"
                        f" level '{level_name}' and difficulty '{difficulty.name}'."
                    )
                }
            )
        
        return attrs

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ["uuid", "title", "description", "is_paid", "duration_minutes"]

    def create(self, validated_data):
        request = self.context.get("request")
        course = self.context.get("course")
        validated_data["created_by"] = request.user
        validated_data["course"] = course
        return super().create(validated_data)

class CreateQuestionSerializer(serializers.ModelSerializer):
    quiz_uuid = serializers.CharField(source="quiz.uuid", read_only=True)

    class Meta:
        model = Question
        fields = ["text", "question_type", "uuid", "quiz_uuid"]

    def create(self, validated_data):
        quiz = self.context.get("quiz")
        remove_fields = ["quiz_uuid"]
        for field in remove_fields:
            validated_data.pop(field, None)
        validated_data["quiz"] = quiz
        print(validated_data)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        remove_fields = ["quiz_uuid"]
        for field in remove_fields:
            validated_data.pop(field, None)
        return super().update(instance, validated_data)


class CreateAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ["text", "is_correct", "uuid"]

    def create(self, validated_data):
        question = self.context.get("question")
        validated_data["question"] = question
        return super().create(validated_data)

class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ["uuid", "text"]

class QuestionSerializer(serializers.ModelSerializer):

    answers = AnswerOptionSerializer(source="options", many=True)

    class Meta:
        model = Question
        fields = [
            "uuid",
            "text",
            "question_type",
            "answers"
        ]

class QuizStartSerializer(serializers.ModelSerializer):

    questions = QuestionSerializer(many=True)

    class Meta:
        model = Quiz
        fields = [
            "uuid",
            "title",
            "questions"
        ]

class SubmitAnswerSerializer(serializers.Serializer):

    question_id = serializers.UUIDField()
    selected_options = serializers.ListField(
        child=serializers.UUIDField()
    )

class QuizSubmitSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()
    answers = SubmitAnswerSerializer(many=True)