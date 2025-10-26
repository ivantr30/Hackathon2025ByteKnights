from django.db import models

from django.conf import settings
from django.utils.text import slugify
from pytils.translit import slugify

class Room(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название комнаты")
    slug = models.SlugField(max_length=100, unique=True, blank=True, allow_unicode=False) 
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Комната"
        verbose_name_plural = "Комнаты"
        ordering = ['-created_at']

class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages', verbose_name="Комната")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    username_at_time = models.CharField(max_length=150, verbose_name="Имя пользователя в момент отправки")
    text = models.TextField(verbose_name="Текст сообщения")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")

    def __str__(self):
        return f"Сообщение от {self.username_at_time} в {self.room.name}"
    
    class Meta:
        verbose_name = "Сообщение чата"
        verbose_name_plural = "Сообщения чата"
        ordering = ['timestamp']
class ArchivedRoom(models.Model):
    """Модель для хранения информации и лога чата архивированной комнаты."""
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)
    creator_username = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField()
    archived_at = models.DateTimeField(auto_now_add=True)
    
    chat_log = models.FileField(upload_to='chat_logs/', null=True, blank=True, verbose_name="Лог чата")

    def __str__(self):
        return f"{self.name} (архив от {self.archived_at.strftime('%Y-%m-%d %H:%M')})"
        
    class Meta:
        verbose_name = "Архивная комната"
        verbose_name_plural = "Архивные комнаты"
        ordering = ['-archived_at']