from . import views
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.upload_file, name='fileup'),
    path('process/', views.process, name='process'),
    path('process_data_ajax/', views.process_data_ajax, name='process_data_ajax'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('download-output-file/', views.download_output_file, name='download_output_file'),

]