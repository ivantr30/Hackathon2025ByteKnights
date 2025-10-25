from django.db import models

from django.conf import settings
from django.utils.text import slugify

class Room(models.Model):
    """
    Модель для комнаты конференции.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Название комнаты")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="created_rooms",
        verbose_name="Создатель"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

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