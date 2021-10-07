from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    full_name = models.CharField('Полное имя', max_length=30)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username


class Task(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='author_tasks',
        verbose_name='Автор',
        null=True
    )
    performers = models.ManyToManyField(
        User,
        related_name='performers_tasks',
        verbose_name='Исполнители'
    )
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', max_length=400)
    finished = models.DateField(
        'Планируемая дата завершения',
    )
    file = models.FileField(
        'Прикрепленный файл',
        upload_to='task/',
        blank=True,
        null=True,
    )
    created = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created']

    def __str__(self):
        return self.title
