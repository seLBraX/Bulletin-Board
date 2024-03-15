from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy
from django.core.signing import BadSignature
from django.core.paginator import Paginator
from django.db.models import Q

from .models import AdvUser, SubRubric, Ad, Comment
from .forms import ChangeUserInfoForm, RegisterUserForm, SearchForm, AdForm, AIFormSet, UserCommentForm, GuestCommentForm
from .utilities import signer

def index(request):
    # Вывод последних 10 объявлений
    ads = Ad.objects.filter(is_active=True)[:10]
    context = {'ads': ads}
    return render(request, 'main/index.html', context)

def other_page(request, page):
    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request=request))

class BLoginView(LoginView):
    template_name = 'main/login.html'

@login_required
def profile(request):
    ads = Ad.objects.filter(author=request.user.pk)
    context = {'ads': ads}
    return render(request, 'main/profile.html', context)

class BLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'main/logout.html'

class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = AdvUser
    template_name = 'main/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Данные пользователя изменены'
    
    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)
    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

class BPasswordChangeView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    template_name = 'main/password_change.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль пользователя изменен'
    
class RegisterUserView(CreateView):
    model = AdvUser
    template_name = 'main/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main:register_done')

class RegisterDoneView(TemplateView):
    template_name = 'main/register_done.html'

def user_activate(request, sign):
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'main/bad_signature.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template = 'main/user_is_activated.html'
    else:
        template = 'main/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)

class DeleteUserView(LoginRequiredMixin, DeleteView):
    model = AdvUser
    template_name = 'main/delete_user.html'
    success_url = reverse_lazy('main:index')
    
    def setup(self, request, *args, **kwargs): # Сохраняем ключ текущего пользователя
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs): # Делаем выход для текущего пользователя и создаем всплывающее сообщение об успешном удалении
        logout(request)
        messages.add_message(request, messages.SUCCESS, 'Пользователь удален')
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None): # Отыскиваем по ключу пользователя, подлежащего удалению
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

def by_rubric(request, pk):
    rubric = get_object_or_404(SubRubric, pk=pk) # Название рубрики
    ads = Ad.objects.filter(is_active=True, rubric=pk) # Объявления, относящиеся к рубрике
    keyword = request.GET.get('keyword', False)
    if keyword:
        q = Q(title__icontains=keyword) | Q(content__icontains=keyword) # Фильтрация уже отобранных объявлений по введенному пользователю искомому слову
        ads = ads.filter(q)
    else:
        keyword = ''
    form = SearchForm(initial={'keyword': keyword}) # Вывод формы поиска
    paginator = Paginator(ads, 2) # Пагинатор, выводящий по 2 объявления
    page = request.GET.get('page', False)
    if page:
        page_num = page
    else:
        page_num = 1
    page = paginator.get_page(page_num)
    context = {'rubric': rubric, 'page': page, 'ads': page.object_list, 'form': form}
    return render(request, 'main/by_rubric.html', context)

def detail(request, rubric_pk, pk):
    ad = Ad.objects.get(pk=pk)
    ais = ad.additionalimage_set.all()
    comments = Comment.objects.filter(ad=pk, is_active=True)
    initial = {'ad': ad.pk} # В поле ad создаваемой формы ввода комментария заносим ключ выводящегося на странице объявления. С этим объявлением будет связан комментарий.
    if request.user.is_authenticated:
        initial['author'] = request.user.username
        form_class = UserCommentForm
    else:
        form_class = GuestCommentForm
    form = form_class(initial=initial)
    if request.method == 'POST':
        c_form = form_class(request.POST)
        if c_form.is_valid():
            c_form.save()
            messages.add_message(request, messages.SUCCESS, 'Comment added')
        else:
            form = c_form # Переносим форму из переменной c_form в переменную form. Эта форма, хранящая некорректные данные и сообщения об ошибках ввода, будет выведена на экран,
                          # и посетитель сразу увидит, что он ввел не так.
            messages.add_message(request, messages.WARNING, 'No comment added')
    context = {'ad': ad, 'ais': ais, 'comments': comments, 'form': form}
    return render(request, 'main/detail.html', context)

@login_required
def profile_ad_detail(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    ais = ad.additionalimage_set.all()
    comments = Comment.objects.filter(ad=pk, is_active=True)
    context = {'ad': ad, 'ais': ais, 'comments': comments}
    return render(request, 'main/profile_ad_detail.html', context)

@login_required
def profile_ad_add(request):
    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES)
        if form.is_valid():
            ad = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=ad)
            if formset.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS, 'Ad added')
                return redirect('main:profile')
    else:
        form = AdForm(initial={'author': request.user.pk})
        formset = AIFormSet()
    context = {'form': form, 'formset': formset}
    return render(request, 'main/profile_ad_add.html', context)

@login_required
def profile_ad_change(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            ad = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=ad)
            if formset.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS, 'Ad edited')
                return redirect('main:profile')
    else:
        form = AdForm(instance=ad)
        formset = AIFormSet(instance=ad)
    context = {'form': form, 'formset': formset}
    return render(request, 'main/profile_ad_change.html', context)

@login_required
def profile_ad_delete(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    if request.method == 'POST':
        ad.delete()
        messages.add_message(request, messages.SUCCESS, 'Ad deleted')
        return redirect('main:profile')
    else:
        context = {'ad': ad}
        return render(request, 'main/profile_ad_delete.html', context)


