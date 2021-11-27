from django.contrib.auth.views import LoginView, PasswordResetView
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

from .forms import RegisterForm, ChangePasswordForm, UserChangeForm, CreatePostForm, LoginUserForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from .token import activation_token
from django.contrib.auth.forms import PasswordResetForm
from .models import PostModel, TagModel, ImagePostModel
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin

User = get_user_model()


class ListPostView(LoginRequiredMixin, ListView):
    """Домашняя страница с отображением списка 4 последних постов"""
    model = PostModel
    paginate_by = 4
    template_name = 'blog/index.html'
    context_object_name = 'posts'
    login_url = reverse_lazy('sign_in')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Домашняя'
        for post in context['posts']:
            context['image'] = ImagePostModel.objects.filter(post_id=post.id).first()
        return context

    def get_queryset(self):
        return PostModel.objects.order_by('-datetime_create').prefetch_related('tag')


class PostDetailView(DetailView):
    """Представление страницы с детальным описание поста"""
    model = PostModel
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    slug_url_kwarg = 'url'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Детально о посте - ' + str(context['post'])
        context['images'] = ImagePostModel.objects.filter(post_id=context['post'].id)
        context['col_images'] = len(context['images'])
        return context


class UserLoginView(LoginView):
    """Представление страницы с логированием"""
    form_class = LoginUserForm
    template_name = 'blog/sign_in.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Вход'
        return context

    def get_success_url(self):
        return reverse_lazy('home')


class RegisterCreateView(CreateView):
    form_class = RegisterForm
    template_name = 'blog/sign_up.html'

    # success_url = reverse_lazy('sign_in')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистрация'
        return context

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = User.objects.create_user(email=email, password=password)
        user.is_active = False
        user.save()
        current_site = get_current_site(self.request)
        subject = 'Пожалуйста активируйте свой аккаунт'
        message = render_to_string('blog/activation_request.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': activation_token.make_token(user),
        })
        user.email_user(subject, message)
        return render(self.request, 'blog/message.html', {
            'message': 'Ссылка для активации отправлена на указанную Вами почту ' + form.cleaned_data[
                'email'] + '. Пожалуйста, проверьте свою почту.'})


class ResetPasswordCreateView(PasswordResetView):
    """Страница запроса на смену пароля.
    Проверяет на регситрацию почту,
    если почта не зарегистрированна то не чего не делает(надо, что-то дописать),
    если почта уже зарегистрированна то отправляет письмо на указанный адрес с уникальной ссылкой
    """
    form_class = PasswordResetForm
    template_name = 'blog/reset_password.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистрация'
        return context

    def form_valid(self, form):
        qs = User.objects.filter(email=form.cleaned_data['email'])
        if qs.exists():
            for user in qs:
                current_site = get_current_site(self.request)
                subject = 'Смена пароля ' + str(current_site)
                message = render_to_string('blog/password_request.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': activation_token.make_token(user),
                })
                user.email_user(subject, message)
                return render(self.request, 'blog/message.html', {
                    'message': 'Ссылка для смены пароля отправлена на указанную Вами почту ' + form.cleaned_data[
                        'email'] + '. Пожалуйста, проверьте свою почту.'})


def change_password_view(request, uid64, token):
    """Проверка уникальной ссылки при сммене пароля.
    Страница ввода нового пароля"""
    if request.user.is_authenticated:
        return redirect(to='home')

    try:
        uid = force_text(urlsafe_base64_decode(uid64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user is not None and activation_token.check_token(user, token):
        if request.method == 'POST':
            form = ChangePasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['password'])
                user.save()
                return redirect(to='sign_in')
        else:
            form = ChangePasswordForm()
    else:
        return render(request, 'blog/message.html',
                      {'message': 'Данная ссылка на смену пароля не актуальна! Попробуйте запросить смену пароля '
                                  'повторно'})
    return render(request, 'blog/change_password.html', {'form': form})


def activate(request, uid64, token):
    """Проверка уникальной ссылки при активации"""
    if request.user.is_authenticated:
        return redirect(to='home')

    try:
        uid = force_text(urlsafe_base64_decode(uid64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user is not None and activation_token.check_token(user, token):
        user.is_active = True
        user.signup_confirmed = True
        user.save()
        login(request, user)
        return redirect(to='home')
    else:
        return render(request, 'blog/message.html',
                      {'message': 'Данная ссылка на активацию не актуальна! Попробуйте пройти регистрация заново'})


def profile_view(request, url):
    """Страница изменения профиля"""
    if request.method == 'POST':
        form = UserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(to='home')
    else:
        form = UserChangeForm(initial={'email': request.user.email,
                                       'sex': request.user.sex,
                                       'country': request.user.country,
                                       'birthday': request.user.birthday})
    return render(request, 'blog/profile.html', {'user': request.user,
                                                 'form': form})


@login_required
def logout_view(request):
    """Выход из аккаунта"""
    logout(request)
    return redirect('sign_in')


class CreateNewPostView(CreateView):
    """Представление страницы создание нового поста"""
    model = PostModel
    form_class = CreatePostForm
    template_name = 'blog/create_post.html'
    context_object_name = 'post_form'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание поста'
        return context

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        post.save()
        images = self.request.FILES.getlist('images')
        for image in images:
            ImagePostModel.objects.create(post=post,
                                          image=image)
        return super().form_valid(form)
