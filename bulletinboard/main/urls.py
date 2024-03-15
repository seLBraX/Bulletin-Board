from django.urls import path

from .views import index, other_page, BLoginView, profile, BLogoutView, ChangeUserInfoView, BPasswordChangeView, RegisterUserView, RegisterDoneView, user_activate, DeleteUserView
from .views import by_rubric, detail, profile_ad_detail, profile_ad_add, profile_ad_change, profile_ad_delete

app_name = 'main'
urlpatterns = [
    path('', index, name='index'),
    path('<int:rubric_pk>/<int:pk>/', detail, name='detail'),
    path('<int:pk>/', by_rubric, name='by_rubric'),
    path('<str:page>/', other_page, name='other'),
    path('accounts/register/activate/<str:sign>/', user_activate, name='register_activate'),
    path('accounts/register/done/', RegisterDoneView.as_view(), name='register_done'),
    path('accounts/register/', RegisterUserView.as_view(), name='register'),
    path('accounts/login/', BLoginView.as_view(), name='login'),
    path('accounts/profile/delete/', DeleteUserView.as_view(), name='profile_delete'),
    path('accounts/profile/change/', ChangeUserInfoView.as_view(), name='profile_change'),
    path('accounts/profile/change/<int:pk>/', profile_ad_change, name='profile_ad_change'),
    path('accounts/profile/delete/<int:pk>/', profile_ad_delete, name='profile_ad_delete'),
    path('account/profile/add/', profile_ad_add, name='profile_ad_add'),
    path('accounts/profile/<int:pk>/', profile_ad_detail, name='profile_ad_detail'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/logout/', BLogoutView.as_view(), name='logout'),
    path('accounts/password/change/', BPasswordChangeView.as_view(), name='password_change'),

]
