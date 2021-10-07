from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Task, User


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'title',
        'description',
        'created',
        'finished',
    )
    empty_value_display = '-пусто-'
    raw_id_fields = ('performers',)


@admin.register(User)
class User(UserAdmin):
    list_display = (
        'pk',
        'username',
        'full_name'
    )
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('full_name',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('full_name',)}),
    )
    search_fields = ('username',)
    empty_value_display = '-пусто-'
