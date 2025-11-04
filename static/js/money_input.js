/**
 * Script para formatação automática de campos monetários
 * Formata valores no padrão brasileiro (R$ 1.234,56)
 * Aplicado automaticamente em campos com a classe 'money-input'
 */

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        // Seleciona apenas campos dentro de formulários
        const moneyInputs = document.querySelectorAll('form input.money-input');
        
        console.log('Campos monetários em formulários encontrados:', moneyInputs.length);
        
        moneyInputs.forEach(input => {
            console.log('Processando campo:', input.name);
            
            // Placeholder
            if (input.placeholder && !input.placeholder.includes('R$')) {
                input.placeholder = 'R$ ' + input.placeholder;
            } else if (!input.placeholder) {
                input.placeholder = 'R$ 0,00';
            }
            
            // Formatar valor inicial se existir
            if (input.value && input.value.trim() !== '') {
                let valorInicial = input.value.replace(',', '.');
                let numero = parseFloat(valorInicial);
                if (!isNaN(numero)) {
                    input.value = 'R$ ' + formatarNumeroComVirgula(numero.toFixed(2));
                }
            }
            
            // Evento input: formata enquanto digita (sem vírgula)
            input.addEventListener('input', function(e) {
                let valor = e.target.value;
                
                // Remove tudo que não é número
                valor = valor.replace(/\D/g, '');
                
                if (!valor) {
                    e.target.value = '';
                    return;
                }
                
                // Remove zeros à esquerda
                valor = valor.replace(/^0+/, '') || '0';
                
                // Formata com pontos de milhar
                let parteInteira = valor.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
                
                // Mostra apenas com R$ e pontos de milhar (sem vírgula ainda)
                e.target.value = 'R$ ' + parteInteira;
            });
            
            // Evento blur: adiciona ,00 automaticamente
            input.addEventListener('blur', function(e) {
                let valor = e.target.value;
                
                if (!valor || valor === 'R$ ') {
                    e.target.value = '';
                    return;
                }
                
                // Remove R$ e espaços
                valor = valor.replace(/R\$/g, '').trim();
                
                // Remove pontos de milhar
                valor = valor.replace(/\./g, '');
                
                // Converte para número
                let numero = parseFloat(valor);
                
                if (isNaN(numero)) {
                    e.target.value = '';
                    return;
                }
                
                // Formata com duas casas decimais
                e.target.value = 'R$ ' + formatarNumeroComVirgula(numero.toFixed(2));
            });
            
            // Evento focus: seleciona tudo para facilitar edição
            input.addEventListener('focus', function(e) {
                setTimeout(() => {
                    e.target.select();
                }, 0);
            });
            
            // Permite apenas números
            input.addEventListener('keypress', function(e) {
                const char = String.fromCharCode(e.keyCode || e.which);
                if (!/[0-9]/.test(char) && e.keyCode !== 8 && e.keyCode !== 46) {
                    e.preventDefault();
                }
            });
        });
        
        /**
         * Formata um número com pontos de milhar e vírgula decimal
         * @param {string} valor - Valor no formato "1234.56"
         * @returns {string} Valor formatado "1.234,56"
         */
        function formatarNumeroComVirgula(valor) {
            // Separa parte inteira e decimal
            let partes = String(valor).split('.');
            let parteInteira = partes[0] || '0';
            let parteDecimal = partes[1] || '00';
            
            // Garante 2 casas decimais
            parteDecimal = (parteDecimal + '00').substring(0, 2);
            
            // Remove zeros à esquerda
            parteInteira = parteInteira.replace(/^0+/, '') || '0';
            
            // Adiciona pontos de milhar
            parteInteira = parteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
            
            return parteInteira + ',' + parteDecimal;
        }
        
        /**
         * Converte valor formatado para número antes de enviar
         */
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                console.log('Formulário sendo enviado...');
                moneyInputs.forEach(input => {
                    if (input.value && input.value !== 'R$ ') {
                        let valorOriginal = input.value;
                        let valor = input.value;
                        
                        // Remove R$ e espaços
                        valor = valor.replace(/R\$/g, '').trim();
                        
                        // Remove pontos de milhar e substitui vírgula por ponto
                        valor = valor.replace(/\./g, '').replace(',', '.');
                        
                        // Se não tiver vírgula, adiciona .00
                        if (!valorOriginal.includes(',')) {
                            valor = valor + '.00';
                        }
                        
                        let numero = parseFloat(valor);
                        if (!isNaN(numero)) {
                            input.value = numero.toFixed(2);
                            console.log('Convertendo', input.name, ':', valorOriginal, '->', input.value);
                        } else {
                            input.value = '';
                        }
                    }
                });
            });
        });
    }, 100);
});
