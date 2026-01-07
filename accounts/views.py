from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash # Імпортовано update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages # Імпортовано messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from activity.models import ActivityLog
from .forms import UserRegistrationForm, UserLoginForm, EditProfileForm, ChangePasswordForm # Імпортовано ChangePasswordForm


def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Реєстрація успішна. Ласкаво просимо!")
            return redirect("home")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/registration.html", {"form": form, "page": "register"})


def login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = UserLoginForm()
    return render(request, "accounts/login.html", {"form": form, "page": "login"})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Ви успішно вийшли з облікового запису.")
    return redirect("login")


@login_required
def profile_view(request):
    context = {
        "page": "profile",
        "user": request.user
    }
    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile_view(request):
    user = request.user
    
    # Ініціалізація форм
    profile_form = EditProfileForm(instance=user)
    # Ініціалізація форми пароля для відображення в модальному вікні
    password_form = ChangePasswordForm(user=request.user) 
    
    # Змінна для автоматичного відкриття модального вікна
    open_password_modal = False 

    if request.method == "POST":
        # Логіка обробки POST-запиту
        
        if 'profile_submit' in request.POST:
            profile_form = EditProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Дані профілю успішно оновлено!")
                return redirect("edit_profile") 
            else:
                messages.error(request, "Помилка при оновленні даних профілю. Перевірте поля.")
                # Форма пароля залишається чистою
                password_form = ChangePasswordForm(user=request.user) 

        elif 'password_submit' in request.POST:
            password_form = ChangePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  
                messages.success(request, 'Пароль успішно змінено!')
                # Перенаправляємо, щоб очистити форму
                return redirect('edit_profile') 
            else:
                messages.error(request, 'Помилка при зміні пароля. Будь ласка, перевірте поточний та новий паролі.')
                # Якщо є помилки, встановлюємо прапорець для автоматичного відкриття модального вікна
                open_password_modal = True
                # Профільна форма залишається чистою
                profile_form = EditProfileForm(instance=user) 

    # Перевіряємо, чи є GET-параметр для відкриття модального вікна (наприклад, з profile.html)
    if request.GET.get('action') == 'change_password':
        open_password_modal = True

    # Якщо є помилки, модальне вікно має бути відкрито (це вже встановлено в POST-обробнику)
    
    context = {
        "form": profile_form,
        "password_form": password_form,
        "page": "edit_profile",
        "open_password_modal": open_password_modal # Передаємо змінну для JS
    }
    return render(request, "accounts/edit_profile.html", context)


@login_required
def delete_profile_view(request):
    error = None

    if request.method == "POST":
        password = request.POST.get("password")

        user = authenticate(username=request.user.username, password=password)

        if user is None:
            error = "Невірний пароль."
            messages.error(request, "Невірний пароль.")
        else:
            request.user.delete()
            messages.success(request, "Ваш обліковий запис було видалено.")
            return redirect("login")

    return render(request, "accounts/delete_profile.html", {"error": error})


def home_view(request):
    if not request.user.is_authenticated:
        context = {"page": "home"}
        return render(request, "home.html", context)

    # 1. Отримуємо параметри з URL
    period = request.GET.get("period", "today") # За замовчуванням 'all', щоб бачити історію
    page_number = request.GET.get('page')
    now = timezone.now()

    # 2. Початковий запит із оптимізацією та сортуванням
    # Використовуємо select_related, щоб не перевантажувати базу запитами про користувача
    queryset = ActivityLog.objects.filter(user=request.user).select_related('user').order_by('-created_at')

    # 3. Фільтрація за періодом
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        queryset = queryset.filter(created_at__gte=start_date)
    elif period == "week":
        start_date = now - timedelta(days=7)
        queryset = queryset.filter(created_at__gte=start_date)
    elif period == "month":
        start_date = now - timedelta(days=30)
        queryset = queryset.filter(created_at__gte=start_date)

    # 4. Пагінація (наприклад, 15 записів на сторінку)
    paginator = Paginator(queryset, 20) 
    
    try:
        logs = paginator.page(page_number)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    context = {
        "page": "home",
        "logs": logs,            # Це об'єкт сторінки для циклу в HTML
        "filter_period": period, # Щоб підсвічувати активну кнопку фільтра
    }
    return render(request, "home.html", context)