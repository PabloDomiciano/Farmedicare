/**
 * Sistema de Formatação Monetária Brasileira
 * Formata campos de input com padrão R$ 120.000,00
 */

document.addEventListener('DOMContentLoaded', function() {
    // Seleciona todos os campos de valor monetário
    const camposMonetarios = document.querySelectorAll('input[name="valor_total"], input[name="valor_medicamento"], input[name="valor_pago"], input[name="valor_parcela"]');
    
    camposMonetarios.forEach(campo => {
        // Formata valor inicial se existir
        if (campo.value) {
            campo.value = formatarMoeda(parseFloat(campo.value));
        }
        
        // Adiciona eventos
        campo.addEventListener('focus', function() {
            // Remove formatação ao focar
            this.value = this.value.replace(/[^\d,]/g, '');
        });
        
        campo.addEventListener('blur', function() {
            // Formata ao sair do campo
            if (this.value) {
                const valorNumerico = converterParaNumero(this.value);
                this.value = formatarMoeda(valorNumerico);
            }
        });
        
        campo.addEventListener('input', function(e) {
            // Permite apenas números e vírgula durante a digitação
            let valor = this.value;
            
            // Remove tudo que não é número ou vírgula
            valor = valor.replace(/[^\d,]/g, '');
            
            // Permite apenas uma vírgula
            const partes = valor.split(',');
            if (partes.length > 2) {
                valor = partes[0] + ',' + partes.slice(1).join('');
            }
            
            // Limita casas decimais a 2
            if (partes.length === 2 && partes[1].length > 2) {
                valor = partes[0] + ',' + partes[1].substring(0, 2);
            }
            
            this.value = valor;
        });
        
        // Antes de submeter o formulário, converte para formato numérico
        const form = campo.closest('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                camposMonetarios.forEach(c => {
                    if (c.value) {
                        c.value = converterParaNumero(c.value).toFixed(2);
                    }
                });
            });
        }
    });
});

/**
 * Converte string formatada para número
 * @param {string} valor - Valor formatado (ex: "R$ 1.500,50" ou "1500,50")
 * @returns {number} - Número decimal
 */
function converterParaNumero(valor) {
    if (typeof valor === 'number') return valor;
    
    // Remove R$, espaços e pontos (separadores de milhar)
    valor = valor.toString().replace(/[R$\s.]/g, '');
    
    // Substitui vírgula por ponto
    valor = valor.replace(',', '.');
    
    return parseFloat(valor) || 0;
}

/**
 * Formata número para moeda brasileira
 * @param {number} valor - Valor numérico
 * @returns {string} - Valor formatado (ex: "R$ 1.500,50")
 */
function formatarMoeda(valor) {
    if (isNaN(valor)) valor = 0;
    
    return 'R$ ' + valor.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Formata valores exibidos em cards e tabelas
 */
function formatarValoresNaPagina() {
    // Seleciona elementos que exibem valores
    const elementosValor = document.querySelectorAll('.valor-monetario, [data-valor]');
    
    elementosValor.forEach(elemento => {
        const valor = elemento.dataset.valor || elemento.textContent;
        const valorNumerico = converterParaNumero(valor);
        elemento.textContent = formatarMoeda(valorNumerico);
    });
}

// Executa formatação ao carregar a página
document.addEventListener('DOMContentLoaded', formatarValoresNaPagina);
