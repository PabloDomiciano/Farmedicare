from django.urls import path
from .views import RelatoriosView, gerar_pdf_relatorio, api_notificacoes, notificacoes_page

urlpatterns = [
    path('dashboard/', RelatoriosView.as_view(), name='dashboard_relatorios'),
    path('gerar-pdf/', gerar_pdf_relatorio, name='gerar_pdf_relatorio'),
    path('api/notificacoes/', api_notificacoes, name='api_notificacoes'),
    path('notificacoes/', notificacoes_page, name='notificacoes_unificadas'),
]
