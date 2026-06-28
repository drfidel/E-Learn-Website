from django import forms

from .models import Lesson, Module, Question, Quiz


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Module title'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content_type', 'video_url', 'text_content', 'file', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lesson title'}),
            'content_type': forms.Select(attrs={'class': 'form-select'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'text_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Lesson text content'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        video_url = cleaned_data.get('video_url')
        text_content = cleaned_data.get('text_content')
        file = cleaned_data.get('file')

        if content_type == Lesson.ContentType.VIDEO and not video_url:
            self.add_error('video_url', 'Video URL is required for video lessons.')
        if content_type == Lesson.ContentType.TEXT and not text_content:
            self.add_error('text_content', 'Text content is required for text lessons.')
        if content_type == Lesson.ContentType.FILE and not file:
            self.add_error('file', 'A file is required for file lessons.')
        return cleaned_data


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'pass_mark']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Quiz title'}),
            'pass_mark': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Question text'}),
            'option_a': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option A'}),
            'option_b': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option B'}),
            'option_c': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option C'}),
            'option_d': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option D'}),
            'correct_option': forms.Select(attrs={'class': 'form-select'}),
        }
