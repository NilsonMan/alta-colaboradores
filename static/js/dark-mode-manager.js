// static/js/dark-mode-manager.js
class DarkModeManager {
    constructor() {
        this.body = document.body;
        this.btnDarkMode = document.getElementById('btnDarkMode');
        this.darkModeIcon = document.getElementById('darkModeIcon');
        this.init();
    }
    
    init() {
        // Evitar doble inicialización
        if (window.darkModeManager) return;
        window.darkModeManager = this;
        
        // Configurar listeners
        this.setupListeners();
        
        // Aplicar estado guardado
        this.applySavedState();
    }
    
    applySavedState() {
        const saved = localStorage.getItem('darkMode');
        const isDark = saved === null ? false : saved === 'true';
        
        this.body.classList.toggle('dark', isDark);
        this.updateMetaTheme(isDark);
        this.updateIcon(isDark);
    }
    
    updateMetaTheme(isDark) {
        let metaTheme = document.querySelector('meta[name="theme-color"]');
        if (!metaTheme) {
            metaTheme = document.createElement('meta');
            metaTheme.name = 'theme-color';
            document.head.appendChild(metaTheme);
        }
        metaTheme.content = isDark ? '#0f172a' : '#ffffff';
    }
    
    updateIcon(isDark) {
        if (this.darkModeIcon) {
            this.darkModeIcon.textContent = isDark ? '☀️' : '🌙';
        }
    }
    
    setupListeners() {
        // Botón de dark mode
        if (this.btnDarkMode) {
            this.btnDarkMode.addEventListener('click', () => this.toggle());
        }
        
        // Sincronización entre pestañas
        window.addEventListener('storage', (e) => {
            if (e.key === 'darkMode') {
                this.applySavedState();
            }
        });
    }
    
    toggle() {
        const isDark = !this.body.classList.contains('dark');
        
        this.body.classList.toggle('dark', isDark);
        localStorage.setItem('darkMode', String(isDark));
        this.updateMetaTheme(isDark);
        this.updateIcon(isDark);
        
        window.dispatchEvent(new CustomEvent('darkModeToggled', {
            detail: { isDark }
        }));
        
        return isDark;
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new DarkModeManager());
} else {
    new DarkModeManager();
}