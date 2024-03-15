from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from captcha.fields import CaptchaField

from .models import AdvUser, SuperRubric, SubRubric, Ad, AdditionalImage, Comment
from .apps import user_registered

class ChangeUserInfoForm(forms.ModelForm):
    # Полное объявление поля email, т.к. хотим сделать поле email обязательным для заполнения1
    email = forms.EmailField(required=True, label='Адрес электронной почты')
    
    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'first_name', 'last_name', 'send_messages')

class RegisterUserForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адрес электронной почты')
    password1 = forms.CharField(required=True, label='Пароль', widget=forms.PasswordInput, help_text=password_validation.password_validators_help_text_html())
    password2 = forms.CharField(required=True, label='Пароль (повторно)', widget=forms.PasswordInput, help_text='Введите тот же самый пароль еще раз для проверки')

    def clean_password1(self):
        password1 = self.cleaned_data['password1']
        if password1:
            password_validation.validate_password(password1)
        return password1

    def clean(self):
        super().clean()
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            errors = {'password2': ValidationError('Введенные пароли не совпадают', code='password_mismatch')}
            raise ValidationError(errors)
            
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        user.is_activated = False
        if commit:
            user.save()
        user_registered.send(RegisterUserForm, instance=user)
        return user
    
    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'send_messages')

class SubRubricForm(forms.ModelForm):
    # Для Подрубрик поле super_rubric обязательно для заполнения:
    super_rubric = forms.ModelChoiceField(required=True, queryset=SuperRubric.objects.all(), empty_label=None, label='Главная рубрика')

    class Meta:
        model = SubRubric
        fields = '__all__'

# Форма поиска для главной страницы
class SearchForm(forms.Form):
    keyword = forms.CharField(required=False, max_length=40, label='')

class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = '__all__'
        widgets = {'author': forms.HiddenInput}

AIFormSet = inlineformset_factory(Ad, AdditionalImage, fields='__all__')

# Форма комментариев для зарегистрированного пользователя
class UserCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ('is_active', )
        widgets = {'ad': forms.HiddenInput}

# Форма комментариев для гостей сайта
class GuestCommentForm(forms.ModelForm):
    captcha = CaptchaField(label='Type in text from pic', error_messages={'invalid': 'Wrong Text'})
    
    class Meta:
        model = Comment
        exclude = ('is_active', )
        widgets = {'ad': forms.HiddenInput}

