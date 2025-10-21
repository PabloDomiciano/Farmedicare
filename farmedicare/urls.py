"""
URL configuration for farmedicare project.

The `urlpatterns` list routes URLs to views. For more information please see:
Examples:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Function views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
    1. Add an import:  from my_app import views
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
    1. Import the include() function: from django.urls import include, path
Including another URLconf
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('', include('paginas.urls')),
    path('pagina_movimentacao/', include('movimentacao.urls')),
    path('pagina_medicamento/', include('medicamento.urls')),
    path('perfis/', include('perfis.urls')),
]