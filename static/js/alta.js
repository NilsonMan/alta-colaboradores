// ============================================
// MÓDULO PRINCIPAL - ALTA COLABORADOR V2.1
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
        correoConfirmacion: document.getElementById('correoConfirmacion')
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
        totalDocumentos: 9, // Documentos fijos
        camposDuplicados: {
            correo: false,
            rfc: false,
            curp: false,
            nss: false
        },
        verificacionesPendientes: new Set(),
        documentos: new Map() // Para almacenar documentos cargados
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
        cambioArea: null
    };
    
    // =========================
    // INICIALIZACIÓN DE COMPONENTES
    // =========================
    function initComponents() {
        console.log('Inicializando módulo de alta V2.1...');
        
        // Inicializar todos los componentes
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
        
        // Inicializar contador de documentos
        updateDocumentCounter();
        
        console.log('Módulo de alta V2.1 inicializado correctamente');
    }
    
    // =========================
    // MANEJADOR DE DOCUMENTOS - COMPLETAMENTE CORREGIDO
    // =========================
    function initDocumentManager() {
        console.log('Inicializando gestor de documentos...');
        
        // Inicializar eventos de carga de archivos
        document.querySelectorAll('.doc-card input[type="file"]').forEach(input => {
            input.addEventListener('change', handleFileUpload);
        });
        
        // Inicializar drag and drop
        initDragAndDrop();
        
        // Mostrar progreso inicial
        updateUploadProgress();
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
        
        // Validar tamaño
        if (file.size > maxSize) {
            showToast('Error', `El archivo excede el tamaño máximo de ${maxSize / 1024 / 1024}MB`, 'danger');
            input.value = '';
            removeDocument(fileName);
            return;
        }
        
        // Validar tipo
        if (!file.type.match(/(pdf|image\/jpeg|image\/jpg|image\/png)/)) {
            showToast('Error', 'Solo se permiten archivos PDF, JPG o PNG', 'danger');
            input.value = '';
            removeDocument(fileName);
            return;
        }
        
        // Verificar si es un documento nuevo (no reemplazo)
        if (!card.classList.contains('uploaded')) {
            STATE.documentosCargados++;
        }
        
        // Almacenar documento
        STATE.documentos.set(fileName, file);
        
        // Actualizar UI
        updateDocumentCard(card, true);
        updateUploadProgress();
        
        // Mostrar preview si es imagen
        if (file.type.startsWith('image/')) {
            previewImage(file, card);
        }
        
        console.log(`Documento cargado: ${fileName} (${STATE.documentosCargados}/${STATE.totalDocumentos})`);
        showToast('✅ Documento cargado', `${fileName} cargado correctamente`, 'success');
    }
    
    function updateDocumentCard(card, uploaded) {
        if (uploaded) {
            card.classList.add('uploaded');
        } else {
            card.classList.remove('uploaded');
        }
    }
    
    function updateDocumentCounter() {
        STATE.documentosCargados = document.querySelectorAll('.doc-card.uploaded').length;
        console.log(`Documentos cargados: ${STATE.documentosCargados}/${STATE.totalDocumentos}`);
    }
    
    function updateUploadProgress() {
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('uploadProgress');
        const status = document.getElementById('uploadStatus');
        
        if (!progressContainer || !progressBar || !status) {
            console.error('Elementos de progreso no encontrados');
            return;
        }
        
        const percentage = STATE.totalDocumentos > 0 
            ? (STATE.documentosCargados / STATE.totalDocumentos) * 100 
            : 0;
        
        console.log(`Actualizando progreso: ${percentage}% (${STATE.documentosCargados}/${STATE.totalDocumentos})`);
        
        // Mostrar/ocultar contenedor
        if (STATE.documentosCargados > 0) {
            progressContainer.style.display = 'block';
            progressContainer.classList.add('visible');
        } else {
            progressContainer.style.display = 'none';
        }
        
        // Actualizar barra
        progressBar.style.width = `${percentage}%`;
        progressBar.textContent = `${Math.round(percentage)}%`;
        
        // Actualizar texto
        status.textContent = `${STATE.documentosCargados} de ${STATE.totalDocumentos} documentos cargados`;
        
        // Cambiar color según progreso
        if (STATE.documentosCargados === STATE.totalDocumentos) {
            progressBar.classList.remove('bg-info');
            progressBar.classList.add('bg-success');
            progressBar.textContent = '¡Completado!';
        } else if (STATE.documentosCargados > 0) {
            progressBar.classList.remove('bg-success');
            progressBar.classList.add('bg-info');
        }
    }
    
    function removeDocument(fileName) {
        const card = Array.from(document.querySelectorAll('.doc-card')).find(card => {
            return card.querySelector('.doc-title').textContent === fileName;
        });
        
        if (card && card.classList.contains('uploaded')) {
            card.classList.remove('uploaded');
            STATE.documentosCargados = Math.max(0, STATE.documentosCargados - 1);
            STATE.documentos.delete(fileName);
            updateUploadProgress();
            
            // Resetear input file
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
                
                // Restaurar icono original al hacer clic
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
    // MANEJADOR DE CORREO - CORREGIDO (sin undefined)
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
        
        // Limpiar y formatear nombres
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
        
        // Validar que no estén vacíos
        if (!nombreFormateado || !apellidoFormateado) {
            DOM.correoInput.value = '';
            return;
        }
        
        const email = `${nombreFormateado}.${apellidoFormateado}${CONFIG.dominioCorreo}`;
        DOM.correoInput.value = email.toLowerCase();
        
        // Mostrar botón de confirmación
        if (DOM.btnConfirmarCorreo) {
            DOM.btnConfirmarCorreo.classList.remove('d-none');
            DOM.btnConfirmarCorreo.classList.add('pulse');
        }
        
        // Auto-confirmación después de 5 segundos
        clearTimeout(STATE.timerCorreo);
        STATE.timerCorreo = setTimeout(() => {
            if (!STATE.correoConfirmado && !STATE.modalMostrado && DOM.correoInput.value) {
                requestEmailConfirmation();
            }
        }, 5000);
    }
    
    function requestEmailConfirmation() {
        if (STATE.correoConfirmado || STATE.modalMostrado || !DOM.correoInput.value.trim()) {
            return;
        }
        
        const email = DOM.correoInput.value.trim();
        
        // Verificar formato básico
        if (!VALIDATION.email.test(email)) {
            showToast('Error', 'Formato de correo inválido', 'danger');
            return;
        }
        
        // Verificar duplicado antes de mostrar modal
        verificarCampoDuplicadoMejorado(
            { selector: 'input[name="correo"]', key: 'correo', nombre: 'Correo', icono: '📧' },
            email
        ).then(esDuplicado => {
            if (esDuplicado) {
                showToast('Correo duplicado', 'Por favor ingrese un correo diferente', 'warning');
                return;
            }
            
            // Mostrar correo en modal
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
            // Bloquear correo
            DOM.correoInput.readOnly = true;
            DOM.correoInput.classList.add('is-valid');
            DOM.correoInput.classList.remove('is-invalid');
            
            // Actualizar estado
            if (DOM.estadoCorreo) {
                DOM.estadoCorreo.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Correo confirmado';
                DOM.estadoCorreo.className = 'text-success fw-semibold mt-1';
            }
            
            // Ocultar botón de confirmación
            if (DOM.btnConfirmarCorreo) {
                DOM.btnConfirmarCorreo.classList.add('d-none');
                DOM.btnConfirmarCorreo.classList.remove('pulse');
            }
            
            // Desbloquear formulario
            unlockForm();
            
            showToast('✅ Correo confirmado', 'Correo institucional confirmado correctamente', 'success');
        } else {
            // Permitir corrección
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
    // VERIFICACIÓN DE DUPLICADOS - CORREGIDA
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
                    
                    // Limpiar feedback anterior
                    const feedbackExistente = this.nextElementSibling;
                    if (feedbackExistente && feedbackExistente.classList.contains('duplicate-feedback')) {
                        feedbackExistente.remove();
                    }
                    
                    // Limpiar clases de error
                    this.classList.remove('is-duplicate', 'is-invalid');
                    STATE.camposDuplicados[campo.key] = false;
                });
            }
        });
    }
    
    async function verificarCampoDuplicadoMejorado(campo, valor) {
        if (!valor.trim()) return false;
        
        const input = document.querySelector(campo.selector);
        if (!input) return false;
        
        // Limpiar feedback anterior
        const feedbackExistente = input.nextElementSibling;
        if (feedbackExistente && feedbackExistente.classList.contains('duplicate-feedback')) {
            feedbackExistente.remove();
        }
        
        // Mostrar estado de verificación
        input.classList.add('is-validating');
        
        // Evitar verificaciones simultáneas
        if (STATE.verificacionesPendientes.has(campo.key)) {
            return false;
        }
        
        STATE.verificacionesPendientes.add(campo.key);
        
        try {
            // Simular verificación (en producción aquí iría la llamada a la API)
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const esDuplicado = Math.random() > 0.7; // Simulación
            
            input.classList.remove('is-validating');
            
            if (esDuplicado) {
                mostrarErrorDuplicadoMejorado(campo, valor, input);
                STATE.camposDuplicados[campo.key] = true;
                return true;
            } else {
                // Marcar como válido
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
    
    function mostrarErrorDuplicadoMejorado(campo, valor, input) {
        // Crear elemento de feedback
        const feedback = document.createElement('div');
        feedback.className = 'duplicate-feedback mt-2';
        feedback.innerHTML = `
            <div class="alert alert-warning py-2 mb-0" role="alert">
                <div class="d-flex align-items-center">
                    <i class="bi bi-exclamation-triangle-fill fs-5 me-2"></i>
                    <div class="flex-grow-1">
                        <div class="fw-bold">${campo.icono} ${campo.nombre} duplicado</div>
                        <div class="small">El valor "<strong>${valor}</strong>" ya existe en el sistema.</div>
                        <div class="small mt-1">
                            <button type="button" class="btn btn-sm btn-outline-secondary btn-limpiar">
                                <i class="bi bi-x-circle me-1"></i>Limpiar campo
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insertar después del input
        input.parentNode.insertBefore(feedback, input.nextSibling);
        
        // Aplicar clases de error
        input.classList.add('is-duplicate', 'is-invalid');
        input.classList.remove('is-valid');
        
        // Enfocar el campo
        input.focus();
        
        // Agregar evento al botón de limpiar
        feedback.querySelector('.btn-limpiar').addEventListener('click', function() {
            input.value = '';
            input.classList.remove('is-duplicate', 'is-invalid');
            feedback.remove();
            STATE.camposDuplicados[campo.key] = false;
            input.focus();
        });
    }
    
    // =========================
    // FUNCIONES DE VALIDACIÓN BÁSICA
    // =========================
    function initValidations() {
        // CURP Validation
        const curpInput = document.querySelector('input[name="curp"]');
        if (curpInput) {
            curpInput.addEventListener('blur', validateCURP);
        }
        
        // Email Validation
        if (DOM.correoInput) {
            DOM.correoInput.addEventListener('blur', validateEmail);
        }
        
        // Phone Validation
        const phoneInput = document.querySelector('input[name="telefono"]');
        if (phoneInput) {
            phoneInput.addEventListener('input', formatPhone);
        }
        
        // Account Number Validation
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
            
            // Simular carga de puestos
            await new Promise(resolve => setTimeout(resolve, 500));
            
            DOM.puestoSelect.innerHTML = '<option value="">Seleccione un puesto</option>';
            
            // Datos de ejemplo
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
            // Simular envío
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            showToast('✅ Éxito', 'Colaborador guardado correctamente', 'success');
            
            // Redirigir después de 1.5 segundos
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
        
        // Auto-validación al perder foco
        document.querySelectorAll('[required]').forEach(field => {
            field.addEventListener('blur', function() {
                if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
        
        // Fecha actual como fecha de alta
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
        
        // El correo sigue siendo de solo lectura si está confirmado
        if (DOM.correoInput && STATE.correoConfirmado) {
            DOM.correoInput.readOnly = true;
        }
    }
    
    // =========================
    // BOTONES ESPECIALES
    // =========================
    function initBotonesEspeciales() {
        // Botón de Baja
        const btnBaja = document.getElementById('btnBajaColaborador');
        if (btnBaja) {
            btnBaja.addEventListener('click', function(e) {
                e.preventDefault();
                mostrarModalBaja();
            });
        }
        
        // Botón de Cambio de Área
        const btnCambioArea = document.getElementById('btnCambioArea');
        if (btnCambioArea) {
            btnCambioArea.addEventListener('click', function(e) {
                e.preventDefault();
                mostrarModalCambioArea();
            });
        }
    }
    
    function mostrarModalBaja() {
        showToast('Funcionalidad', 'Módulo de baja de colaboradores - En desarrollo', 'info');
    }
    
    function mostrarModalCambioArea() {
        showToast('Funcionalidad', 'Módulo de cambio de área - En desarrollo', 'info');
    }
    
    // =========================
    // FUNCIÓN DE TOAST
    // =========================
    function showToast(title, message, type = 'info') {
        // Crear contenedor si no existe
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
        console.log('Inicializando módulo de alta de colaboradores V2.1...');
        
        initComponents();
        lockForm();
        
        console.log('Módulo de alta V2.1 inicializado correctamente');
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
    
    window.previsualizarDocumento = function(btn) {
        const card = btn.closest('.doc-card');
        if (!card) return;
        
        const fileName = card.querySelector('.doc-title').textContent;
        const file = STATE.documentos.get(fileName);
        
        if (!file) {
            showToast('Error', 'No hay documento para previsualizar', 'warning');
            return;
        }
        
        const url = URL.createObjectURL(file);
        const iframe = document.getElementById('previewFrame');
        const img = document.getElementById('previewImg');
        
        // Resetear displays
        iframe.style.display = 'none';
        img.style.display = 'none';
        
        // Configurar según el tipo de archivo
        if (file.type.includes('pdf')) {
            iframe.src = url;
            iframe.style.display = 'block';
        } else if (file.type.includes('image')) {
            img.src = url;
            img.style.display = 'block';
        } else {
            showToast('Error', 'Tipo de archivo no soportado para previsualización', 'warning');
            return;
        }
        
        // Mostrar modal
        const modalElement = document.getElementById('modalPreview');
        const modal = MODALS.preview || new bootstrap.Modal(modalElement);
        MODALS.preview = modal;
        
        // Liberar URL cuando se cierre el modal
        modalElement.addEventListener('hidden.bs.modal', () => {
            URL.revokeObjectURL(url);
        }, { once: true });
        
        modal.show();
    };
    
    window.cambiarDocumento = function(btn) {
        const card = btn.closest('.doc-card');
        if (!card) return;
        
        const input = card.querySelector('input[type="file"]');
        if (!input) return;
        
        // Obtener nombre del documento
        const fileName = card.querySelector('.doc-title').textContent;
        
        // Remover del estado
        if (card.classList.contains('uploaded')) {
            STATE.documentosCargados = Math.max(0, STATE.documentosCargados - 1);
            STATE.documentos.delete(fileName);
        }
        
        // Resetear UI
        input.value = '';
        card.classList.remove('uploaded');
        
        // Actualizar progreso
        updateUploadProgress();
        
        // Efecto visual
        card.classList.add('shake');
        setTimeout(() => card.classList.remove('shake'), 400);
        
        // Abrir selector de archivos
        setTimeout(() => input.click(), 100);
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