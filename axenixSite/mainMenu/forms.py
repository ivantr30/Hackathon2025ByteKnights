from django import forms
from .models import Room

class RoomCreationForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Введите название новой комнаты'
            })
        }