from django.db import models

from django.conf import settings
from django.utils.text import slugify
from pytils.translit import slugify

class Room(models.Model):
    # ... ваши поля name, creator, created_at ...
    name = models.CharField(max_length=100, unique=True, verbose_name="Название комнаты")
    slug = models.SlugField(max_length=100, unique=True, blank=True, allow_unicode=False) # allow_unicode=False важно!
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    # Переопределяем метод save, чтобы использовать правильный slugify
    def save(self, *args, **kwargs):
        if not self.slug:
            # Теперь slugify будет правильно транслитерировать кириллицу
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Комната"
        verbose_name_plural = "Комнаты"
        ordering = ['-created_at']