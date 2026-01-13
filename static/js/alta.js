// ============================================
// MÓDULO PRINCIPAL - ALTA COLABORADOR V2.3
// ============================================

(function() {
    'use strict';
    
    // =========================
    // CONFIGURACIÓN Y CONSTANTES
    // =========================
    const CONFIG = window.APP_CONFIG || {
        dominioCorreo: '@marnezdesarrollos.com',
        AREA_COMERCIAL_ID: 2,
        MAX_FILE_SIZE: 10485760,
        today: new Date().toISOString().split('T')[0]
    };
    
    const VALIDATION = window.VALIDATION_REGEX || {
        curp: /^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z\d]{2}$/,
        email: /^[^\s@]+@marnezdesarrollos\.com$/i
    };
    
    // =========================
    // ELEMENTOS DEL DOM
    // =========================
    const DOM = {
        formulario: document.getElementById('formulario'),
        correoInput: document.getElementById('correo'),
        nombreInput: document.getElementById('nombre'),
        apellidoInput: document.getElementById('apellido'),
        estadoCorreo: document.getElementById('estadoCorreo'),
        areaSelect: document.getElementById('area'),
        btnConfirmarCorreo: document.getElementById('btnConfirmarCorreo'),
        correoSi: document.getElementById('correoSi'),
        correoNo: document.getElementById('correoNo'),
        puestoSelect: document.getElementById('puesto'),
        puestoComercialSelect: document.getElementById('rol_comercial'),
        sueldoInput: document.getElementById('sueldo'),
        areaHidden: document.getElementById('areaHidden'),
        correoConfirmacion: document.getElementById('correoConfirmacion'),
        rfcInput: document.querySelector('input[name="rfc"]')
    };
    
    // =========================
    // ESTADO DE LA APLICACIÓN
    // =========================
    const STATE = {
        correoConfirmado: false,
        modalMostrado: false,
        timerCorreo: null,
        areaSeleccionada: null,
        esComercial: false,
        documentosCargados: 0,
        totalDocumentos: 9,
        camposDuplicados: {
            correo: false,
            rfc: false,
            curp: false,
            nss: false
        },
        verificacionesPendientes: new Set(),
        documentos: new Map(),
        usuarioRegistrado: false,
        modalUsuarioRegistrado: null,
        previewModal: null
    };
    
    // =========================
    // MODALES
    // =========================
    const MODALS = {
        correo: DOM.correoSi ? new bootstrap.Modal(
            document.getElementById('modalCorreo'),
            { backdrop: 'static', keyboard: false }
        ) : null,
        preview: null,
        baja: null,
        cambioArea: null,
        usuarioRegistrado: null
    };
    
    // =========================
    // INICIALIZACIÓN DE COMPONENTES
    // =========================
    function initComponents() {
        console.log('Inicializando módulo de alta V2.3...');
        
        initValidations();
        initAreaManager();
        initEmailManager();
        initDocumentManager();
        initFormSubmitter();
        initSectionToggles();
        initCharacterCounter();
        initFormEnhancements();
        initDuplicateChecker();
        initBotonesEspeciales();
        initRFCValidation();
        initVerificacionRFC();
        
        updateDocumentCounter();
        
        console.log('Módulo de alta V2.3 inicializado correctamente');
    }
    
    // =========================
    // VERIFICACIÓN DE RFC AL BOTÓN "COLABORADOR"
    // =========================
    function initVerificacionRFC() {
        const btnColaborador = document.getElementById('btnColaborador');
        if (!btnColaborador) return;
        
        btnColaborador.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const rfc = DOM.rfcInput ? DOM.rfcInput.value.trim() : '';
            
            if (!rfc || rfc.length < 12) {
                showToast('Error', 'Ingresa un RFC válido (12-13 caracteres)', 'warning');
                DOM.rfcInput?.focus();
                return;
            }
            
            await verificarRFC(rfc);
        });
    }
    
    // =========================
    // VERIFICAR RFC EN SERVIDOR
    // =========================
    async function verificarRFC(rfc) {
        try {
            // Mostrar carga
            if (DOM.rfcInput) {
                DOM.rfcInput.classList.add('is-validating');
            }
            
            // Simular llamada al servidor (en producción sería fetch)
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Datos de ejemplo
            const usuarioExistente = Math.random() > 0.5;
            
            if (usuarioExistente) {
                mostrarInfoColaboradorExistente({
                    nombre: 'Juan Pérez González',
                    rfc: rfc,
                    correo: 'juan.perez@marnezdesarrollos.com',
                    area: 'Ventas',
                    estado: 'Activo',
                    fecha_alta: '2023-05-15',
                    puesto: 'Asesor Comercial'
                });
            } else {
                showToast('RFC disponible', 'No se encontró un colaborador con este RFC', 'success');
            }
            
        } catch (error) {
            console.error('Error verificando RFC:', error);
            showToast('Error', 'No se pudo verificar el RFC', 'danger');
        } finally {
            if (DOM.rfcInput) {
                DOM.rfcInput.classList.remove('is-validating');
            }
        }
    }
    
    // =========================
    // MOSTRAR INFORMACIÓN DE COLABORADOR EXISTENTE
    // =========================
    function mostrarInfoColaboradorExistente(datos) {
        const modalElement = document.getElementById('modalUsuarioRegistrado');
        if (!modalElement) return;
        
        // Actualizar datos en el modal
        document.getElementById('dupNombre').textContent = datos.nombre;
        document.getElementById('dupRFC').textContent = datos.rfc;
        document.getElementById('dupCorreo').textContent = datos.correo;
        document.getElementById('dupArea').textContent = datos.area;
        document.getElementById('dupEstado').textContent = datos.estado;
        
        // Configurar botón de continuar
        const btnContinuar = document.getElementById('btnContinuarRegistro');
        if (btnContinuar) {
            btnContinuar.addEventListener('click', function() {
                const confirmado = document.getElementById('confirmarNuevoRegistro').checked;
                
                if (!confirmado) {
                    showToast('Atención', 'Debes confirmar que es un nuevo registro', 'warning');
                    return;
                }
                
                MODALS.usuarioRegistrado.hide();
                showToast('Procediendo', 'Puedes continuar con el alta del colaborador', 'info');
            }, { once: true });
        }
        
        // Mostrar modal
        MODALS.usuarioRegistrado = MODALS.usuarioRegistrado || new bootstrap.Modal(modalElement);
        MODALS.usuarioRegistrado.show();
    }
    
    // =========================
    // VALIDACIÓN RFC (13 caracteres)
    // =========================
    function initRFCValidation() {
        if (!DOM.rfcInput) return;
        
        DOM.rfcInput.maxLength = 13;
        
        DOM.rfcInput.addEventListener('input', function(e) {
            let value = e.target.value.toUpperCase();
            
            if (value.length > 13) {
                value = value.substring(0, 13);
            }
            
            value = value.replace(/[^A-Z0-9-]/g, '');
            
            e.target.value = value;
            
            if (value.length >= 12 && value.length <= 13) {
                e.target.classList.remove('is-invalid');
                e.target.classList.add('is-valid');
            } else if (value.length > 0 && value.length < 12) {
                e.target.classList.remove('is-valid');
                e.target.classList.add('is-invalid');
            } else {
                e.target.classList.remove('is-valid', 'is-invalid');
            }
        });
        
        DOM.rfcInput.addEventListener('blur', function() {
            if (this.value.length > 0 && (this.value.length < 12 || this.value.length > 13)) {
                this.classList.add('is-invalid');
                showToast('RFC inválido', 'El RFC debe tener entre 12 y 13 caracteres', 'warning');
            }
        });
    }
    
    // =========================
    // MANEJADOR DE DOCUMENTOS - CON PREVISUALIZACIÓN
    // =========================
    function initDocumentManager() {
        console.log('Inicializando gestor de documentos...');
        
        document.querySelectorAll('.doc-card input[type="file"]').forEach(input => {
            input.addEventListener('change', handleFileUpload);
        });
        
        initDragAndDrop();
    }
    
    function handleFileUpload(e) {
        const input = e.target;
        const file = input.files[0];
        
        if (!file) {
            console.log('No se seleccionó archivo');
            return;
        }
        
        console.log('Archivo seleccionado:', file.name, file.size, file.type);
        
        validateAndProcessFile(file, input);
    }
    
    function validateAndProcessFile(file, input) {
        const maxSize = parseInt(input.dataset.maxSize) || CONFIG.MAX_FILE_SIZE;
        const card = input.closest('.doc-card');
        const fileName = card.querySelector('.doc-title').textContent;
        
        console.log(`Validando documento: ${fileName}`);
        
        if (file.size > maxSize) {
            showToast('Error', `El archivo excede el tamaño máximo de ${maxSize / 1024 / 1024}MB`, 'danger');
            input.value = '';
            removeDocument(fileName);
            return;
        }
        
        if (!file.type.match(/(pdf|image\/jpeg|image\/jpg|image\/png)/)) {
            showToast('Error', 'Solo se permiten archivos PDF, JPG o PNG', 'danger');
            input.value = '';
            removeDocument(fileName);
            return;
        }
        
        if (!card.classList.contains('flipped')) {
            STATE.documentosCargados++;
        }
        
        STATE.documentos.set(fileName, file);
        
        card.classList.add('flipped');
        
        setTimeout(() => {
            updateUploadProgress();
        }, 300);
        
        if (file.type.startsWith('image/')) {
            previewImage(file, card);
        }
        
        // Actualizar nombre de archivo en la tarjeta
        const fileNameElement = card.querySelector('.doc-file-name');
        if (fileNameElement) {
            fileNameElement.textContent = file.name;
        }
        
        console.log(`Documento cargado: ${fileName} (${STATE.documentosCargados}/${STATE.totalDocumentos})`);
        showToast('✅ Documento cargado', `${fileName} cargado correctamente`, 'success');
    }
    
    // =========================
    // PREVISUALIZACIÓN DE DOCUMENTOS
    // =========================
    function initPreviewModal() {
        const modalElement = document.getElementById('modalPreview');
        if (!modalElement) return;
        
        MODALS.preview = new bootstrap.Modal(modalElement);
        
        // Configurar descarga
        const downloadBtn = document.getElementById('downloadPreview');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const currentFile = STATE.currentPreviewFile;
                if (currentFile) {
                    const url = URL.createObjectURL(currentFile);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = currentFile.name;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }
            });
        }
    }
    
    // =========================
    // FUNCIÓN GLOBAL PARA PREVISUALIZAR
    // =========================
    window.previsualizarDocumento = function(btn) {
        const card = btn.closest('.doc-card');
        if (!card) return;
        
        const fileName = card.querySelector('.doc-title').textContent;
        const file = STATE.documentos.get(fileName);
        
        if (!file) {
            showToast('Error', 'No hay documento para previsualizar', 'warning');
            return;
        }
        
        mostrarPrevisualizacion(file);
    };
    
    function mostrarPrevisualizacion(file) {
        if (!MODALS.preview) {
            initPreviewModal();
        }
        
        const iframe = document.getElementById('previewFrame');
        const img = document.getElementById('previewImg');
        const unsupported = document.getElementById('previewUnsupported');
        const downloadBtn = document.getElementById('downloadPreview');
        
        // Resetear displays
        iframe.style.display = 'none';
        img.style.display = 'none';
        unsupported.classList.add('d-none');
        
        // Guardar archivo actual para descarga
        STATE.currentPreviewFile = file;
        
        // Configurar descarga
        if (downloadBtn) {
            downloadBtn.href = '#';
        }
        
        if (file.type.includes('pdf')) {
            const url = URL.createObjectURL(file);
            iframe.src = url;
            iframe.style.display = 'block';
        } else if (file.type.includes('image')) {
            const url = URL.createObjectURL(file);
            img.src = url;
            img.style.display = 'block';
        } else {
            unsupported.classList.remove('d-none');
        }
        
        // Mostrar modal
        MODALS.preview.show();
        
        // Liberar URL cuando se cierre el modal
        const modalElement = document.getElementById('modalPreview');
        modalElement.addEventListener('hidden.bs.modal', () => {
            if (iframe.src) URL.revokeObjectURL(iframe.src);
            if (img.src) URL.revokeObjectURL(img.src);
        }, { once: true });
    }
    
    // =========================
    // FUNCIÓN GLOBAL PARA CAMBIAR DOCUMENTO
    // =========================
    window.cambiarDocumento = function(btn) {
        const card = btn.closest('.doc-card');
        if (!card) return;
        
        const input = card.querySelector('input[type="file"]');
        if (!input) return;
        
        const fileName = card.querySelector('.doc-title').textContent;
        
        if (card.classList.contains('flipped')) {
            STATE.documentosCargados = Math.max(0, STATE.documentosCargados - 1);
            STATE.documentos.delete(fileName);
        }
        
        card.classList.remove('flipped');
        input.value = '';
        
        // Limpiar nombre de archivo
        const fileNameElement = card.querySelector('.doc-file-name');
        if (fileNameElement) {
            fileNameElement.textContent = '';
        }
        
        setTimeout(() => {
            updateUploadProgress();
        }, 300);
        
        setTimeout(() => input.click(), 100);
    };
    
    function updateDocumentCounter() {
        STATE.documentosCargados = document.querySelectorAll('.doc-card.flipped').length;
        console.log(`Documentos cargados: ${STATE.documentosCargados}/${STATE.totalDocumentos}`);
    }
    
    function updateUploadProgress() {
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('uploadProgress');
        const status = document.getElementById('uploadStatus');
        
        if (!progressContainer || !progressBar || !status) return;
        
        const percentage = STATE.totalDocumentos > 0 
            ? (STATE.documentosCargados / STATE.totalDocumentos) * 100 
            : 0;
        
        console.log(`Actualizando progreso: ${percentage}% (${STATE.documentosCargados}/${STATE.totalDocumentos})`);
        
        if (STATE.documentosCargados > 0) {
            progressContainer.style.display = 'block';
            progressContainer.classList.add('visible');
        } else {
            progressContainer.style.display = 'none';
        }
        
        progressBar.style.width = `${percentage}%`;
        
        const percentageElement = document.getElementById('progressPercentage');
        if (percentageElement) {
            percentageElement.textContent = `${Math.round(percentage)}%`;
        }
        
        status.textContent = `${STATE.documentosCargados} de ${STATE.totalDocumentos} documentos cargados`;
        
        if (STATE.documentosCargados === STATE.totalDocumentos) {
            progressBar.classList.add('progress-complete');
            status.innerHTML = '<strong>¡Todos los documentos cargados!</strong>';
        } else {
            progressBar.classList.remove('progress-complete');
        }
    }
    
    function removeDocument(fileName) {
        const card = Array.from(document.querySelectorAll('.doc-card')).find(card => {
            return card.querySelector('.doc-title').textContent === fileName;
        });
        
        if (card && card.classList.contains('flipped')) {
            card.classList.remove('flipped');
            STATE.documentosCargados = Math.max(0, STATE.documentosCargados - 1);
            STATE.documentos.delete(fileName);
            updateUploadProgress();
            
            const input = card.querySelector('input[type="file"]');
            if (input) input.value = '';
        }
    }
    
    function previewImage(file, card) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const icon = card.querySelector('.doc-icon');
            if (icon) {
                const originalHTML = icon.innerHTML;
                icon.innerHTML = `<img src="${e.target.result}" 
                    style="width:40px;height:40px;object-fit:cover;border-radius:8px;" 
                    alt="Vista previa">`;
                
                card.querySelector('input[type="file"]').addEventListener('click', () => {
                    icon.innerHTML = originalHTML;
                }, { once: true });
            }
        };
        reader.readAsDataURL(file);
    }
    
    function initDragAndDrop() {
        document.querySelectorAll('.doc-front').forEach(dropZone => {
            dropZone.addEventListener('dragover', handleDragOver);
            dropZone.addEventListener('dragleave', handleDragLeave);
            dropZone.addEventListener('drop', handleDrop);
        });
    }
    
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.style.borderColor = 'var(--accent)';
        e.currentTarget.style.backgroundColor = 'rgba(255, 217, 57, 0.1)';
    }
    
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.style.borderColor = '';
        e.currentTarget.style.backgroundColor = '';
    }
    
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const dropZone = e.currentTarget;
        dropZone.style.borderColor = '';
        dropZone.style.backgroundColor = '';
        
        const input = dropZone.querySelector('input[type="file"]');
        const files = e.dataTransfer.files;
        
        if (files.length > 0) {
            input.files = files;
            const event = new Event('change');
            input.dispatchEvent(event);
        }
    }
    
    // =========================
    // MANEJADOR DE CORREO
    // =========================
    function initEmailManager() {
        if (!DOM.nombreInput || !DOM.apellidoInput) return;
        
        let timeout;
        
        function handleInput() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const nombre = DOM.nombreInput.value.trim();
                const apellido = DOM.apellidoInput.value.trim();
                
                if (nombre && apellido && !STATE.correoConfirmado) {
                    generateEmail(nombre, apellido);
                } else if (!nombre || !apellido) {
                    DOM.correoInput.value = '';
                }
            }, 500);
        }
        
        DOM.nombreInput.addEventListener('input', handleInput);
        DOM.apellidoInput.addEventListener('input', handleInput);
        
        if (DOM.btnConfirmarCorreo) {
            DOM.btnConfirmarCorreo.addEventListener('click', requestEmailConfirmation);
        }
        
        if (DOM.correoSi && DOM.correoNo) {
            DOM.correoSi.addEventListener('click', () => confirmEmail(true));
            DOM.correoNo.addEventListener('click', () => confirmEmail(false));
        }
    }
    
    function generateEmail(nombre, apellido) {
        if (STATE.correoConfirmado) return;
        
        const nombreFormateado = nombre.split(' ')[0]
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/ñ/g, 'n')
            .replace(/Ñ/g, 'N')
            .replace(/[^a-z]/g, '');
        
        const apellidoFormateado = apellido.split(' ')[0]
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/ñ/g, 'n')
            .replace(/Ñ/g, 'N')
            .replace(/[^a-z]/g, '');
        
        if (!nombreFormateado || !apellidoFormateado) {
            DOM.correoInput.value = '';
            return;
        }
        
        const email = `${nombreFormateado}.${apellidoFormateado}${CONFIG.dominioCorreo}`;
        DOM.correoInput.value = email.toLowerCase();
        
        if (DOM.btnConfirmarCorreo) {
            DOM.btnConfirmarCorreo.classList.remove('d-none');
            DOM.btnConfirmarCorreo.classList.add('pulse');
        }
        
        clearTimeout(STATE.timerCorreo);
        STATE.timerCorreo = setTimeout(() => {
            if (!STATE.correoConfirmado && !STATE.modalMostrado && DOM.correoInput.value && !STATE.usuarioRegistrado) {
                requestEmailConfirmation();
            }
        }, 5000);
    }
    
    function requestEmailConfirmation() {
        if (STATE.correoConfirmado || STATE.modalMostrado || !DOM.correoInput.value.trim() || STATE.usuarioRegistrado) {
            return;
        }
        
        const email = DOM.correoInput.value.trim();
        
        if (!VALIDATION.email.test(email)) {
            showToast('Error', 'Formato de correo inválido', 'danger');
            return;
        }
        
        verificarUsuarioRegistrado().then(estaRegistrado => {
            if (estaRegistrado) {
                return;
            }
            
            if (DOM.correoConfirmacion) {
                DOM.correoConfirmacion.textContent = email;
            }
            
            STATE.modalMostrado = true;
            if (MODALS.correo) {
                MODALS.correo.show();
            }
        });
    }
    
    function confirmEmail(confirmed) {
        STATE.correoConfirmado = confirmed;
        STATE.modalMostrado = false;
        
        if (confirmed) {
            DOM.correoInput.readOnly = true;
            DOM.correoInput.classList.add('is-valid');
            DOM.correoInput.classList.remove('is-invalid');
            
            if (DOM.estadoCorreo) {
                DOM.estadoCorreo.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Correo confirmado';
                DOM.estadoCorreo.className = 'text-success fw-semibold mt-1';
            }
            
            if (DOM.btnConfirmarCorreo) {
                DOM.btnConfirmarCorreo.classList.add('d-none');
                DOM.btnConfirmarCorreo.classList.remove('pulse');
            }
            
            unlockForm();
            
            showToast('✅ Correo confirmado', 'Correo institucional confirmado correctamente', 'success');
        } else {
            DOM.correoInput.readOnly = false;
            DOM.correoInput.focus();
            DOM.correoInput.select();
            DOM.correoInput.classList.remove('is-valid');
            
            if (DOM.estadoCorreo) {
                DOM.estadoCorreo.innerHTML = '<i class="bi bi-clock-history me-1"></i>Pendiente de confirmación';
                DOM.estadoCorreo.className = 'text-warning fw-semibold mt-1';
            }
            
            if (DOM.btnConfirmarCorreo) {
                DOM.btnConfirmarCorreo.classList.remove('d-none');
            }
        }
        
        if (MODALS.correo) {
            MODALS.correo.hide();
        }
    }
    
    // =========================
    // VERIFICACIÓN DE USUARIO REGISTRADO
    // =========================
    async function verificarUsuarioRegistrado() {
        const nombre = DOM.nombreInput ? DOM.nombreInput.value.trim() : '';
        const apellido = DOM.apellidoInput ? DOM.apellidoInput.value.trim() : '';
        const rfc = DOM.rfcInput ? DOM.rfcInput.value.trim() : '';
        const curp = document.querySelector('input[name="curp"]') ? document.querySelector('input[name="curp"]').value.trim() : '';
        const nss = document.querySelector('input[name="nss"]') ? document.querySelector('input[name="nss"]').value.trim() : '';
        
        if (!nombre && !apellido && !rfc && !curp && !nss) {
            return false;
        }
        
        try {
            if (DOM.correoInput) {
                DOM.correoInput.classList.add('is-validating');
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const usuarioYaRegistrado = Math.random() > 0.5;
            
            if (usuarioYaRegistrado) {
                STATE.usuarioRegistrado = true;
                
                let campoDuplicado = '';
                let valorDuplicado = '';
                
                if (rfc && Math.random() > 0.5) {
                    campoDuplicado = 'rfc';
                    valorDuplicado = rfc;
                } else if (curp && Math.random() > 0.5) {
                    campoDuplicado = 'curp';
                    valorDuplicado = curp;
                } else if (nss && Math.random() > 0.5) {
                    campoDuplicado = 'nss';
                    valorDuplicado = nss;
                } else {
                    campoDuplicado = 'nombre';
                    valorDuplicado = `${nombre} ${apellido}`;
                }
                
                mostrarModalUsuarioRegistrado(campoDuplicado, valorDuplicado);
                return true;
            }
            
            STATE.usuarioRegistrado = false;
            return false;
            
        } catch (error) {
            console.error('Error verificando usuario registrado:', error);
            return false;
        } finally {
            if (DOM.correoInput) {
                DOM.correoInput.classList.remove('is-validating');
            }
        }
    }
    
    // =========================
    // MODAL DE USUARIO REGISTRADO
    // =========================
    function mostrarModalUsuarioRegistrado(campo, valor) {
        let modalElement = document.getElementById('modalUsuarioRegistrado');
        
        if (!modalElement) {
            modalElement = document.createElement('div');
            modalElement.id = 'modalUsuarioRegistrado';
            modalElement.className = 'modal fade modal-duplicate';
            modalElement.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
                                Usuario Ya Registrado
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="text-center mb-4">
                                <i class="bi bi-person-x-fill text-danger" style="font-size: 3rem;"></i>
                            </div>
                            <p class="text-center mb-3">
                                <strong>El colaborador ya se encuentra registrado en el sistema.</strong>
                            </p>
                            <div class="duplicate-details">
                                <p class="mb-2"><strong>Campo duplicado:</strong> <span id="duplicateField"></span></p>
                                <p class="mb-0"><strong>Valor:</strong> <code id="duplicateValue"></code></p>
                            </div>
                            <div class="alert alert-warning mt-3">
                                <i class="bi bi-info-circle me-2"></i>
                                <strong>Importante:</strong> Puedes corregir los datos en los campos correspondientes.
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-arrow-left me-1"></i>Entendido
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modalElement);
        }
        
        const fieldNames = {
            'nombre': 'Nombre Completo',
            'correo': 'Correo Electrónico',
            'rfc': 'RFC',
            'curp': 'CURP',
            'nss': 'Número de Seguro Social'
        };
        
        document.getElementById('duplicateField').textContent = fieldNames[campo] || campo;
        document.getElementById('duplicateValue').textContent = valor;
        
        STATE.modalUsuarioRegistrado = new bootstrap.Modal(modalElement);
        STATE.modalUsuarioRegistrado.show();
        
        modalElement.addEventListener('hidden.bs.modal', function() {
            const input = document.querySelector(`input[name="${campo}"]`);
            if (input) {
                input.focus();
                input.select();
            }
            
            STATE.usuarioRegistrado = false;
        }, { once: true });
    }
    
    // =========================
    // VERIFICACIÓN DE DUPLICADOS
    // =========================
    function initDuplicateChecker() {
        const campos = [
            { selector: 'input[name="correo"]', key: 'correo', nombre: 'Correo', icono: '📧' },
            { selector: 'input[name="rfc"]', key: 'rfc', nombre: 'RFC', icono: '🆔' },
            { selector: 'input[name="curp"]', key: 'curp', nombre: 'CURP', icono: '📄' },
            { selector: 'input[name="nss"]', key: 'nss', nombre: 'NSS', icono: '🏥' }
        ];
        
        campos.forEach(campo => {
            const input = document.querySelector(campo.selector);
            if (input) {
                let timeout;
                
                input.addEventListener('blur', function() {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        const valor = this.value.trim();
                        if (valor) {
                            verificarCampoDuplicadoMejorado(campo, valor);
                        }
                    }, 800);
                });
                
                input.addEventListener('input', function() {
                    clearTimeout(timeout);
                    
                    const feedbackExistente = this.nextElementSibling;
                    if (feedbackExistente && feedbackExistente.classList.contains('duplicate-feedback')) {
                        feedbackExistente.remove();
                    }
                    
                    this.classList.remove('is-duplicate', 'is-invalid');
                    STATE.camposDuplicados[campo.key] = false;
                    
                    STATE.usuarioRegistrado = false;
                });
            }
        });
    }
    
    async function verificarCampoDuplicadoMejorado(campo, valor) {
        if (!valor.trim()) return false;
        
        const input = document.querySelector(campo.selector);
        if (!input) return false;
        
        const feedbackExistente = input.nextElementSibling;
        if (feedbackExistente && feedbackExistente.classList.contains('duplicate-feedback')) {
            feedbackExistente.remove();
        }
        
        input.classList.add('is-validating');
        
        if (STATE.verificacionesPendientes.has(campo.key)) {
            return false;
        }
        
        STATE.verificacionesPendientes.add(campo.key);
        
        try {
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const esDuplicado = Math.random() > 0.7;
            
            input.classList.remove('is-validating');
            
            if (esDuplicado) {
                mostrarModalUsuarioRegistrado(campo.key, valor);
                input.classList.add('is-duplicate', 'is-invalid');
                STATE.camposDuplicados[campo.key] = true;
                return true;
            } else {
                input.classList.add('is-valid');
                input.classList.remove('is-invalid');
                STATE.camposDuplicados[campo.key] = false;
                return false;
            }
        } catch (error) {
            console.error('Error verificando duplicado:', error);
            input.classList.remove('is-validating');
            return false;
        } finally {
            STATE.verificacionesPendientes.delete(campo.key);
        }
    }
    
    // =========================
    // FUNCIONES DE VALIDACIÓN BÁSICA
    // =========================
    function initValidations() {
        const curpInput = document.querySelector('input[name="curp"]');
        if (curpInput) {
            curpInput.addEventListener('blur', validateCURP);
        }
        
        if (DOM.correoInput) {
            DOM.correoInput.addEventListener('blur', validateEmail);
        }
        
        const phoneInput = document.querySelector('input[name="telefono"]');
        if (phoneInput) {
            phoneInput.addEventListener('input', formatPhone);
        }
        
        const accountInput = document.getElementById('numero_cuenta');
        if (accountInput) {
            accountInput.addEventListener('input', formatAccountNumber);
        }
    }
    
    function validateCURP(e) {
        const value = e.target.value.trim().toUpperCase();
        if (!value) return;
        
        const isValid = VALIDATION.curp.test(value);
        updateFieldStatus(e.target, isValid, 'CURP inválido');
    }
    
    function validateEmail(e) {
        const value = e.target.value.trim();
        if (!value) return;
        
        const isValid = VALIDATION.email.test(value);
        updateFieldStatus(e.target, isValid, 'Correo inválido (debe ser @marnezdesarrollos.com)');
    }
    
    function updateFieldStatus(field, isValid, errorMessage) {
        field.classList.toggle('is-valid', isValid);
        field.classList.toggle('is-invalid', !isValid);
        
        if (!isValid && errorMessage) {
            let feedback = field.nextElementSibling;
            if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                field.parentNode.insertBefore(feedback, field.nextSibling);
            }
            feedback.textContent = errorMessage;
        }
    }
    
    function formatPhone(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 10) {
            value = value.substring(0, 10);
        }
        e.target.value = value;
    }
    
    function formatAccountNumber(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 18) {
            value = value.substring(0, 18);
        }
        e.target.value = value;
    }
    
    // =========================
    // MANEJADOR DE ÁREAS
    // =========================
    function initAreaManager() {
        if (!DOM.areaSelect) return;
        
        DOM.areaSelect.addEventListener('change', handleAreaChange);
        
        if (DOM.areaSelect.value) {
            handleAreaChange();
        }
    }
    
    async function handleAreaChange() {
        const areaId = DOM.areaSelect.value;
        if (!areaId) return;
        
        STATE.areaSeleccionada = areaId;
        STATE.esComercial = parseInt(areaId) === CONFIG.AREA_COMERCIAL_ID;
        
        if (DOM.areaHidden) {
            DOM.areaHidden.value = areaId;
        }
        
        showForm();
        configurePuestos();
        await loadPuestos(areaId);
    }
    
    function showForm() {
        if (DOM.formulario) {
            DOM.formulario.classList.remove('d-none');
            setTimeout(() => {
                DOM.formulario.classList.add('js-ready');
            }, 10);
        }
    }
    
    function configurePuestos() {
        if (!DOM.puestoSelect || !DOM.puestoComercialSelect) return;
        
        DOM.puestoSelect.classList.toggle('d-none', STATE.esComercial);
        DOM.puestoComercialSelect.classList.toggle('d-none', !STATE.esComercial);
        DOM.puestoSelect.required = !STATE.esComercial;
        DOM.puestoComercialSelect.required = STATE.esComercial;
        
        const labelSueldo = document.getElementById('labelSueldo');
        if (labelSueldo) {
            labelSueldo.textContent = STATE.esComercial ? 'Comisión base' : 'Sueldo';
        }
        
        const labelPuesto = document.getElementById('labelPuesto');
        if (labelPuesto) {
            labelPuesto.textContent = STATE.esComercial ? 'Rol comercial *' : 'Puesto *';
        }
    }
    
    async function loadPuestos(areaId) {
        if (!DOM.puestoSelect || STATE.esComercial) return;
        
        try {
            DOM.puestoSelect.disabled = true;
            DOM.puestoSelect.innerHTML = '<option value="">Cargando puestos...</option>';
            
            await new Promise(resolve => setTimeout(resolve, 500));
            
            DOM.puestoSelect.innerHTML = '<option value="">Seleccione un puesto</option>';
            
            const puestos = [
                { id: 1, nombre: 'Gerente' },
                { id: 2, nombre: 'Supervisor' },
                { id: 3, nombre: 'Coordinador' },
                { id: 4, nombre: 'Analista' },
                { id: 5, nombre: 'Asistente' }
            ];
            
            puestos.forEach(puesto => {
                const option = document.createElement('option');
                option.value = puesto.id;
                option.textContent = puesto.nombre;
                DOM.puestoSelect.appendChild(option);
            });
            
            DOM.puestoSelect.disabled = false;
        } catch (error) {
            console.error('Error cargando puestos:', error);
            DOM.puestoSelect.innerHTML = '<option value="">Error al cargar</option>';
            showToast('Error', 'No se pudieron cargar los puestos', 'danger');
        }
    }
    
    // =========================
    // ENVÍO DE FORMULARIO
    // =========================
    function initFormSubmitter() {
        if (!DOM.formulario) return;
        
        DOM.formulario.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!validateForm()) {
                scrollToFirstError();
                return;
            }
            
            if (!STATE.correoConfirmado) {
                showToast('Atención', 'Debes confirmar el correo antes de enviar', 'warning');
                requestEmailConfirmation();
                return;
            }
            
            const hayDuplicados = Object.values(STATE.camposDuplicados).some(v => v === true);
            if (hayDuplicados) {
                showToast('Error', 'Hay campos duplicados. Por favor corrija antes de enviar.', 'danger');
                scrollToFirstDuplicate();
                return;
            }
            
            if (STATE.documentosCargados === 0) {
                const confirmed = confirm('No has cargado ningún documento. ¿Deseas continuar de todas formas?');
                if (!confirmed) return;
            }
            
            await submitForm();
        });
    }
    
    function validateForm() {
        let isValid = true;
        const requiredFields = DOM.formulario.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim() && !field.disabled && field.type !== 'file') {
                field.classList.add('is-invalid');
                isValid = false;
                
                let feedback = field.nextElementSibling;
                if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                    feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Este campo es obligatorio';
                    field.parentNode.insertBefore(feedback, field.nextSibling);
                }
            } else if (field.value.trim()) {
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
            }
        });
        
        return isValid;
    }
    
    function scrollToFirstError() {
        const firstError = document.querySelector('.is-invalid');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
            showToast('Error', 'Por favor completa todos los campos requeridos', 'danger');
        }
    }
    
    function scrollToFirstDuplicate() {
        const firstDuplicate = document.querySelector('.is-duplicate');
        if (firstDuplicate) {
            firstDuplicate.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstDuplicate.focus();
        }
    }
    
    async function submitForm() {
        const submitBtn = DOM.formulario.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Guardando...';
        submitBtn.disabled = true;
        
        try {
            // Crear FormData
            const formData = new FormData(DOM.formulario);
            
            // Agregar documentos
            STATE.documentos.forEach((file, docName) => {
                formData.append('documentos_nombres[]', docName);
                formData.append('documentos_archivos[]', file);
            });
            
            // Simular envío
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // En producción, descomentar esto:
            /*
            const response = await fetch('/api/alta-colaborador', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Error en el servidor');
            }
            */
            
            showToast('✅ Éxito', 'Colaborador guardado correctamente', 'success');
            
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
            
        } catch (error) {
            console.error('Error:', error);
            showToast('❌ Error', 'Error al guardar el colaborador', 'danger');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
    
    // =========================
    // TOGGLES DE SECCIONES
    // =========================
    function initSectionToggles() {
        document.querySelectorAll('.section-toggle').forEach(toggle => {
            toggle.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const target = document.getElementById(targetId);
                const icon = this.querySelector('.toggle-icon');
                
                this.classList.toggle('collapsed');
                target.classList.toggle('collapsed');
                
                if (icon) {
                    icon.style.transform = target.classList.contains('collapsed') 
                        ? 'rotate(-90deg)' 
                        : 'rotate(0deg)';
                }
                
                localStorage.setItem(`section_${targetId}`, target.classList.contains('collapsed'));
            });
            
            const targetId = toggle.getAttribute('data-target');
            const target = document.getElementById(targetId);
            const isCollapsed = localStorage.getItem(`section_${targetId}`) === 'true';
            
            if (isCollapsed && target) {
                toggle.classList.add('collapsed');
                target.classList.add('collapsed');
                const icon = toggle.querySelector('.toggle-icon');
                if (icon) {
                    icon.style.transform = 'rotate(-90deg)';
                }
            }
        });
    }
    
    // =========================
    // CONTADOR DE CARACTERES
    // =========================
    function initCharacterCounter() {
        const textarea = document.querySelector('textarea[name="comentarios"]');
        const charCount = document.getElementById('charCount');
        
        if (textarea && charCount) {
            textarea.addEventListener('input', function() {
                const length = this.value.length;
                charCount.textContent = length;
                
                if (length > 450) {
                    charCount.style.color = 'var(--danger)';
                    charCount.style.fontWeight = 'bold';
                } else if (length > 400) {
                    charCount.style.color = 'var(--warning)';
                    charCount.style.fontWeight = 'bold';
                } else {
                    charCount.style.color = '';
                    charCount.style.fontWeight = '';
                }
            });
            
            charCount.textContent = textarea.value.length;
        }
    }
    
    // =========================
    // MEJORAS DE FORMULARIO
    // =========================
    function initFormEnhancements() {
        setTimeout(() => {
            if (DOM.nombreInput) {
                DOM.nombreInput.focus();
            }
        }, 300);
        
        document.querySelectorAll('[required]').forEach(field => {
            field.addEventListener('blur', function() {
                if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
        
        const fechaInput = document.querySelector('input[name="fecha_alta"]');
        if (fechaInput && CONFIG.today) {
            fechaInput.max = CONFIG.today;
            fechaInput.value = CONFIG.today;
        }
    }
    
    // =========================
    // BLOQUEO/DESBLOQUEO DE FORMULARIO
    // =========================
    function lockForm() {
        if (!DOM.formulario) return;
        
        DOM.formulario.dataset.bloqueado = "true";
        const elements = DOM.formulario.querySelectorAll("input, select, textarea, button");
        
        elements.forEach(el => {
            const id = el.id;
            if (!["nombre", "apellido", "correo", "btnConfirmarCorreo"].includes(id)) {
                el.disabled = true;
            }
        });
    }
    
    function unlockForm() {
        if (!DOM.formulario) return;
        
        DOM.formulario.dataset.bloqueado = "false";
        const elements = DOM.formulario.querySelectorAll("input, select, textarea, button");
        
        elements.forEach(el => {
            el.disabled = false;
        });
        
        if (DOM.correoInput && STATE.correoConfirmado) {
            DOM.correoInput.readOnly = true;
        }
    }
    
    // =========================
    // BOTONES ESPECIALES
    // =========================
    function initBotonesEspeciales() {
        const btnBaja = document.getElementById('btnBajaColaborador');
        if (btnBaja) {
            btnBaja.addEventListener('click', function(e) {
                e.preventDefault();
                mostrarModalBaja();
            });
        }
        
        const btnCambioArea = document.getElementById('btnCambioArea');
        if (btnCambioArea) {
            btnCambioArea.addEventListener('click', function(e) {
                e.preventDefault();
                mostrarModalCambioArea();
            });
        }
        
        // Añadir botón colaborador si no existe
        if (!document.getElementById('btnColaborador')) {
            const btnColaborador = document.createElement('button');
            btnColaborador.id = 'btnColaborador';
            btnColaborador.className = 'btn btn-info';
            btnColaborador.innerHTML = '<i class="bi bi-person-check me-1"></i>Verificar Colaborador';
            
            const areaGroup = DOM.areaSelect?.parentNode;
            if (areaGroup) {
                areaGroup.parentNode.insertBefore(btnColaborador, areaGroup.nextSibling);
            }
        }
    }
    
    function mostrarModalBaja() {
        showToast('Funcionalidad', 'Módulo de baja de colaboradores - En desarrollo', 'info');
    }
    
    function mostrarModalCambioArea() {
        showToast('Funcionalidad', 'Módulo de cambio de área - En desarrollo', 'info');
    }
    
    // =========================
    // FUNCIÓN DE TOAST - MEJORADA
    // =========================
    function showToast(title, message, type = 'info') {
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
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
        
        toast.className = `toast ${typeClasses[type] || 'bg-info text-white'}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header ${type === 'warning' ? 'bg-warning' : ''}">
                <i class="bi bi-${icons[type] || 'info-circle'} me-2"></i>
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close ${type === 'warning' ? '' : 'btn-close-white'}" 
                        data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, { 
            delay: 5000,
            autohide: true
        });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    // =========================
    // INICIALIZACIÓN
    // =========================
    function init() {
        console.log('Inicializando módulo de alta de colaboradores V2.3...');
        
        initComponents();
        lockForm();
        
        console.log('Módulo de alta V2.3 inicializado correctamente');
    }
    
    // =========================
    // EJECUCIÓN
    // =========================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // =========================
    // FUNCIONES GLOBALES
    // =========================
    window.documentoCargado = function(input) {
        const event = new Event('change');
        input.dispatchEvent(event);
    };
    
    window.toggleCredito = function(tipo) {
        const input = document.getElementById(tipo + "_credito");
        if (!input) return;
        
        const select = event?.target || document.querySelector(`select[name="${tipo}"]`);
        const tieneCredito = select.value === "Sí";
        
        input.classList.toggle("d-none", !tieneCredito);
        input.required = tieneCredito;
        
        if (!tieneCredito) input.value = "";
    };
})();