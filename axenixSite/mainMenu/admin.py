from django.contrib import admin
from .models import Room, ArchivedRoom, ChatMessage

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'created_at')

@admin.register(ArchivedRoom)
class ArchivedRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator_username', 'created_at', 'archived_at', 'chat_log')
    readonly_fields = ('name', 'slug', 'creator_username', 'created_at', 'archived_at', 'chat_log')
    
    def has_add_permission(self, request):
        return False
admin.site.register(ChatMessage)