from django.urls import path
from . import views
from django.conf.urls import url
from core import views

app_name = 'core'

urlpatterns = [
	path('', views.search_between_date, name='search_between_date'),
	url(r'^register/$',views.register,name='register'),
	url(r'^user_login/$',views.user_login,name='user_login'),
]