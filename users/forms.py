# users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
import re


def normalize_phone_number(phone):
    """Очищает и приводит номер к единому формату (начинается с 7)."""
    phone_digits = re.sub(r'\D', '', phone)
    if len(phone_digits) == 11 and phone_digits.startswith('8'):
        phone_digits = '7' + phone_digits[1:]
    return phone_digits


class ClientSignUpForm(UserCreationForm):
    first_name = forms.CharField(label="Ваше имя", max_length=150, required=True)

    # ▼▼▼ НОВОЕ ПОЛЕ EMAIL ▼▼▼
    email = forms.EmailField(label="Email", required=True)

    phone_number = forms.CharField(
        label="Номер телефона",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '+7 (___) ___-__-__', 'id': 'phone-mask-signup'})
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Добавляем email в список полей
        fields = ('first_name', 'email', 'phone_number')

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        normalized_phone = normalize_phone_number(phone)

        if CustomUser.objects.filter(username=normalized_phone).exists():
            raise forms.ValidationError("Этот номер телефона уже зарегистрирован.")
        return normalized_phone

    # ▼▼▼ ОБНОВЛЕННЫЙ МЕТОД SAVE ▼▼▼
    def save(self, commit=True):
        user = super().save(commit=False)
        # Устанавливаем username равным очищенному номеру телефона
        user.username = self.cleaned_data['phone_number']
        user.phone_number = self.cleaned_data['phone_number']
        user.first_name = self.cleaned_data['first_name']
        user.email = self.cleaned_data['email']  # Сохраняем email
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Номер телефона"
        self.fields['username'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите номер телефона',
            'id': 'phone-mask-login'
        })
        self.fields['password'].label = "Пароль"

    def clean_username(self):
        username = self.cleaned_data.get('username')
        return normalize_phone_number(username)