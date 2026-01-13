// static/js/dark-mode-manager.js - VERSIÓN MEJORADA
class DarkModeManager {
    constructor() {
        this.body = document.body;
        this.html = document.documentElement;
        this.btnDarkMode = document.getElementById('btnDarkMode');
        this.darkModeIcon = document.getElementById('darkModeIcon');
        this.init();
    }
    
    init() {
        // Evitar doble inicialización
        if (window.darkModeManager) {
            return window.darkModeManager;
        }
        window.darkModeManager = this;
        
        // Configurar estado inicial
        this.setupInitialState();
        
        // Configurar listeners
        this.setupListeners();
        
        // Aplicar estado actual
        this.applyCurrentState();
    }
    
    setupInitialState() {
        // Primero aplicar clases de Bootstrap
        const saved = localStorage.getItem('darkMode');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const isDark = saved !== null ? saved === 'true' : prefersDark;
        
        // Aplicar clase de Bootstrap para controles de formulario
        this.html.setAttribute('data-bs-theme', isDark ? 'dark' : 'light');
        
        // Aplicar clase personalizada para estilos CSS
        this.body.classList.toggle('dark-mode', isDark);
        this.body.classList.toggle('dark', isDark);
        
        // Guardar estado
        localStorage.setItem('darkMode', String(isDark));
    }
    
    getCurrentState() {
        // Verificar localStorage primero
        const saved = localStorage.getItem('darkMode');
        if (saved !== null) {
            return saved === 'true';
        }
        
        // Si no hay valor guardado, verificar preferencia del sistema
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        return prefersDark;
    }
    
    applyCurrentState() {
        const isDark = this.getCurrentState();
        this.setDarkMode(isDark);
    }
    
    setDarkMode(isDark) {
        // 1. Aplicar atributo de Bootstrap para controles de formulario
        this.html.setAttribute('data-bs-theme', isDark ? 'dark' : 'light');
        
        // 2. Aplicar clases para CSS personalizado
        this.body.classList.toggle('dark-mode', isDark);
        this.body.classList.toggle('dark', isDark);
        
        // 3. Actualizar icono
        this.updateIcon(isDark);
        
        // 4. Actualizar meta theme-color
        this.updateMetaTheme(isDark);
        
        // 5. Guardar en localStorage
        localStorage.setItem('darkMode', String(isDark));
        
        // 6. Disparar evento personalizado
        this.dispatchChangeEvent(isDark);
        
        return isDark;
    }
    
    updateIcon(isDark) {
        if (this.darkModeIcon) {
            this.darkModeIcon.textContent = isDark ? '☀️' : '🌙';
            this.darkModeIcon.title = isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
        }
    }
    
    updateMetaTheme(isDark) {
        // Actualizar meta theme-color para PWA
        let metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) {
            metaTheme.content = isDark ? '#0f172a' : '#ffffff';
        }
    }
    
    dispatchChangeEvent(isDark) {
        window.dispatchEvent(new CustomEvent('darkModeChanged', {
            detail: { isDark }
        }));
    }
    
    setupListeners() {
        // Botón de dark mode
        if (this.btnDarkMode) {
            this.btnDarkMode.addEventListener('click', () => this.toggle());
        }
        
        // Escuchar preferencias del sistema (solo si no hay preferencia guardada)
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            if (localStorage.getItem('darkMode') === null) {
                this.setDarkMode(e.matches);
            }
        });
    }
    
    toggle() {
        const currentState = this.body.classList.contains('dark-mode');
        return this.setDarkMode(!currentState);
    }
    
    // Métodos públicos
    enable() {
        return this.setDarkMode(true);
    }
    
    disable() {
        return this.setDarkMode(false);
    }
    
    isEnabled() {
        return this.body.classList.contains('dark-mode');
    }
}

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    new DarkModeManager();
});