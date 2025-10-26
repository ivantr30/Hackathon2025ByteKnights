import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from json import JSONDecodeError
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from .models import Room  
from .forms import RoomCreationForm
from django.urls import reverse
from django.views.decorators.http import require_POST


@csrf_exempt
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"message": "Требуется POST"}, status=405)

    try:
        data = json.loads(request.body)
    except JSONDecodeError:
        return JsonResponse({"message": "Некорректный JSON"}, status=400)

    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return JsonResponse({"message": "Имя и пароль обязательны"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"message": "Пользователь с таким именем уже существует"}, status=409)

    user = User.objects.create_user(username=username, password=password)

    return JsonResponse({
        "message": f"Пользователь {username} успешно зарегистрирован!",
        "redirect_url": reverse('mainMenu:join_page'), 
    }, status=201)


@csrf_exempt
def run_function_join(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")
        except (json.JSONDecodeError, AttributeError):
             return JsonResponse({"success": False, "message": "Некорректный запрос"}, status=400)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({
                "success": True, 
                "message": f"Добро пожаловать, {username}!",
                "redirect_url": reverse('mainMenu:room_list') 
            })
        else:
            return JsonResponse({
                "success": False, 
                "message": "Неверное имя пользователя или пароль"
            }, status=401)
    
    return JsonResponse({"success": False, "message": "Требуется POST-запрос"}, status=405)
        

def join_page(request):
	return render(request, 'Join.html')

def reg_page(request): 
	return render(request, 'Reg.html')



@login_required
def main_view(request):
    form = RoomCreationForm()
    if request.method == 'POST':
        form = RoomCreationForm(request.POST)
        if form.is_valid():
            new_room = form.save(commit=False)
            new_room.creator = request.user
            new_room.save()
            return redirect('mainMenu:room_detail', slug=new_room.slug)
    
    return render(request, 'index.html', {'form': form})

@login_required
@require_POST
def check_room_view(request):
    try:
        data = json.loads(request.body)
        room_name = data.get('room_name')

        if not room_name:
            return JsonResponse({'exists': False, 'error': 'Название комнаты не предоставлено.'}, status=400)

        room = Room.objects.filter(name__iexact=room_name).first()

        if room:
            return JsonResponse({'exists': True, 'slug': room.slug})
        else:
            # Если не найдена
            return JsonResponse({'exists': False})

    except json.JSONDecodeError:
        return JsonResponse({'exists': False, 'error': 'Некорректный запрос.'}, status=400)
    except Exception as e:
        return JsonResponse({'exists': False, 'error': str(e)}, status=500)

@login_required
def room_view(request, slug):
        room = get_object_or_404(Room, slug=slug)
        
        return render(request, 'room.html', {
            'room': room
        })
    

