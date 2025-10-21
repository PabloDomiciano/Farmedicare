/**
 * Sistema de Notificações Popup - Estilo YouTube
 * Controla abertura/fechamento e carregamento de notificações
 */

document.addEventListener('DOMContentLoaded', function() {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationPopup = document.getElementById('notificationPopup');
    const closePopup = document.getElementById('closePopup');
    const notificationPopupBody = document.getElementById('notificationPopupBody');
    
    let notificacoesCarregadas = false;

    // Abrir/Fechar popup ao clicar no sino
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const isOpen = notificationPopup.classList.contains('show');
            
            if (isOpen) {
                fecharPopup();
            } else {
                abrirPopup();
            }
        });
    }

    // Fechar com botão X
    if (closePopup) {
        closePopup.addEventListener('click', function(e) {
            e.stopPropagation();
            fecharPopup();
        });
    }

    // Fechar ao clicar fora
    document.addEventListener('click', function(e) {
        if (notificationPopup && notificationPopup.classList.contains('show')) {
            if (!notificationPopup.contains(e.target) && !notificationBtn.contains(e.target)) {
                fecharPopup();
            }
        }
    });

    // Prevenir fechamento ao clicar dentro do popup
    if (notificationPopup) {
        notificationPopup.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    function abrirPopup() {
        notificationPopup.classList.add('show');
        notificationBtn.classList.add('active');
        
        // Carregar notificações apenas uma vez
        if (!notificacoesCarregadas) {
            carregarNotificacoes();
            notificacoesCarregadas = true;
        }
    }

    function fecharPopup() {
        notificationPopup.classList.remove('show');
        notificationBtn.classList.remove('active');
    }

    function carregarNotificacoes() {
        // Fazer requisição AJAX para buscar notificações
        fetch('/pagina_medicamento/api/notificacoes/')
            .then(response => response.json())
            .then(data => {
                renderizarNotificacoes(data);
            })
            .catch(error => {
                console.error('Erro ao carregar notificações:', error);
                notificationPopupBody.innerHTML = `
                    <div class="notification-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Erro ao carregar notificações</p>
                        <small>Tente novamente mais tarde</small>
                    </div>
                `;
            });
    }

    function renderizarNotificacoes(data) {
        if (!data.notificacoes || data.notificacoes.length === 0) {
            notificationPopupBody.innerHTML = `
                <div class="notification-empty">
                    <i class="fas fa-check-circle"></i>
                    <p>Nenhuma notificação</p>
                    <small>Tudo em ordem com seus medicamentos!</small>
                </div>
            `;
            return;
        }

        // Limitar a 5 notificações no popup (as mais urgentes)
        const notificacoesLimitadas = data.notificacoes.slice(0, 5);
        
        let html = '<div class="notification-list">';
        
        notificacoesLimitadas.forEach(notif => {
            const icone = getIconeNotificacao(notif.tipo);
            const cor = getCorNotificacao(notif.tipo);
            
            html += `
                <div class="notification-item ${notif.tipo}" data-tipo="${notif.tipo}">
                    <div class="notification-icon" style="color: ${cor};">
                        <i class="fas ${icone}"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">${notif.medicamento}</div>
                        <div class="notification-message">${getMensagemCurta(notif)}</div>
                        <div class="notification-time">${getTempoRelativo(notif.validade)}</div>
                    </div>
                    ${notif.tipo === 'vencido' ? '<div class="notification-pulse"></div>' : ''}
                </div>
            `;
        });
        
        html += '</div>';
        
        notificationPopupBody.innerHTML = html;
    }

    function getIconeNotificacao(tipo) {
        const icones = {
            'vencido': 'fa-times-circle',
            'muito_proximo': 'fa-exclamation-triangle',
            'proximo': 'fa-clock'
        };
        return icones[tipo] || 'fa-bell';
    }

    function getCorNotificacao(tipo) {
        const cores = {
            'vencido': '#ef5350',
            'muito_proximo': '#ff9800',
            'proximo': '#ffa726'
        };
        return cores[tipo] || '#42a5f5';
    }

    function getMensagemCurta(notif) {
        if (notif.dias_para_vencer < 0) {
            return `Venceu há ${notif.dias_vencido_abs} dias`;
        } else if (notif.dias_para_vencer === 0) {
            return 'Vence hoje!';
        } else if (notif.dias_para_vencer === 1) {
            return 'Vence amanhã!';
        } else {
            return `Vence em ${notif.dias_para_vencer} dias`;
        }
    }

    function getTempoRelativo(validade) {
        const dataValidade = new Date(validade);
        return `Validade: ${dataValidade.toLocaleDateString('pt-BR')}`;
    }
});
