// ============================================
// DASHBOARD BI PROFESIONAL - JS PRINCIPAL
// ============================================

'use strict';

class DashboardBI {
    constructor() {
        this.config = window.DASHBOARD_CONFIG || this.getDefaultConfig();
        this.state = {
            currentYear: this.config.CURRENT_YEAR || new Date().getFullYear(),
            selectedYears: [],
            selectedMonth: null,
            charts: {
                altas: null,
                bajas: null,
                comparativa: null,
                reclutadorDetalle: null  // <-- Añadido el gráfico del modal
            },
            isLoading: false,
            dataCache: new Map(),
            reclutadoresData: null,
            reclutadoresComercial: null
        };
        
        this.dom = {
            yearSelect: document.getElementById('yearSelect'),
            monthSelect: document.getElementById('monthSelect'),
            compareYearSelect: document.getElementById('compareYearSelect'),
            btnRefresh: document.getElementById('btnRefresh'),
            toggleNormalized: document.getElementById('toggleNormalized'),
            
            kpiTotal: document.getElementById('kpiTotalContrataciones'),
            kpiBajasGestion: document.getElementById('kpiBajasGestion'),
            kpiBajasComercial: document.getElementById('kpiBajasComercial'),
            kpiRetencion: document.getElementById('kpiRetencion'),
            kpiTotalSubtitle: document.getElementById('kpiTotalSubtitle'),
            
            reclutadoresList: document.getElementById('reclutadoresList')
        };
        
        this.init();
    }
    
