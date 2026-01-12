// ============================================
// UTILIDADES COMPARTIDAS - DARK MODE
// ============================================

(function() {
    'use strict';
    
    const DarkModeUtils = {
        // Aplicar dark mode al cargar
        init() {
            this.applySavedState();
            this.setupObservers();
            this.setupCrossTabSync();
        },
        
        // Aplicar estado guardado
        applySavedState() {
            const saved = localStorage.getItem('darkMode');
            const isDark = saved === 'true';
            
            if (isDark) {
                document.body.classList.add('dark');
            } else {
                document.body.classList.remove('dark');
            }
            
            console.log(`DarkModeUtils: ${isDark ? 'Modo oscuro activado' : 'Modo claro activado'}`);
            return isDark;
        },
        
        // Cambiar estado
        toggle() {
            const isDark = !document.body.classList.contains('dark');
            return this.set(isDark);
        },
        
        // Establecer estado específico
        set(isDark) {
            const body = document.body;
            
            if (isDark) {
                body.classList.add('dark');
            } else {
                body.classList.remove('dark');
            }
            
            localStorage.setItem('darkMode', isDark);
            
            // Disparar eventos para sincronización
            this.dispatchChangeEvent(isDark);
            this.dispatchStorageEvent(isDark);
            
            return isDark;
        },
        
        // Obtener estado actual
        get() {
            return document.body.classList.contains('dark');
        },
        
        // Disparar evento de cambio
        dispatchChangeEvent(isDark) {
            window.dispatchEvent(new CustomEvent('darkModeChange', {
                detail: { isDark }
            }));
        },
        
        // Disparar evento de storage (para sincronización entre pestañas)
        dispatchStorageEvent(isDark) {
            // Simular evento storage
            window.dispatchEvent(new StorageEvent('storage', {
                key: 'darkMode',
                newValue: isDark.toString(),
                oldValue: (!isDark).toString(),
                url: window.location.href,
                storageArea: localStorage
            }));
        },
        
        // Configurar observadores
        setupObservers() {
            // Observar cambios en localStorage (para sincronización entre pestañas)
            window.addEventListener('storage', (e) => {
                if (e.key === 'darkMode') {
                    const isDark = e.newValue === 'true';
                    this.set(isDark);
                }
            });
            
            // Observar cambios en el body
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.attributeName === 'class') {
                        const isDark = this.get();
                        localStorage.setItem('darkMode', isDark);
                    }
                });
            });
            
            observer.observe(document.body, { attributes: true });
        },
        
        // Sincronización entre pestañas mejorada
        setupCrossTabSync() {
            // También escuchar nuestro propio evento personalizado
            window.addEventListener('darkModeToggle', (e) => {
                this.set(e.detail.isDark);
            });
            
            window.addEventListener('darkModeChange', (e) => {
                this.set(e.detail.isDark);
            });
        },
        
        // Actualizar icono (si existe en la página)
        updateIcon() {
            const icon = document.getElementById('darkModeIcon');
            if (icon) {
                const isDark = this.get();
                icon.textContent = isDark ? '☀️' : '🌙';
                icon.title = isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
            }
        }
    };
    
    // Inicializar al cargar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => DarkModeUtils.init());
    } else {
        DarkModeUtils.init();
    }
    
    // Exportar para uso global
    window.DarkModeUtils = DarkModeUtils;
})();