from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login_view'),
    path('login/', views.login_view, name='login_view'),
    path('cadastro/', views.cadastro_view, name='cadastro_view'),
    path('index/', views.index_view, name='index'),
    path('processar_csv/', views.processar_csv, name='processar_csv'),
]
