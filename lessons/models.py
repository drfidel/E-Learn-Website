from django.db import models


class Module(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} - {self.title}'


class Lesson(models.Model):
    class ContentType(models.TextChoices):
        VIDEO = 'video', 'Video'
        TEXT = 'text', 'Text'
        FILE = 'file', 'File'

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    video_url = models.URLField(blank=True)
    text_content = models.TextField(blank=True)
    file = models.FileField(upload_to='lessons/files/', blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']


class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=255)
    pass_mark = models.PositiveIntegerField(default=50)


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
