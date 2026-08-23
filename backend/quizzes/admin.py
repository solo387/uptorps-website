from django.contrib import admin
from .models import (
    Difficulty, 
    Level, 
    Programme, 
    Course,
    Quiz,
    Question,
    AnswerOption,
    QuizAttempt,
    UserAnswer,

)
# from audits.signals 
# Register your models here.


@admin.register(Difficulty)
class DifficultyAdmin(admin.ModelAdmin):
    search_fields = ("name","description","created_at")

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)
    
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    search_fields = ("name",)

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)

@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    search_fields = ("name",)

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)
    search_fields = ("name",)

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    search_fields = ("name",)

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)
    
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    search_fields = ("course__name","title", "uuid", "description__icontains")
    readonly_fields = ("uuid",)

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    search_fields = ("quiz__uuid","quiz__description__icontains",)
    readonly_fields = ("uuid",)

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)
    
@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    search_fields = ("question__name",)
    readonly_fields = ("uuid",)

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)
    
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    search_fields = ("user__email","quiz__uuid")
    

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)
    
@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    search_fields = ("attempt__user__email",)

    def save_model(self, request, obj, form, change):
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)