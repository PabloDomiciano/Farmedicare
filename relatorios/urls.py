from django.urls import path
from .views import RelatoriosView, gerar_pdf_relatorio

urlpatterns = [
    path('dashboard/', RelatoriosView.as_view(), name='dashboard_relatorios'),
    path('gerar-pdf/', gerar_pdf_relatorio, name='gerar_pdf_relatorio'),
]