    getDefaultConfig() {
        return {
            AREA_COMERCIAL_ID: 2,
            CURRENT_YEAR: new Date().getFullYear(),
            AVAILABLE_YEARS: [],
            API_ENDPOINTS: {
                kpis: '/api/kpis',
                contrataciones: '/api/contrataciones',
                bajas: '/api/bajas',
                comparativa: '/api/contrataciones/comparativa',
                reclutadores: '/api/contrataciones/reclutador',
                detalle_reclutador: '/api/contrataciones/detalle-reclutador/',
                reclutadores_comercial: '/api/reclutadores/comercial',
                buscar_reclutador: '/api/buscar-reclutador'
            },
            MESES: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
            MESES_CORTOS: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                           'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            COLORS: {
                gestion: '#ff6b6b',
                comercial: '#4ecdc4',
                years: ['#36a2eb', '#ff6384', '#ff9f40', '#4bc0c0', '#9966ff', '#ffcd56']
            }
        };
    }
    
    // =========================
    // INICIALIZACIÓN
    // =========================
    init() {
        console.log('🚀 Iniciando Dashboard BI Profesional...');
        
        this.updateCurrentDate();
        this.initCharts();
        this.setupEventListeners();
        this.setupInitialState();
        
        // Cargar datos iniciales
        setTimeout(() => {
            this.loadData();
        }, 100);
        
        console.log('✅ Dashboard BI inicializado correctamente');
        
        // Exponer instancia globalmente
        window.dashboardBI = this;
    }
    
    setupInitialState() {
        if (this.dom.compareYearSelect) {
            const selectedOptions = Array.from(this.dom.compareYearSelect.selectedOptions)
                .map(opt => parseInt(opt.value))
                .filter(y => !isNaN(y));
            this.state.selectedYears = selectedOptions.length > 0 ? 
                selectedOptions : 
                [this.state.currentYear - 2, this.state.currentYear - 1, this.state.currentYear];
        }
    }
    
    // =========================
    // FUNCIONES DE UTILIDAD
    // =========================
    updateCurrentDate() {
        const now = new Date();
        const dateStr = now.toLocaleDateString('es-MX', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        const dateElement = document.getElementById('currentDate');
        if (dateElement) dateElement.textContent = dateStr;
    }
    
    updateLastUpdateTime() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('es-MX', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        const updateElement = document.getElementById('lastUpdate');
        if (updateElement) updateElement.textContent = timeStr;
    }
    
    showLoading(show, elementId = null) {
        this.state.isLoading = show;
        
        if (elementId) {
            const loadingElement = document.getElementById(elementId);
            if (loadingElement) {
                loadingElement.style.display = show ? 'flex' : 'none';
            }
        }
        
        if (this.dom.btnRefresh) {
            this.dom.btnRefresh.disabled = show;
            this.dom.btnRefresh.innerHTML = show ? 
                '<span class="spinner-border spinner-border-sm me-2"></span>Cargando...' :
                '<i class="bi bi-arrow-clockwise me-2"></i>Actualizar';
        }
    }
    
    updateKPI(element, value) {
        if (!element) return;
        
        element.classList.remove('skeleton');
        
        const oldValue = element.textContent;
        const newValue = typeof value === 'number' ? value.toLocaleString('es-MX') : value;
        
        if (oldValue !== newValue) {
            element.classList.add('pulse');
            element.textContent = newValue;
            
            setTimeout(() => {
                element.classList.remove('pulse');
            }, 500);
        }
    }
    
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    showToast(message, type = 'info') {
        // Implementación básica de toast
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        const toast = this.createToastElement(message, type);
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, { 
            delay: 3000,
            autohide: true
        });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
        `;
        document.body.appendChild(container);
        return container;
    }
    
    createToastElement(message, type) {
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        
        const typeClasses = {
            success: 'bg-success text-white',
            danger: 'bg-danger text-white',
            warning: 'bg-warning text-dark',
            info: 'bg-info text-white'
        };
        
        const icons = {
            success: 'check-circle-fill',
            danger: 'exclamation-triangle-fill',
            warning: 'exclamation-triangle-fill',
            info: 'info-circle-fill'
        };
        
        toast.className = `toast ${typeClasses[type] || 'bg-info text-white'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header ${type === 'warning' ? 'bg-warning' : ''}">
                <i class="bi bi-${icons[type] || 'info-circle'} me-2"></i>
                <strong class="me-auto">${type === 'danger' ? '❌ Error' : 
                                         type === 'success' ? '✅ Éxito' : 
                                         type === 'warning' ? '⚠️ Advertencia' : 'ℹ️ Información'}</strong>
                <button type="button" class="btn-close ${type === 'warning' ? '' : 'btn-close-white'}" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        return toast;
    }
    
    // =========================
    // FUNCIONES DE DATOS
    // =========================
    async fetchData(endpoint, params = {}, pathParam = null) {
        let url;
        
        if (pathParam !== null) {
            url = new URL(this.config.API_ENDPOINTS[endpoint] + pathParam, window.location.origin);
        } else {
            url = new URL(this.config.API_ENDPOINTS[endpoint], window.location.origin);
        }
        
        Object.keys(params).forEach(key => {
            if (Array.isArray(params[key])) {
                params[key].forEach(value => {
                    url.searchParams.append(`${key}[]`, value);
                });
            } else if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        const cacheKey = url.toString();
        
        if (this.state.dataCache.has(cacheKey)) {
            return this.state.dataCache.get(cacheKey);
        }
        
        try {
            const response = await fetch(url.toString());
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.state.dataCache.set(cacheKey, data);
            return data;
        } catch (error) {
            console.error(`Error en ${endpoint}:`, error);
            this.showToast(`Error al cargar datos: ${error.message}`, 'danger');
            throw error;
        }
    }
    
    async loadData() {
        if (this.state.isLoading) return;
        
        this.showLoading(true);
        this.showLoading(true, 'loadingAltas');
        this.showLoading(true, 'loadingBajas');
        
        try {
            const params = {
                year: this.state.currentYear || new Date().getFullYear(),
                month: this.state.selectedMonth
            };
            
            const [kpisData, contratacionesData, bajasData] = await Promise.all([
                this.fetchData('kpis', params),
                this.fetchData('contrataciones', params),
                this.fetchData('bajas', params)
            ]);
            
            this.updateKPIs(kpisData);
            this.updateChartAltas(contratacionesData);
            this.updateChartBajas(bajasData);
            this.updateTableDetalle(contratacionesData, bajasData);
            
            this.updateLastUpdateTime();
            
            // Cargar datos adicionales en segundo plano
            setTimeout(() => {
                this.loadReclutadoresData();
                this.loadReclutadoresComercial();
                this.loadComparativa();
            }, 500);
            
        } catch (error) {
            console.error('Error cargando datos:', error);
        } finally {
            this.showLoading(false);
            this.showLoading(false, 'loadingAltas');
            this.showLoading(false, 'loadingBajas');
        }
    }
    
    async loadReclutadoresData() {
        try {
            const data = await this.fetchData('reclutadores', { 
                year: this.state.currentYear || new Date().getFullYear()
            });
            
            this.state.reclutadoresData = data;
            this.updateReclutadoresList(data);
            
        } catch (error) {
            console.error('Error cargando datos de reclutadores:', error);
        }
    }
    
    async loadReclutadoresComercial() {
        try {
            const data = await this.fetchData('reclutadores_comercial', { 
                year: this.state.currentYear || new Date().getFullYear()
            });
            
            this.state.reclutadoresComercial = data;
            
        } catch (error) {
            console.error('Error cargando reclutadores comerciales:', error);
        }
    }
    
    async loadComparativa() {
        if (this.state.selectedYears.length === 0) {
            this.state.selectedYears = [this.state.currentYear - 2, this.state.currentYear - 1, this.state.currentYear];
        }
        
        try {
            this.showLoading(true, 'loadingComparativa');
            const data = await this.fetchData('comparativa', { years: this.state.selectedYears });
            this.updateChartComparativa(data);
        } catch (error) {
            console.error('Error cargando comparativa:', error);
        } finally {
            this.showLoading(false, 'loadingComparativa');
        }
    }
    
    // =========================
    // ACTUALIZACIÓN DE UI
    // =========================
    updateKPIs(kpisData) {
    if (!kpisData) return;
    
    const total = kpisData.total || 0;
    const gestion = kpisData.gestion || 0;
    const comercial = kpisData.comercial || 0;
    const bajasGestion = kpisData.bajas_gestion || 0;
    const bajasComercial = kpisData.bajas_comercial || 0;
    const activos = kpisData.activos || 0; // <-- Esto sí viene de la API
    
    this.updateKPI(this.dom.kpiTotal, total);
    this.updateKPI(this.dom.kpiBajasGestion, bajasGestion);
    this.updateKPI(this.dom.kpiBajasComercial, bajasComercial);
    
    if (this.dom.kpiTotalSubtitle) {
        this.dom.kpiTotalSubtitle.textContent = `Total: ${total} | Gestión: ${gestion} | Comercial: ${comercial}`;
    }
    
    // Calcular retención usando "activos" que viene de la API
    const retencion = total > 0 ? ((activos) / total * 100).toFixed(1) : 0;
    this.updateKPI(this.dom.kpiRetencion, `${retencion}%`);
}
    
    updateChartAltas(contratacionesData) {
        if (!this.state.charts.altas || !contratacionesData) return;
        
        if (!Array.isArray(contratacionesData)) {
            contratacionesData = [contratacionesData];
        }
        
        const gestionData = this.config.MESES_CORTOS.map((_, index) => {
            const item = contratacionesData.find(c => c.mes_num === index + 1) || 
                         contratacionesData[index] || {};
            return item.gestion || 0;
        });
        
        const comercialData = this.config.MESES_CORTOS.map((_, index) => {
            const item = contratacionesData.find(c => c.mes_num === index + 1) || 
                         contratacionesData[index] || {};
            return item.comercial || 0;
        });
        
        this.state.charts.altas.data.datasets = [
            {
                label: 'Gestión (Total, incluye bajas)',
                data: gestionData,
                borderColor: this.config.COLORS.gestion,
                backgroundColor: this.hexToRgba(this.config.COLORS.gestion, 0.1),
                borderWidth: 3,
                tension: 0.4,
                fill: true
            },
            {
                label: 'Comercial (Total, incluye bajas)',
                data: comercialData,
                borderColor: this.config.COLORS.comercial,
                backgroundColor: this.hexToRgba(this.config.COLORS.comercial, 0.1),
                borderWidth: 3,
                tension: 0.4,
                fill: true
            }
        ];
        
        this.state.charts.altas.update();
        
        const totalGestion = gestionData.reduce((a, b) => a + b, 0);
        const totalComercial = comercialData.reduce((a, b) => a + b, 0);
        const total = totalGestion + totalComercial;
        
        const summaryElement = document.getElementById('chartAltasSummary');
        if (summaryElement) {
            summaryElement.textContent = `Total: ${total} | Gestión: ${totalGestion} | Comercial: ${totalComercial}`;
        }
    }
    
    updateChartBajas(bajasData) {
        if (!this.state.charts.bajas || !bajasData) return;
        
        if (!Array.isArray(bajasData)) {
            bajasData = [bajasData];
        }
        
        const gestionData = this.config.MESES_CORTOS.map((_, index) => {
            const item = bajasData.find(c => c.mes_num === index + 1) || 
                         bajasData[index] || {};
            return item.gestion || 0;
        });
        
        const comercialData = this.config.MESES_CORTOS.map((_, index) => {
            const item = bajasData.find(c => c.mes_num === index + 1) || 
                         bajasData[index] || {};
            return item.comercial || 0;
        });
        
        this.state.charts.bajas.data.datasets = [
            {
                label: 'Gestión (No ID:5)',
                data: gestionData,
                borderColor: this.config.COLORS.gestion,
                backgroundColor: this.hexToRgba(this.config.COLORS.gestion, 0.2),
                borderWidth: 3,
                tension: 0.4
            },
            {
                label: 'Comercial (ID:5)',
                data: comercialData,
                borderColor: this.config.COLORS.comercial,
                backgroundColor: this.hexToRgba(this.config.COLORS.comercial, 0.2),
                borderWidth: 3,
                tension: 0.4
            }
        ];
        
        this.state.charts.bajas.update();
        
        const totalGestion = gestionData.reduce((a, b) => a + b, 0);
        const totalComercial = comercialData.reduce((a, b) => a + b, 0);
        const total = totalGestion + totalComercial;
        
        const summaryElement = document.getElementById('chartBajasSummary');
        if (summaryElement) {
            summaryElement.textContent = `Total: ${total} | Gestión: ${totalGestion} | Comercial: ${totalComercial}`;
        }
    }
    
    updateChartComparativa(comparativaData) {
        if (!this.state.charts.comparativa || !comparativaData) return;
        
        const datasets = [];
        const years = Object.keys(comparativaData).sort();
        const isNormalized = this.dom.toggleNormalized?.checked;
        
        years.forEach((year, index) => {
            const yearData = comparativaData[year];
            
            let data = this.config.MESES_CORTOS.map((_, idx) => {
                const item = yearData.find(d => d.mes_num === idx + 1) || 
                             yearData[idx] || {};
                return item.total || 0;
            });
            
            if (isNormalized) {
                const maxValue = Math.max(...data);
                if (maxValue > 0) {
                    data = data.map(value => (value / maxValue * 100));
                }
            }
            
            datasets.push({
                label: `Año ${year}`,
                data: data,
                borderColor: this.config.COLORS.years[index % this.config.COLORS.years.length],
                backgroundColor: this.hexToRgba(this.config.COLORS.years[index % this.config.COLORS.years.length], 0.1),
                borderWidth: 2,
                tension: 0.4,
                fill: true
            });
        });
        
        this.state.charts.comparativa.data.datasets = datasets;
        
        if (this.state.charts.comparativa.options.scales.y) {
            this.state.charts.comparativa.options.scales.y.title.text = isNormalized ? 'Porcentaje (%)' : 'Cantidad';
            this.state.charts.comparativa.options.scales.y.max = isNormalized ? 100 : undefined;
        }
        
        this.state.charts.comparativa.update();
    }
    
    updateReclutadoresList(reclutadoresData) {
        if (!this.dom.reclutadoresList || !reclutadoresData || !Array.isArray(reclutadoresData)) {
            return;
        }
        
        this.dom.reclutadoresList.innerHTML = '';
        
        if (reclutadoresData.length === 0) {
            this.dom.reclutadoresList.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-people display-4 text-muted mb-3"></i>
                    <p class="text-muted">No hay datos de reclutadores</p>
                </div>
            `;
            return;
        }
        
        const topReclutadores = [...reclutadoresData]
            .sort((a, b) => b.total_anual - a.total_anual)
            .slice(0, 10);
        
        const maxTotal = Math.max(...topReclutadores.map(r => r.total_anual));
        
        topReclutadores.forEach(reclutador => {
            const template = document.getElementById('templateReclutadorItem');
            if (!template) return;
            
            const porcentaje = maxTotal > 0 ? (reclutador.total_anual / maxTotal * 100) : 0;
            
            const rowHTML = template.innerHTML
                .replace(/{id}/g, reclutador.reclutador)
                .replace(/{nombre}/g, reclutador.reclutador)
                .replace(/{total}/g, reclutador.total_anual)
                .replace(/{porcentaje}/g, porcentaje.toFixed(1));
            
            const div = document.createElement('div');
            div.innerHTML = rowHTML;
            const item = div.firstElementChild;
            
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.verDetalleReclutadorPorNombre(reclutador.reclutador);
            });
            
            this.dom.reclutadoresList.appendChild(item);
        });
    }
    
    updateTableDetalle(contratacionesData, bajasData) {
    const tableBody = document.getElementById('tableDetalleBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    if (!Array.isArray(contratacionesData)) {
        contratacionesData = [contratacionesData];
    }
    if (!Array.isArray(bajasData)) {
        bajasData = [bajasData];
    }
    
    let totalGestionAnual = 0;
    let totalComercialAnual = 0;
    let totalBajasGestionAnual = 0;
    let totalBajasComercialAnual = 0;
    let totalContratacionesActivasAnual = 0;
    
    this.config.MESES_CORTOS.forEach((mes, index) => {
        const mesNum = index + 1;
        const altaItem = contratacionesData.find(c => c.mes_num === mesNum) || 
                        contratacionesData[index] || {};
        const bajaItem = bajasData.find(b => b.mes_num === mesNum) || 
                        bajasData[index] || {};
        
        const gestion = altaItem.gestion || 0;                    // Total gestión (incluye bajas)
        const comercial = altaItem.comercial || 0;                // Total comercial (incluye bajas)
        const gestionActivos = altaItem.gestion_activos || 0;     // Gestión activos (sin baja)
        const comercialActivos = altaItem.comercial_activos || 0; // Comercial activos (sin baja)
        const bajasGestion = bajaItem.gestion || 0;
        const bajasComercial = bajaItem.comercial || 0;
        
        const totalContrataciones = gestion + comercial;          // Total contrataciones del mes (incluye bajas)
        const totalContratacionesActivas = gestionActivos + comercialActivos; // Solo activos
        const totalBajas = bajasGestion + bajasComercial;
        
        totalGestionAnual += gestion;
        totalComercialAnual += comercial;
        totalBajasGestionAnual += bajasGestion;
        totalBajasComercialAnual += bajasComercial;
        totalContratacionesActivasAnual += totalContratacionesActivas;
        
        const retencion = totalContrataciones > 0 ? 
            (totalContratacionesActivas / totalContrataciones * 100).toFixed(1) : 0;
        
        let retencionClass = 'bg-secondary';
        let retencionIcon = '';
        if (retencion >= 80) {
            retencionClass = 'bg-success';
            retencionIcon = '<i class="bi bi-arrow-up-circle"></i>';
        } else if (retencion >= 60) {
            retencionClass = 'bg-warning';
            retencionIcon = '<i class="bi bi-dash-circle"></i>';
        } else {
            retencionClass = 'bg-danger';
            retencionIcon = '<i class="bi bi-arrow-down-circle"></i>';
        }
        
        const template = document.getElementById('templateRowDetalle');
        if (!template) {
            // Si no hay template, crear la fila directamente
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="fw-medium">${mes}</td>
                <td class="text-center">
                    <span class="badge bg-warning fs-6" title="Total: ${gestion} | Activos: ${gestionActivos}">${gestion}</span>
                </td>
                <td class="text-center">
                    <span class="badge bg-info fs-6" title="Total: ${comercial} | Activos: ${comercialActivos}">${comercial}</span>
                </td>
                <td class="text-center">
                    <span class="badge bg-secondary">${bajasGestion}</span>
                </td>
                <td class="text-center">
                    <span class="badge bg-secondary">${bajasComercial}</span>
                </td>
                <td class="text-center">
                    <strong>${totalContrataciones}</strong>
                    <br>
                    <small class="text-muted">Activos: ${totalContratacionesActivas}</small>
                </td>
                <td class="text-center">
                    <span class="badge bg-danger">${totalBajas}</span>
                </td>
                <td class="text-center">
                    <span class="badge ${retencionClass}">
                        ${retencionIcon} ${retencion}%
                    </span>
                </td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-primary" onclick="showReclutadoresPorMes(${mesNum})" title="Ver detalle del mes">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        } else {
            // Usar el template si existe
            const rowHTML = template.innerHTML
                .replace(/{mes}/g, mes)
                .replace(/{gestion}/g, gestion)
                .replace(/{gestion_activos}/g, gestionActivos)
                .replace(/{comercial}/g, comercial)
                .replace(/{comercial_activos}/g, comercialActivos)
                .replace(/{bajas_gestion}/g, bajasGestion)
                .replace(/{bajas_comercial}/g, bajasComercial)
                .replace(/{total_contrataciones}/g, totalContrataciones)
                .replace(/{total_contrataciones_activas}/g, totalContratacionesActivas)
                .replace(/{total_bajas}/g, totalBajas)
                .replace(/{retencion}/g, retencion)
                .replace(/{retencion_class}/g, retencionClass)
                .replace(/{retencion_icon}/g, retencionIcon)
                .replace(/{mes_num}/g, mesNum);
            
            const row = document.createElement('tr');
            row.innerHTML = rowHTML;
            tableBody.appendChild(row);
        }
    });
    
    // Agregar fila de total anual
    const totalContratacionesAnual = totalGestionAnual + totalComercialAnual;
    const totalBajasAnual = totalBajasGestionAnual + totalBajasComercialAnual;
    const retencionAnual = totalContratacionesAnual > 0 ? 
        (totalContratacionesActivasAnual / totalContratacionesAnual * 100).toFixed(1) : 0;
    
    let retencionAnualClass = 'bg-secondary';
    if (retencionAnual >= 80) retencionAnualClass = 'bg-success';
    else if (retencionAnual >= 60) retencionAnualClass = 'bg-warning';
    else retencionAnualClass = 'bg-danger';
    
    const totalRow = document.createElement('tr');
    totalRow.className = 'table-primary fw-bold';
    totalRow.innerHTML = `
        <td><strong>TOTAL ANUAL</strong></td>
        <td class="text-center">
            <span class="badge bg-warning fs-6" title="Total contrataciones de gestión">${totalGestionAnual}</span>
        </td>
        <td class="text-center">
            <span class="badge bg-info fs-6" title="Total contrataciones comerciales">${totalComercialAnual}</span>
        </td>
        <td class="text-center">
            <span class="badge bg-secondary" title="Bajas de gestión">${totalBajasGestionAnual}</span>
        </td>
        <td class="text-center">
            <span class="badge bg-secondary" title="Bajas comerciales">${totalBajasComercialAnual}</span>
        </td>
        <td class="text-center">
            <strong>${totalContratacionesAnual}</strong>
            <br>
            <small class="text-muted">Activos: ${totalContratacionesActivasAnual}</small>
        </td>
        <td class="text-center">
            <span class="badge bg-danger" title="Total bajas">${totalBajasAnual}</span>
        </td>
        <td class="text-center">
            <span class="badge ${retencionAnualClass}">
                ${retencionAnual}%
            </span>
        </td>
        <td class="text-center">
            <button class="btn btn-sm btn-outline-info" onclick="dashboardBI.showModalDetalleReclutadores()" title="Ver todos los reclutadores">
                <i class="bi bi-people-fill"></i>
            </button>
        </td>
    `;
    tableBody.appendChild(totalRow);
    
    // Actualizar tooltips
    setTimeout(() => {
        const tooltipTriggerList = [].slice.call(tableBody.querySelectorAll('[title]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }, 100);
}
    // =========================
    // CHART INITIALIZATION
    // =========================
    initCharts() {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js no está cargado');
            return;
        }
        
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            size: 12
                        },
                        padding: 20
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 6,
                    displayColors: true
                }
            }
        };
        
        // Gráfica de Altas
        const chartAltasCanvas = document.getElementById('chartAltas');
        if (chartAltasCanvas) {
            const ctx = chartAltasCanvas.getContext('2d');
            this.state.charts.altas = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: this.config.MESES_CORTOS,
                    datasets: []
                },
                options: {
                    ...commonOptions,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { 
                                precision: 0,
                                callback: function(value) {
                                    if (value % 1 === 0) {
                                        return value;
                                    }
                                }
                            },
                            grid: { 
                                color: 'rgba(0, 0, 0, 0.05)',
                                drawBorder: false
                            },
                            title: {
                                display: true,
                                text: 'Cantidad',
                                font: { size: 12, weight: 'bold' }
                            }
                        },
                        x: {
                            grid: { 
                                display: false,
                                drawBorder: false
                            },
                            title: {
                                display: true,
                                text: 'Mes',
                                font: { size: 12, weight: 'bold' }
                            }
                        }
                    }
                }
            });
        }
        
        // Gráfica de Bajas
        const chartBajasCanvas = document.getElementById('chartBajas');
        if (chartBajasCanvas) {
            const ctx = chartBajasCanvas.getContext('2d');
            this.state.charts.bajas = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: this.config.MESES_CORTOS,
                    datasets: []
                },
                options: {
                    ...commonOptions,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                            grid: { color: 'rgba(0, 0, 0, 0.05)' },
                            title: {
                                display: true,
                                text: 'Cantidad',
                                font: { size: 12, weight: 'bold' }
                            }
                        },
                        x: {
                            grid: { display: false },
                            title: {
                                display: true,
                                text: 'Mes',
                                font: { size: 12, weight: 'bold' }
                            }
                        }
                    }
                }
            });
        }
        
        // Gráfica Comparativa
        const chartComparativaCanvas = document.getElementById('chartComparativa');
        if (chartComparativaCanvas) {
            const ctx = chartComparativaCanvas.getContext('2d');
            this.state.charts.comparativa = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: this.config.MESES_CORTOS,
                    datasets: []
                },
                options: {
                    ...commonOptions,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                            grid: { color: 'rgba(0, 0, 0, 0.05)' },
                            title: {
                                display: true,
                                text: 'Cantidad',
                                font: { size: 12, weight: 'bold' }
                            }
                        },
                        x: {
                            grid: { display: false },
                            title: {
                                display: true,
                                text: 'Mes',
                                font: { size: 12, weight: 'bold' }
                            }
                        }
                    }
                }
            });
        }
    }
    
    // =========================
    // EVENT LISTENERS
    // =========================
    setupEventListeners() {
        if (this.dom.yearSelect) {
            this.dom.yearSelect.addEventListener('change', (e) => {
                this.state.currentYear = e.target.value ? parseInt(e.target.value) : null;
                this.state.dataCache.clear();
                this.loadData();
            });
        }
        
        if (this.dom.monthSelect) {
            this.dom.monthSelect.addEventListener('change', (e) => {
                this.state.selectedMonth = e.target.value ? parseInt(e.target.value) : null;
                this.state.dataCache.clear();
                this.loadData();
            });
        }
        
        if (this.dom.compareYearSelect) {
            this.dom.compareYearSelect.addEventListener('change', (e) => {
                const selectedOptions = Array.from(e.target.selectedOptions)
                    .map(opt => parseInt(opt.value))
                    .filter(y => !isNaN(y));
                this.state.selectedYears = selectedOptions;
                this.loadComparativa();
            });
        }
        
        if (this.dom.btnRefresh) {
            this.dom.btnRefresh.addEventListener('click', () => {
                this.state.dataCache.clear();
                this.loadData();
            });
        }
        
        if (this.dom.toggleNormalized) {
            this.dom.toggleNormalized.addEventListener('change', () => this.loadComparativa());
        }
    }
    
    // =========================
    // FUNCIONES PARA MODALES (DENTRO DE LA CLASE)
    // =========================
    async showReclutadoresPorMes(mesNum) {
        try {
            console.log('Mostrando reclutadores para mes:', mesNum);
            
            // Primero, obtener el año seleccionado
            const year = this.state.currentYear || this.config.CURRENT_YEAR;
            
            // Llamar a la API para obtener reclutadores del mes específico
            const data = await this.fetchData('reclutadores_comercial', {
                year: year,
                month: mesNum
            });
            
            console.log('Datos recibidos para mes', mesNum, ':', data);
            
            // Verificar si tenemos datos
            if (!data || data.length === 0) {
                this.showToast(`No hay datos de reclutadores para ${this.config.MESES[mesNum-1]}`, 'warning');
                return;
            }
            
            // Llenar el modal de detalle comercial
            this.fillModalDetalleComercial(data, year, mesNum);
            
            // Mostrar el modal
            const modalElement = document.getElementById('modalDetalleComercial');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
            
        } catch (error) {
            console.error('Error mostrando reclutadores por mes:', error);
            this.showToast('Error al cargar los reclutadores del mes', 'danger');
        }
    }
    
    async showModalDetalleComercial() {
        try {
            console.log('Mostrando modal detalle comercial');
            
            const year = this.state.currentYear || this.config.CURRENT_YEAR;
            const mes = this.state.selectedMonth || null;
            
            // Obtener todos los reclutadores comerciales
            const data = await this.fetchData('reclutadores_comercial', {
                year: year,
                month: mes
            });
            
            console.log('Datos reclutadores comerciales:', data);
            
            if (!data || data.length === 0) {
                this.showToast('No hay datos de reclutadores comerciales', 'warning');
                return;
            }
            
            // Llenar el modal
            this.fillModalDetalleComercial(data, year, mes);
            
            // Mostrar modal
            const modalElement = document.getElementById('modalDetalleComercial');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
            
        } catch (error) {
            console.error('Error mostrando detalle comercial:', error);
            this.showToast('Error al cargar el detalle comercial', 'danger');
        }
    }
    
    async showModalDetalleReclutadores() {
        try {
            console.log('Mostrando modal detalle reclutadores');
            
            // Primero cargar los datos si no están en caché
            if (!this.state.reclutadoresData) {
                await this.loadReclutadoresData();
            }
            
            // Obtener el contenedor del modal
            const modalElement = document.getElementById('modalDetalleReclutador');
            if (!modalElement) {
                console.error('Modal no encontrado');
                return;
            }
            
            // Actualizar título
            const titleElement = modalElement.querySelector('#modalReclutadorTitle');
            if (titleElement) {
                titleElement.innerHTML = `<i class="bi bi-person-badge me-2"></i>Top Reclutadores - ${this.state.currentYear}`;
            }
            
            // Crear contenido para el modal
            const modalBody = modalElement.querySelector('.modal-body');
            if (modalBody && this.state.reclutadoresData) {
                let html = `
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Reclutador</th>
                                    <th class="text-center">Contrataciones</th>
                                    <th class="text-center">Porcentaje</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                // Ordenar reclutadores por total
                const sortedReclutadores = [...this.state.reclutadoresData]
                    .sort((a, b) => b.total_anual - a.total_anual);
                
                // Calcular total para porcentajes
                const totalAnual = sortedReclutadores.reduce((sum, r) => sum + r.total_anual, 0);
                
                sortedReclutadores.forEach((reclutador, index) => {
                    const porcentaje = totalAnual > 0 ? (reclutador.total_anual / totalAnual * 100).toFixed(1) : 0;
                    
                    html += `
                        <tr>
                            <td><strong>${index + 1}</strong></td>
                            <td>${reclutador.reclutador}</td>
                            <td class="text-center">
                                <span class="badge bg-primary fs-6">${reclutador.total_anual}</span>
                            </td>
                            <td class="text-center">
                                <div class="progress" style="height: 20px;">
                                    <div class="progress-bar bg-success" style="width: ${porcentaje}%">
                                        ${porcentaje}%
                                    </div>
                                </div>
                            </td>
                            <td class="text-center">
                                <button class="btn btn-sm btn-outline-info" onclick="dashboardBI.verDetalleReclutador('${reclutador.reclutador}')">
                                    <i class="bi bi-eye"></i> Ver Detalle
                                </button>
                            </td>
                        </tr>
                    `;
                });
                
                html += `
                            </tbody>
                        </table>
                    </div>
                    <div class="text-center mt-3">
                        <small class="text-muted">Total anual de contrataciones: ${totalAnual}</small>
                    </div>
                `;
                
                modalBody.innerHTML = html;
            }
            
            // Mostrar el modal
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
        } catch (error) {
            console.error('Error mostrando detalle de reclutadores:', error);
            this.showToast('Error al cargar el detalle de reclutadores', 'danger');
        }
    }
    
    fillModalDetalleComercial(data, year, mes) {
    const modalTitle = document.getElementById('modalComercialTitle');
    const modalSubtitle = document.getElementById('modalComercialSubtitle');
    const modalBody = document.getElementById('modalComercialBody');
    
    if (!modalTitle || !modalSubtitle || !modalBody) {
        console.error('Elementos del modal no encontrados');
        return;
    }
    
    // Configurar título
    if (mes) {
        modalTitle.textContent = `Reclutadores Comerciales - ${this.config.MESES[mes-1]} ${year}`;
    } else {
        modalTitle.textContent = `Reclutadores Comerciales - ${year}`;
    }
    
    modalSubtitle.textContent = `Total de reclutadores: ${data.length}`;
    
    // Generar tabla
    let html = '';
    
    if (Array.isArray(data) && data.length > 0) {
        // Calcular total para porcentajes
        const totalContrataciones = data.reduce((sum, item) => sum + (item.total || 0), 0);
        
        data.forEach(item => {
            const porcentaje = totalContrataciones > 0 ? 
                ((item.total || 0) / totalContrataciones * 100).toFixed(1) : 0;
            
            // ESCAPAR comillas simples
            const nombreSeguro = (item.nombre || item.reclutador || 'Sin nombre').replace(/'/g, "\\'");
            const idSeguro = item.id || 'null';
            
            html += `
                <tr>
                    <td>
                        <strong>${item.nombre || item.reclutador || 'Sin nombre'}</strong><br>
                        <small class="text-muted">ID: ${item.id || 'N/A'}</small>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-primary fs-6">${item.total || 0}</span>
                    </td>
                    <td class="text-center">
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar bg-info" style="width: ${porcentaje}%">
                                ${porcentaje}%
                            </div>
                        </div>
                    </td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-outline-primary" 
                                onclick="dashboardBI.verDetalleReclutadorPorNombre('${nombreSeguro}')">
                            <i class="bi bi-person-lines-fill"></i> Detalle
                        </button>
                    </td>
                </tr>
            `;
        });
    } else {
        html = `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    <i class="bi bi-people display-4"></i><br>
                    <p class="mt-2">No hay datos disponibles</p>
                </td>
            </tr>
        `;
    }
    
    modalBody.innerHTML = html;
}
    
async verDetalleReclutador(reclutadorId, reclutadorNombre) {
    try {
        console.log('🔍 Iniciando verDetalleReclutador - ID:', reclutadorId, 'Nombre:', reclutadorNombre);
        
        const year = this.state.currentYear || this.config.CURRENT_YEAR;
        
        // PRIMERO: Verificar que reclutadorId sea un número
        let idNumerico = reclutadorId;
        if (typeof reclutadorId === 'string' && isNaN(reclutadorId)) {
            console.warn('⚠️ reclutadorId es texto, no número:', reclutadorId);
            
            // Intentar convertir nombre a ID
            idNumerico = this.convertirNombreAId(reclutadorId);
            if (!idNumerico) {
                console.error('❌ No se pudo convertir nombre a ID');
                this.showToast(`Error: No se encontró el ID para "${reclutadorId}"`, 'danger');
                return;
            }
            console.log('✅ Nombre convertido a ID:', idNumerico);
        }
        
        // SEGUNDO: Construir URL correctamente
        const endpointBase = this.config.API_ENDPOINTS.detalle_reclutador;
        let urlFinal;
        
        // Verificar si el endpoint termina con /
        if (endpointBase.endsWith('/')) {
            urlFinal = `${endpointBase}${idNumerico}?year=${year}`;
        } else {
            urlFinal = `${endpointBase}/${idNumerico}?year=${year}`;
        }
        
        console.log('📡 URL construida:', urlFinal);
        
        // TERCERO: Intentar fetch con manejo de errores mejorado
        let response;
        try {
            response = await fetch(urlFinal, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                // Agregar timeout
                signal: AbortSignal.timeout(10000)
            });
            
            console.log('🔧 Estado de respuesta:', response.status, response.statusText);
            
        } catch (fetchError) {
            console.error('❌ Error en fetch:', fetchError);
            
            if (fetchError.name === 'TimeoutError') {
                this.showToast('Timeout: El servidor no respondió en 10 segundos', 'danger');
            } else if (fetchError.name === 'AbortError') {
                this.showToast('Solicitud cancelada', 'warning');
            } else {
                this.showToast(`Error de conexión: ${fetchError.message}`, 'danger');
            }
            return;
        }
        
        // CUARTO: Procesar respuesta
        if (response.ok) {
            try {
                const data = await response.json();
                console.log('✅ Datos recibidos correctamente:', data);
                
                // Verificar estructura de datos
                if (!data || data.error) {
                    console.warn('⚠️ Datos con error o vacíos:', data);
                    this.showToast(data?.error || 'Datos vacíos recibidos', 'warning');
                    return;
                }
                
                // Asegurar que tenemos nombre para mostrar
                const nombreMostrar = data.reclutador?.nombre || reclutadorNombre || `ID ${idNumerico}`;
                
                // Llenar y mostrar modal
                this.fillModalDetalleReclutador(data, idNumerico, nombreMostrar, year);
                
                // Mostrar modal
                const modalElement = document.getElementById('modalDetalleReclutador');
                if (modalElement) {
                    try {
                        const modal = new bootstrap.Modal(modalElement);
                        modal.show();
                        console.log('✅ Modal mostrado correctamente');
                    } catch (modalError) {
                        console.error('❌ Error mostrando modal:', modalError);
                        this.showToast('Error mostrando ventana de detalles', 'warning');
                    }
                } else {
                    console.error('❌ Modal no encontrado en DOM');
                    this.showToast('Error: No se encontró la ventana de detalles', 'danger');
                }
                
            } catch (jsonError) {
                console.error('❌ Error parseando JSON:', jsonError);
                this.showToast('Error procesando datos del servidor', 'danger');
            }
        } else {
            // Manejar diferentes códigos de error HTTP
            switch (response.status) {
                case 404:
                    console.error('❌ Error 404: Recurso no encontrado');
                    console.log('URL intentada:', urlFinal);
                    this.showToast(
                        `Reclutador no encontrado (ID: ${idNumerico})<br>` +
                        `Verifica que el ID sea correcto`, 
                        'warning'
                    );
                    break;
                    
                case 500:
                    console.error('❌ Error 500: Error interno del servidor');
                    this.showToast('Error interno del servidor', 'danger');
                    break;
                    
                default:
                    console.error(`❌ Error HTTP ${response.status}: ${response.statusText}`);
                    this.showToast(`Error ${response.status}: ${response.statusText}`, 'danger');
            }
            
            // Intentar leer mensaje de error del cuerpo
            try {
                const errorText = await response.text();
                if (errorText) {
                    console.log('📄 Cuerpo de error:', errorText);
                }
            } catch (e) {
                // Ignorar error al leer cuerpo
            }
        }
        
    } catch (error) {
        console.error('❌ Error crítico en verDetalleReclutador:', error);
        this.showToast(`Error inesperado: ${error.message}`, 'danger');
    }
}

// Agrega esta función auxiliar para convertir nombres a IDs
convertirNombreAId(nombreReclutador) {
    // Mapeo de nombres a IDs - ACTUALIZA ESTOS VALORES SEGÚN TU BD
    const mapaNombres = {
        // Ejemplo: 'Nombre en la lista': ID_real_en_BD
        'Comercial': 5,
        'Francesca Argáez': 1,
        'Jazmín Moo': 2,
        'Ana Mata': 3,
        'Rousseli Trejo': 4,
        'Roussell Trejo': 4, // Alternativa de escritura
        'Julio': 6,
        'Nilson': 7,
        'Erick': 8,
        'Sin reclutador asignado': 0
    };
    
    // Buscar coincidencia exacta
    if (mapaNombres[nombreReclutador]) {
        return mapaNombres[nombreReclutador];
    }
    
    // Buscar coincidencia insensible a mayúsculas
    const nombreLower = nombreReclutador.toLowerCase();
    for (const [nombre, id] of Object.entries(mapaNombres)) {
        if (nombre.toLowerCase() === nombreLower) {
            console.log('✅ Coincidencia insensible encontrada:', nombre, '->', id);
            return id;
        }
    }
    
    // Si no se encuentra, intentar con los datos locales
    if (this.state.reclutadoresData) {
        const reclutadorLocal = this.state.reclutadoresData.find(r => 
            r.reclutador?.toLowerCase() === nombreLower ||
            r.nombre?.toLowerCase() === nombreLower
        );
        
        if (reclutadorLocal && reclutadorLocal.reclutador_id) {
            console.log('✅ Encontrado en datos locales:', reclutadorLocal.reclutador_id);
            return reclutadorLocal.reclutador_id;
        }
    }
    
    console.error('❌ No se pudo convertir nombre a ID:', nombreReclutador);
    return null;
}
    
fillModalDetalleReclutador(data, reclutadorId, reclutadorNombre, year) {
    const modalElement = document.getElementById('modalDetalleReclutador');
    if (!modalElement) {
        console.error('❌ Modal no encontrado en DOM');
        return;
    }

    // Limpiar modal anterior si existe
    const oldModal = bootstrap.Modal.getInstance(modalElement);
    if (oldModal) oldModal.dispose();

    // Actualizar título
    const titleElement = modalElement.querySelector('#modalReclutadorTitle');
    if (titleElement) {
        titleElement.innerHTML = `<i class="bi bi-person-badge me-2"></i>${reclutadorNombre} - ${year}`;
    }

    const modalBody = modalElement.querySelector('.modal-body');
    if (!modalBody) return;

    // Extraer datos
    let contratos = [];
    let totalAnual = 0;

    if (data && !data.error) {
        if (data.contratos && Array.isArray(data.contratos)) {
            contratos = data.contratos;
            totalAnual = data.total_anual || 0;
        } else if (Array.isArray(data)) {
            contratos = data;
            totalAnual = data.reduce((sum, item) => sum + (item.total || 0), 0);
        }

        // Crear el HTML con el gráfico
        const html = `
            <div class="container-fluid">
                <!-- FILA 1: GRÁFICO -->
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="card border-0 shadow-sm">
                            <div class="card-body">
                                <h6 class="card-title mb-3">
                                    <i class="bi bi-bar-chart-line me-2"></i>Desempeño Mensual
                                </h6>
                                <div class="chart-container" style="position: relative; height: 250px;">
                                    <canvas id="chartReclutadorDetalle"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- FILA 2: TABLA -->
                <div class="row">
                    <div class="col-12">
                        <div class="card border-0 shadow-sm">
                            <div class="card-body">
                                <h6 class="card-title mb-3">
                                    <i class="bi bi-table me-2"></i>Detalle por Mes
                                </h6>
                                <div class="table-responsive">
                                    <table class="table table-sm table-hover">
                                        <thead>
                                            <tr>
                                                <th>Mes</th>
                                                <th class="text-center">Contrataciones</th>
                                                <th>Progreso</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${this.generarFilasTabla(contratos)}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- INFORMACIÓN -->
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="alert alert-light">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>Total Anual:</strong> ${totalAnual} contrataciones
                                </div>
                                <div>
                                    <small class="text-muted">
                                        <i class="bi bi-person me-1"></i>${reclutadorNombre}
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        modalBody.innerHTML = html;

        // IMPORTANTE: Inicializar el gráfico DESPUÉS de que el HTML esté en el DOM
        setTimeout(() => {
            this.initChartReclutadorDetalle(contratos, reclutadorNombre);
        }, 50);

    } else {
        modalBody.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-exclamation-triangle display-6 text-warning mb-3"></i>
                <h5>No se encontraron datos</h5>
                <p class="text-muted">No hay información disponible para este reclutador</p>
            </div>
        `;
    }

    // Configurar eventos para limpiar correctamente al cerrar
    const cleanupOnClose = () => {
        console.log('🔧 Limpiando gráfico al cerrar modal');
        if (this.state.charts.reclutadorDetalle) {
            this.state.charts.reclutadorDetalle.destroy();
            this.state.charts.reclutadorDetalle = null;
        }
        
        // Asegurar que el backdrop se elimine
        setTimeout(() => {
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                if (backdrop.parentNode) {
                    backdrop.parentNode.removeChild(backdrop);
                }
            });
            
            // Restaurar el scroll del body
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }, 10);
        
        // Remover el event listener para evitar duplicados
        modalElement.removeEventListener('hidden.bs.modal', cleanupOnClose);
    };

    // Asegurar que solo hay un event listener
    modalElement.removeEventListener('hidden.bs.modal', cleanupOnClose);
    modalElement.addEventListener('hidden.bs.modal', cleanupOnClose);

    // Mostrar el modal
    setTimeout(() => {
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: true,      // Permite cerrar haciendo clic fuera
            keyboard: true,      // Permite cerrar con ESC
            focus: true         // Enfoca en el modal
        });
        
        // Configurar botón de cierre manual
        const closeButton = modalElement.querySelector('[data-bs-dismiss="modal"]');
        if (closeButton) {
            closeButton.onclick = () => {
                modal.hide();
            };
        }
        
        modal.show();
    }, 100);
}

