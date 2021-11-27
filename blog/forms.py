import datetime
import sys
from io import BytesIO

from PIL import Image
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField, AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from .models import CountryModel, SexModel, PostModel

from django.utils.translation import gettext_lazy as _

User = get_user_model()


class RegisterForm(forms.ModelForm):
    """Форма регистрации пользователя"""
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_2 = forms.CharField(label='Повторить пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['email', ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        """Проверка email"""
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if qs.exists():
            raise forms.ValidationError("Эта почта уже зарегистрированна")
        return email

    def clean(self):
        """Проверка на совпадение паролей"""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_2 = cleaned_data.get("password_2")
        if password is not None and password != password_2:
            self.add_error("password_2", "Пароли не совпадают")
        return cleaned_data


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Электронная почта', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserAdminCreationForm(forms.ModelForm):
    """
    A form for creating new users. Includes all the required
    fields, plus a repeated password.
    """
    password = forms.CharField(widget=forms.PasswordInput)
    password_2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'sex', 'birthday']

    def clean(self):
        """Verify both passwords match."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_2 = cleaned_data.get("password_2")
        if password is not None and password != password_2:
            self.add_error("password_2", "Пароли не совпадают")
        return cleaned_data

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    """Форма обновления информации о пользователе.
    Пароль в хэш формате.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ['email', 'password', 'is_active', 'admin', 'sex']

    def clean_password(self):
        """Возвращает начальное значение пароля.
        Это делается, для того, что поле не имеетдостыпа
         к начального значению"""
        return self.initial["password"]


class UserChangeForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['email', 'sex', 'country', 'avatar', 'birthday']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'sex': forms.Select(attrs={'class': 'form-select'}),
            'birthday': forms.DateInput(attrs={'class': 'form-control',
                                               'placeholder': datetime.date.today().strftime("%d.%m.%Y")}),
            'avatar': forms.FileInput(attrs={'class': 'form-control',
                                              'type': 'file'})
        }

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        image_temporary = Image.open(self.cleaned_data.get("avatar"))
        if image_temporary.mode != 'RGB':
            image_temporary = image_temporary.convert('RGB')
        output_io_stream = BytesIO()
        image_temporary.thumbnail((50, 50), Image.ANTIALIAS)
        image_temporary.save(output_io_stream, format='JPEG', quality=75)
        output_io_stream.seek(0)
        instance.avatar = InMemoryUploadedFile(output_io_stream, 'ImageField', "avatar.jpg", 'image/jpeg',
                                               sys.getsizeof(output_io_stream), None)
        instance.save()
        return instance


class ChangePasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    password1 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password1 = cleaned_data.get("password1")
        if password is not None and password != password1:
            self.add_error("password", "Пароли не совпадают")
        return cleaned_data


class CreatePostForm(forms.ModelForm):
    images = forms.ImageField(label='Изображения',
                              widget=forms.ClearableFileInput(attrs={'class': 'form-control',
                                                                     'multiple': True}))
    lon = forms.FloatField(localize=True, widget=forms.TextInput(attrs={'class': 'form-control',
                                                                        'hidden': True}))
    lat = forms.FloatField(localize=True, widget=forms.TextInput(attrs={'class': 'form-control',
                                                                        'hidden': True}))

    class Meta:
        model = PostModel
        fields = ['title', 'text', 'tag', 'images', 'emoji', 'lon', 'lat']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control',
                                            'type': 'text'}),
            'tag': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'text': forms.Textarea(attrs={'class': 'form-control'}),
        }

    # Для  SQLite, не проверяет на этапе моделей длину
    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) > 50:
            raise ValidationError('Длина заголовка не должна превышать 50 символов')
        return title

    # Для  SQLite, не проверяет на этапе моделей длину
    def clean_text(self):
        text = self.cleaned_data['text']
        if len(text) > 150:
            raise ValidationError('Длина текста не должна превышать 150 символов')
        return text
