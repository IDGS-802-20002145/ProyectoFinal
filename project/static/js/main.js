
console.log('Hello World!');

function abrirModal() {
    $('#exampleModal').modal('show');
}

//ocultame de primera instancia el div con id dashboard2 y haz que se visualize cuando se haga click en el boton con id btnDashboard2
$('#dataTable2').hide();

function mostrarTabla() {
    $('#dataTable2').show();
    $('#dashboard2').hide();
    $('#ver-detalles').hide();
}
function mostrarDashboard() {
    $('#dataTable2').hide();
    $('#dashboard2').show();
    $('#ver-detalles').show();
}

function ocultarMaterialesUsados() {
    $('#mat').hide();
}

function verMaterialesUsados() {
    $('#mat').show();
}

function setDetalleVisible(valor) {
    if (valor) {
        $('#stock').removeClass('col-md-8');
        $('#stock').addClass('col-md-4');
        $('#mat').show();
    } else {
        $('#stock').removeClass('col-md-4');
        $('#stock').addClass('col-md-8');
        $('#mat').hide();
    }
}

function mostrarComprasR() {
    $('#comprasR').show();
    $('#comprasDasboards').hide();

}
function mostrarComprasP() {
    $('#comprasP').show();
    $('#comprasDasboards').hide();
}

function regresarCompras() {
    $('#comprasR').hide();
    $('#comprasP').hide();
    $('#comprasDasboards').show();
}

function buscarPorFecha() {
    // Obtener el valor de la fecha ingresada por el usuario
    const fechaBuscada = document.getElementById('fecha').value;

    // Recorrer todas las filas de la tabla
    const filas = document.querySelectorAll('#comprasP tbody tr');
    filas.forEach((fila) => {
        const fechaCompra = fila.querySelector('td:first-child').textContent;
        if (fechaCompra === fechaBuscada) {
            // Mostrar la fila si la fecha coincide con la buscada
            fila.style.display = 'table-row';
        } else {
            // Ocultar la fila si la fecha no coincide
            fila.style.display = 'none';
        }
    });
}

function buscarPorFechaR() {
    // Obtener el valor de la fecha ingresada por el usuario
    const fechaBuscada = document.getElementById('fechaR').value;

    // Recorrer todas las filas de la tabla
    const filas = document.querySelectorAll('#comprasR tbody tr');
    filas.forEach((fila) => {
        const fechaCompra = fila.querySelector('td:first-child').textContent;
        if (fechaCompra === fechaBuscada) {
            // Mostrar la fila si la fecha coincide con la buscada
            fila.style.display = 'table-row';
        } else {
            // Ocultar la fila si la fecha no coincide
            fila.style.display = 'none';
        }
    });
}


function mostrarVentaE() {
    $('#ventasE').show();
    $('#ventasDasboards').hide();

}
function mostrarVentasPE() {
    $('#ventasP').show();
    $('#ventasDasboards').hide();
}

function regresarVentas() {
    $('#ventasP').hide();
    $('#ventasE').hide();
    $('#ventasDasboards').show();
}