/**
 * TABELAS INTERATIVAS - FARMEDICARE
 * Adiciona funcionalidades de:
 * - Redimensionar colunas arrastando
 * - Ordenação de colunas
 * - Tooltip para células truncadas
 */

document.addEventListener('DOMContentLoaded', function() {
    initInteractiveTables();
    addExcelLikeHighlight();
});

function initInteractiveTables() {
    const tables = document.querySelectorAll('.tabela, .modelo-table');
    
    tables.forEach(table => {
        makeColumnsResizable(table);
        addSortingFeature(table);
        addTooltipsForTruncatedCells(table);
    });
}

/**
 * Adiciona destaque estilo Excel (apenas linha horizontal)
 */
function addExcelLikeHighlight() {
    const tables = document.querySelectorAll('.tabela, .modelo-table');
    
    tables.forEach(table => {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        const cells = tbody.querySelectorAll('td');
        
        cells.forEach((cell) => {
            cell.addEventListener('mouseenter', function() {
                const row = this.parentElement;
                
                // Destacar todas as células da mesma linha
                Array.from(row.children).forEach(c => {
                    c.classList.add('row-highlighted');
                });
                
                // Destacar a célula atual com cor mais escura
                this.classList.add('cell-active');
            });
            
            cell.addEventListener('mouseleave', function() {
                const row = this.parentElement;
                
                // Remover destaque da linha
                Array.from(row.children).forEach(c => {
                    c.classList.remove('row-highlighted');
                    c.classList.remove('cell-active');
                });
            });
        });
    });
}

/**
 * Torna as colunas redimensionáveis
 */
function makeColumnsResizable(table) {
    const thead = table.querySelector('thead');
    if (!thead) return;
    
    const ths = thead.querySelectorAll('th');
    
    ths.forEach((th, index) => {
        // Não permitir redimensionar a última coluna (ações)
        if (index === ths.length - 1) return;
        
        // Criar handle de redimensionamento
        const resizeHandle = document.createElement('div');
        resizeHandle.classList.add('resize-handle');
        resizeHandle.style.cssText = `
            position: absolute;
            right: 0;
            top: 0;
            width: 5px;
            height: 100%;
            cursor: col-resize;
            user-select: none;
            z-index: 1;
        `;
        
        th.style.position = 'relative';
        th.appendChild(resizeHandle);
        
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;
        
        resizeHandle.addEventListener('mousedown', function(e) {
            isResizing = true;
            startX = e.pageX;
            startWidth = th.offsetWidth;
            
            th.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (!isResizing) return;
            
            const diff = e.pageX - startX;
            const newWidth = startWidth + diff;
            
            // Largura mínima de 50px
            if (newWidth > 50) {
                th.style.width = newWidth + 'px';
                
                // Aplicar a mesma largura para as células da coluna
                const tbody = table.querySelector('tbody');
                if (tbody) {
                    const tds = tbody.querySelectorAll(`tr td:nth-child(${index + 1})`);
                    tds.forEach(td => {
                        td.style.width = newWidth + 'px';
                    });
                }
            }
        });
        
        document.addEventListener('mouseup', function() {
            if (!isResizing) return;
            
            isResizing = false;
            th.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        });
    });
}

/**
 * Adiciona ordenação ao clicar no cabeçalho
 */
function addSortingFeature(table) {
    const thead = table.querySelector('thead');
    if (!thead) return;
    
    const ths = thead.querySelectorAll('th');
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    ths.forEach((th, columnIndex) => {
        // Não ordenar a coluna de ações
        if (columnIndex === ths.length - 1) return;
        
        th.style.cursor = 'pointer';
        th.title = 'Clique para ordenar';
        
        th.addEventListener('click', function(e) {
            // Não ordenar se clicou no handle de resize
            if (e.target.classList.contains('resize-handle')) return;
            
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const currentSort = th.getAttribute('data-sorted');
            const newSort = currentSort === 'asc' ? 'desc' : 'asc';
            
            // Remover ordenação de outras colunas
            ths.forEach(otherTh => {
                otherTh.removeAttribute('data-sorted');
            });
            
            // Definir nova ordenação
            th.setAttribute('data-sorted', newSort);
            
            // Ordenar linhas
            rows.sort((a, b) => {
                const aValue = a.children[columnIndex]?.textContent.trim() || '';
                const bValue = b.children[columnIndex]?.textContent.trim() || '';
                
                // Tentar converter para número
                const aNum = parseFloat(aValue.replace(/[^\d.-]/g, ''));
                const bNum = parseFloat(bValue.replace(/[^\d.-]/g, ''));
                
                let comparison = 0;
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    // Comparação numérica
                    comparison = aNum - bNum;
                } else {
                    // Comparação textual
                    comparison = aValue.localeCompare(bValue, 'pt-BR', {
                        numeric: true,
                        sensitivity: 'base'
                    });
                }
                
                return newSort === 'asc' ? comparison : -comparison;
            });
            
            // Reordenar no DOM
            rows.forEach(row => tbody.appendChild(row));
            
            // Animação suave
            tbody.style.opacity = '0.7';
            setTimeout(() => {
                tbody.style.opacity = '1';
            }, 100);
        });
    });
}

/**
 * Adiciona tooltips para células com texto truncado
 */
function addTooltipsForTruncatedCells(table) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const cells = tbody.querySelectorAll('td');
    
    cells.forEach(cell => {
        // Verificar se o texto está truncado
        if (cell.scrollWidth > cell.clientWidth) {
            cell.setAttribute('title', cell.textContent.trim());
        }
    });
}

/**
 * Destaca linha ao clicar (opcional)
 */
function addRowHighlight() {
    const tables = document.querySelectorAll('.tabela tbody, .modelo-table tbody');
    
    tables.forEach(tbody => {
        const rows = tbody.querySelectorAll('tr');
        
        rows.forEach(row => {
            row.addEventListener('click', function(e) {
                // Não destacar se clicou em um botão ou link
                if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || 
                    e.target.closest('a') || e.target.closest('button')) {
                    return;
                }
                
                // Remover destaque de outras linhas
                rows.forEach(r => r.classList.remove('row-selected'));
                
                // Adicionar destaque
                this.classList.add('row-selected');
            });
        });
    });
}

/**
 * Adiciona busca em tempo real na tabela
 */
function addTableSearch(searchInputId, tableId) {
    const searchInput = document.getElementById(searchInputId);
    const table = document.getElementById(tableId);
    
    if (!searchInput || !table) return;
    
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    searchInput.addEventListener('keyup', function() {
        const searchTerm = this.value.toLowerCase().trim();
        const rows = tbody.querySelectorAll('tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            
            if (text.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

/**
 * Exporta tabela para CSV
 */
function exportTableToCSV(tableId, filename = 'tabela.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        
        cols.forEach(col => {
            // Remove botões e links do export
            let text = col.textContent.trim();
            text = text.replace(/[\n\r]+/g, ' ');
            rowData.push(`"${text}"`);
        });
        
        csv.push(rowData.join(','));
    });
    
    // Criar e baixar arquivo
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Expor funções globalmente
window.exportTableToCSV = exportTableToCSV;
window.addTableSearch = addTableSearch;
