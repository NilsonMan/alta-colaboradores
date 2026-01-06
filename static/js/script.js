function seleccionarArea() {
    const areaSelect = document.getElementById("area");
    const areaId = areaSelect.value;
    const areaTexto = areaSelect.options[areaSelect.selectedIndex].text.toLowerCase();

    const formulario = document.getElementById("formulario");
    const bloqueComercial = document.getElementById("bloqueComercial");

    if (!areaId) {
        formulario.classList.add("d-none");
        return;
    }

    formulario.classList.remove("d-none");

    // Mostrar / ocultar bloque comercial
    if (areaTexto.includes("comercial")) {
        bloqueComercial.classList.remove("d-none");
    } else {
        bloqueComercial.classList.add("d-none");
    }

    cargarPuestos(areaId);
}

function cargarPuestos(areaId) {
    const puesto = document.getElementById("puesto");
    puesto.innerHTML = '<option value="">Cargando...</option>';

    fetch(`/puestos/${areaId}`)
        .then(res => res.json())
        .then(data => {
            puesto.innerHTML = '<option value="">Selecciona un puesto</option>';
            data.forEach(p => {
                const opt = document.createElement("option");
                opt.value = p.id;
                opt.textContent = p.nombre;
                puesto.appendChild(opt);
            });
        });
}
