// ========== SISTEMA DE NOTIFICAÇÕES ESTILO FACEBOOK ==========

document.addEventListener('DOMContentLoaded', function() {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationPopup = document.getElementById('notificationPopup');
    const closePopup = document.getElementById('closePopup');
    const notificationBody = document.getElementById('notificationPopupBody');
    
    if (!notificationBtn || !notificationPopup) return;
    
    let notificacoesCarregadas = false;
    
    // Carregar contador inicial ao carregar a página
    fetch('/relatorios/api/notificacoes/')
        .then(response => response.json())
        .then(data => {
            atualizarBadge(data.total);
        })
        .catch(error => console.error('Erro ao carregar contador:', error));
    
    // Abrir popup de notificações
    notificationBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        
        if (notificationPopup.classList.contains('show')) {
            notificationPopup.classList.remove('show');
        } else {
            notificationPopup.classList.add('show');
            
            if (!notificacoesCarregadas) {
                carregarNotificacoes();
                notificacoesCarregadas = true;
            }
        }
    });
    
    // Fechar popup
    if (closePopup) {
        closePopup.addEventListener('click', function() {
            notificationPopup.classList.remove('show');
        });
    }
    
    // Fechar ao clicar fora
    document.addEventListener('click', function(e) {
        if (!notificationPopup.contains(e.target) && !notificationBtn.contains(e.target)) {
            notificationPopup.classList.remove('show');
        }
    });
});

function carregarNotificacoes() {
    const notificationBody = document.getElementById('notificationPopupBody');
    
    // Mostrar loading
    notificationBody.innerHTML = `
        <div class="notification-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Carregando notificações...</p>
        </div>
    `;
    
    fetch('/relatorios/api/notificacoes/')
        .then(response => response.json())
        .then(data => {
            renderizarNotificacoes(data);
            atualizarBadge(data.total);
        })
        .catch(error => {
            console.error('Erro:', error);
            notificationBody.innerHTML = `
                <div class="notification-empty">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Erro ao carregar notificações</p>
                </div>
            `;
        });
}

function renderizarNotificacoes(data) {
    const notificationBody = document.getElementById('notificationPopupBody');
    
    if (!data.notificacoes || data.notificacoes.length === 0) {
        notificationBody.innerHTML = `
            <div class="notification-empty">
                <i class="fas fa-check-circle"></i>
                <h3>Tudo em ordem!</h3>
                <p>Nenhuma notificação pendente 🎉</p>
            </div>
        `;
        return;
    }
    
    // Limitar a 10 notificações no popup
    const notificacoesLimitadas = data.notificacoes.slice(0, 10);
    
    let html = '';
    notificacoesLimitadas.forEach(notif => {
        html += criarItemNotificacao(notif);
    });
    
    notificationBody.innerHTML = html;
}

function criarItemNotificacao(notif) {
    const pulso = notif.categoria === 'vencido' ? 
        `<div class="notification-pulse" style="background: ${notif.cor};"></div>` : '';
    
    let detalhes = '';
    let subtitulo = '';
    let btnAcao = '';
    
    // Formato estilo Facebook: detalhes específicos por tipo
    if (notif.tipo.includes('receita') || notif.tipo.includes('despesa')) {
        const tipoTexto = notif.tipo.includes('receita') ? 'Receita' : 'Despesa';
        const valorFormatado = formatarMoeda(notif.valor);
        
        subtitulo = `<strong>Parcela ${notif.parcela_numero}/${notif.total_parcelas}</strong> - R$ ${valorFormatado}`;
        
        detalhes = `
            <div class="notif-details">
                <div class="notif-detail-row">
                    <i class="fas fa-building" style="color: ${notif.cor};"></i>
                    <span><strong>${notif.parceiro || 'Sem parceiro'}</strong></span>
                </div>
                <div class="notif-detail-row">
                    <i class="fas fa-tag" style="color: ${notif.cor};"></i>
                    <span>${notif.categoria_nome || 'Sem categoria'}</span>
                </div>
                <div class="notif-detail-row">
                    <i class="fas fa-calendar" style="color: ${notif.cor};"></i>
                    <span>Vencimento: ${notif.data_vencimento || 'Não informado'}</span>
                </div>
                ${notif.descricao ? `
                <div class="notif-detail-row">
                    <i class="fas fa-align-left" style="color: ${notif.cor};"></i>
                    <span>${notif.descricao}</span>
                </div>
                ` : ''}
                <div class="notif-detail-row">
                    <i class="fas fa-home" style="color: ${notif.cor};"></i>
                    <span>${notif.fazenda || 'Sem fazenda'}</span>
                </div>
            </div>
        `;
        
        // Botão de ação para parcelas
        if (notif.id_parcela) {
            btnAcao = `
                <a href="/pagina_movimentacao/editar/parcela/${notif.id_parcela}/" 
                   style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; 
                          background: ${notif.cor}; color: white; border-radius: 6px; text-decoration: none; 
                          font-size: 12px; font-weight: 600; margin-top: 8px; transition: all 0.2s;"
                   onmouseover="this.style.opacity='0.8'"
                   onmouseout="this.style.opacity='1'">
                    <i class="fas fa-hand-holding-usd"></i>
                    Realizar Pagamento
                </a>
            `;
        }
    } else if (notif.tipo.includes('medicamento')) {
        subtitulo = `<strong>${notif.medicamento}</strong>`;
        
        detalhes = `
            <div class="notif-details">
                <div class="notif-detail-row">
                    <i class="fas fa-home" style="color: ${notif.cor};"></i>
                    <span>${notif.fazenda || 'Sem fazenda'}</span>
                </div>
                <div class="notif-detail-row">
                    <i class="fas fa-hashtag" style="color: ${notif.cor};"></i>
                    <span>Lote: ${notif.lote || 'Sem lote'}</span>
                </div>
                <div class="notif-detail-row">
                    <i class="fas fa-box" style="color: ${notif.cor};"></i>
                    <span>Quantidade: ${notif.quantidade || 0}</span>
                </div>
                <div class="notif-detail-row">
                    <i class="fas fa-calendar" style="color: ${notif.cor};"></i>
                    <span>Validade: ${notif.validade || 'Não informado'}</span>
                </div>
            </div>
        `;
    }
    
    return `
        <div class="notification-item ${notif.categoria}" data-tipo="${notif.tipo}" style="background: ${notif.cor_bg}; border-left: 4px solid ${notif.cor_border};">
            ${pulso}
            <div class="notification-icon" style="color: ${notif.cor};">
                <i class="fas ${notif.icone}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-header">
                    <span class="notification-title" style="color: ${notif.cor};">${notif.titulo}</span>
                    <span class="notification-time">${notif.mensagem}</span>
                </div>
                <div class="notification-subtitle">
                    ${subtitulo}
                </div>
                ${detalhes}
                ${btnAcao}
            </div>
        </div>
    `;
}

function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
}

function atualizarBadge(total) {
    const notificationBtn = document.getElementById('notificationBtn');
    if (!notificationBtn) return;
    
    let badge = notificationBtn.querySelector('.badge');
    
    if (total > 0) {
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'badge';
            badge.id = 'notificationBadge';
            notificationBtn.appendChild(badge);
        }
        badge.textContent = total > 99 ? '99+' : total;
    } else {
        if (badge) {
            badge.remove();
        }
    }
}
