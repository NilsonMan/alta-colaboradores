// static/js/auth-modal.js
class AuthModalManager {
    constructor() {
        this.modal = null;
        this.init();
    }
    
    init() {
        console.log('AuthModalManager inicializado');
        
        // Verificar si el usuario está autenticado
        this.checkAuthStatus();
        
        // Escuchar clics en enlaces que requieren autenticación
        document.addEventListener('click', (e) => {
            const link = e.target.closest('[data-requires-auth]');
            if (link) {
                e.preventDefault();
                this.showAuthRequired();
            }
        });
        
        // Escalar clics en botones que abren el modal
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[data-bs-toggle="modal"]');
            if (button && button.dataset.bsTarget === '#authModal') {
                e.preventDefault();
                this.showAuthRequired();
            }
        });
    }
    
    checkAuthStatus() {
        // Verificar si hay una sesión activa
        const authElements = document.querySelectorAll('[data-auth-required]');
        authElements.forEach(element => {
            const requiredArea = element.dataset.requiredArea;
            if (requiredArea) {
                const userArea = document.body.dataset.userArea;
                if (userArea && userArea === requiredArea) {
                    element.classList.remove('d-none');
                } else {
                    element.classList.add('d-none');
                }
            }
        });
    }
    
    showAuthRequired() {
        // Obtener o crear el modal
        let modalElement = document.getElementById('authModal');
        
        if (!modalElement) {
            // Crear modal dinámicamente si no existe
            this.createModal();
            modalElement = document.getElementById('authModal');
        }
        
        // Mostrar el modal
        this.modal = new bootstrap.Modal(modalElement);
        this.modal.show();
        
        // Configurar comportamiento del botón de login
        const loginBtn = modalElement.querySelector('.btn-login-modal');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                window.location.href = '/login';
            });
        }
    }
    
    createModal() {
        const modalHTML = `
            <div class="modal fade" id="authModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">
                                <i class="bi bi-shield-lock me-2"></i>
                                Acceso Restringido
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center py-4">
                            <div class="mb-3">
                                <i class="bi bi-person-lock" style="font-size: 3rem; color: #6c757d;"></i>
                            </div>
                            <h4 class="mb-3">Inicio de Sesión Requerido</h4>
                            <p class="text-muted mb-4">
                                Para acceder a esta sección, necesitas tener permisos especiales.
                                Solo las áreas autorizadas pueden ver esta información.
                            </p>
                            
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                <div>
                                    <strong>Áreas autorizadas:</strong> ID 3 y 4
                                    <br>
                                    <small class="text-muted">
                                        Si perteneces a estas áreas, contacta al administrador para obtener credenciales.
                                    </small>
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <button class="btn btn-primary btn-lg px-4 btn-login-modal">
                                    <i class="bi bi-box-arrow-in-right me-2"></i>
                                    Ir a Iniciar Sesión
                                </button>
                                <button type="button" class="btn btn-outline-secondary btn-lg px-4 ms-2" 
                                        data-bs-dismiss="modal">
                                    Cancelar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    showSessionExpired() {
        const expiredHTML = `
            <div class="modal fade" id="sessionExpiredModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title">
                                <i class="bi bi-exclamation-triangle me-2"></i>
                                Sesión Expirada
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center py-4">
                            <div class="mb-3">
                                <i class="bi bi-clock-history" style="font-size: 3rem; color: #ffc107;"></i>
                            </div>
                            <h4 class="mb-3">Tu sesión ha expirado</h4>
                            <p class="text-muted mb-4">
                                Por seguridad, tu sesión ha caducado. Por favor, inicia sesión nuevamente.
                            </p>
                            
                            <div class="mt-4">
                                <button class="btn btn-warning btn-lg px-4" onclick="window.location.href='/login'">
                                    <i class="bi bi-box-arrow-in-right me-2"></i>
                                    Volver a Iniciar Sesión
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', expiredHTML);
        const modal = new bootstrap.Modal(document.getElementById('sessionExpiredModal'));
        modal.show();
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthModalManager();
    
    // Verificar si hay parámetros de error en la URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('auth_required')) {
        window.authManager.showAuthRequired();
    }
    
    // Interceptar llamadas AJAX para verificar autenticación
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(response => {
            if (response.status === 401) {
                // Sesión expirada o no autenticado
                window.authManager.showSessionExpired();
                throw new Error('Authentication required');
            }
            return response;
        });
    };
});