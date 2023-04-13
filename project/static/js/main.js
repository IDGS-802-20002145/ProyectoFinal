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