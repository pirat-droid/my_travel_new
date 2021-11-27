from django.urls import path
from .views import *
from django.views.decorators.cache import cache_page

urlpatterns = [
    path('', ListPostView.as_view(), name='home'),
    path('sing-in/', UserLoginView.as_view(), name='sign_in'),
    path('sing-up/', RegisterCreateView.as_view(), name='sign_up'),
    path('logout/', logout_view, name='logout'),
    path('reset-password/', ResetPasswordCreateView.as_view(), name='reset_password'),
    path('change-password/<slug:uid64>/<slug:token>/', change_password_view, name='change_password'),
    path('activate/<slug:uid64>/<slug:token>/', activate, name='activate'),
    path('profile/<slug:url>/', profile_view, name='profile'),
    path('create-post/', CreateNewPostView.as_view(), name='create-post'),
    path('post/<slug:url>/', PostDetailView.as_view(), name='post'),
]