initChartReclutadorDetalle(contratos, reclutadorNombre) {
    const canvas = document.getElementById('chartReclutadorDetalle');
    if (!canvas) {
        console.error('❌ No se encontró el canvas para el gráfico');
        return;
    }

    // Limpiar gráfico anterior si existe
    if (this.state.charts.reclutadorDetalle) {
        this.state.charts.reclutadorDetalle.destroy();
    }

    const ctx = canvas.getContext('2d');
    
    // Preparar datos para el gráfico
    const contratosOrdenados = [...contratos].sort((a, b) => a.mes_num - b.mes_num);
    const labels = contratosOrdenados.map(item => 
        this.config.MESES_CORTOS[item.mes_num - 1] || `M${item.mes_num}`
    );
    const data = contratosOrdenados.map(item => item.total || 0);

    // Crear el gráfico
    this.state.charts.reclutadorDetalle = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Contrataciones - ${reclutadorNombre}`,
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                borderRadius: 5,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Contrataciones: ${context.raw}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    },
                    title: {
                        display: true,
                        text: 'Cantidad'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Mes'
                    }
                }
            }
        }
    });

    console.log('✅ Gráfico de reclutador inicializado correctamente');
}

// Función para limpiar el gráfico cuando se cierra el modal
cleanupChartReclutadorDetalle() {
    if (this.state.charts.reclutadorDetalle) {
        this.state.charts.reclutadorDetalle.destroy();
        this.state.charts.reclutadorDetalle = null;
    }
}
// Función auxiliar para generar filas de tabla
generarFilasTabla(contratos) {
    if (!contratos || contratos.length === 0) {
        return '<tr><td colspan="3" class="text-center text-muted">Sin datos</td></tr>';
    }

    const contratosOrdenados = [...contratos].sort((a, b) => a.mes_num - b.mes_num);
    const maxMes = Math.max(...contratosOrdenados.map(item => item.total || 0), 1);

    let html = '';
    contratosOrdenados.forEach((item) => {
        const mesNombre = this.config.MESES[item.mes_num - 1] || `Mes ${item.mes_num}`;
        const totalMes = item.total || 0;
        const porcentaje = maxMes > 0 ? ((totalMes / maxMes) * 100).toFixed(0) : 0;
        
        let badgeClass = 'bg-secondary';
        if (totalMes >= 5) badgeClass = 'bg-success';
        else if (totalMes >= 3) badgeClass = 'bg-info';
        else if (totalMes >= 1) badgeClass = 'bg-warning';

        html += `
            <tr>
                <td class="fw-medium">${mesNombre}</td>
                <td class="text-center">
                    <span class="badge ${badgeClass}">${totalMes}</span>
                </td>
                <td>
                    <div class="progress" style="height: 10px;">
                        <div class="progress-bar" style="width: ${porcentaje}%"></div>
                    </div>
                </td>
            </tr>
        `;
    });

    return html;
}

// 8. FUNCIÓN AUXILIAR para configurar eventos del modal
configurarModalEvents(modalElement) {
    if (!modalElement) return;
    
    // Eliminar eventos antiguos
    modalElement.removeEventListener('hidden.bs.modal', this.handleModalClose);
    modalElement.removeEventListener('hide.bs.modal', this.handleModalHide);
    
    // Agregar nuevos eventos
    modalElement.addEventListener('hidden.bs.modal', () => {
        console.log('✅ Modal completamente oculto');
        
        // Asegurar que el backdrop se elimine
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            backdrop.remove();
        });
        
        // Remover clase de modal abierto del body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // Opcional: Eliminar el modal del DOM si se creó dinámicamente
        // modalElement.remove();
    });
    
    modalElement.addEventListener('hide.bs.modal', () => {
        console.log('🔧 Modal comenzando a ocultarse');
    });
    
    // Configurar el botón de cerrar del header
    const closeButton = modalElement.querySelector('[data-bs-dismiss="modal"]');
    if (closeButton) {
        closeButton.onclick = () => {
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
        };
    }
}
    
    // =========================
    // FUNCIONES PÚBLICAS ORIGINALES (actualizadas)
    // =========================
    async verDetalleReclutadorPorNombre(nombreReclutador) {
        try {
            // Buscar el ID del reclutador
            const searchData = await this.fetchData('buscar_reclutador', 
                { nombre: nombreReclutador }
            );
            
            if (searchData && !searchData.error) {
                let reclutadorId;
                let reclutadorNombreFinal;
                
                if (Array.isArray(searchData)) {
                    if (searchData.length > 0) {
                        reclutadorId = searchData[0].id;
                        reclutadorNombreFinal = searchData[0].nombre || nombreReclutador;
                    }
                } else if (searchData.id) {
                    reclutadorId = searchData.id;
                    reclutadorNombreFinal = searchData.nombre || nombreReclutador;
                }
                
                if (reclutadorId) {
                    // Usar la nueva función verDetalleReclutador
                    await this.verDetalleReclutador(reclutadorId, reclutadorNombreFinal);
                    return;
                }
            }
            
            // Si no encontramos el ID
            if (!this.state.reclutadoresData) return;
            
            const reclutador = this.state.reclutadoresData.find(r => r.reclutador === nombreReclutador);
            if (reclutador) {
                this.showToast(`Reclutador: ${nombreReclutador}<br>Total anual: ${reclutador.total_anual}`, 'info');
            } else {
                this.showToast('No se encontró el reclutador.', 'warning');
            }
            
        } catch (error) {
            console.error('Error buscando reclutador:', error);
            this.showToast('Error al buscar el reclutador.', 'danger');
        }
    }
    
    // =========================
    // API PÚBLICA
    // =========================
    reload() {
        this.state.dataCache.clear();
        this.loadData();
    }
    
    refreshCharts() {
        Object.values(this.state.charts).forEach(chart => {
            if (chart) chart.update();
        });
    }
    
    getState() {
        return { ...this.state };
    }
    
    setYear(year) {
        this.state.currentYear = year;
        if (this.dom.yearSelect) {
            this.dom.yearSelect.value = year;
        }
        this.state.dataCache.clear();
        this.loadData();
    }
}

// Inicializar dashboard cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new DashboardBI();
    });
} else {
    new DashboardBI();
}

// Solución temporal - exponer funciones faltantes globalmente
window.showModalDetalleComercial = function() {
    if (window.dashboardBI) {
        window.dashboardBI.showModalDetalleComercial();
    } else {
        alert('Dashboard no está inicializado. Recarga la página.');
    }
};

window.showModalDetalleReclutadores = function() {
    if (window.dashboardBI) {
        window.dashboardBI.showModalDetalleReclutadores();
    } else {
        alert('Dashboard no está inicializado. Recarga la página.');
    }
};

window.showReclutadoresPorMes = function(mes) {
    if (window.dashboardBI) {
        window.dashboardBI.showReclutadoresPorMes(mes);
    } else {
        alert('Dashboard no está inicializado. Recarga la página.');
    }
};

