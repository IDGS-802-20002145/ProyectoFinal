console.log('Hello World!');

function abrirModal() {
    $('#exampleModal').modal('show');
}

//ocultame de primera instancia el div con id dashboard2 y haz que se visualize cuando se haga click en el boton con id btnDashboard2
$('#dataTable2').hide();

function mostrarTabla(){
    $('#dataTable2').show();
    $('#dashboard2').hide();
    $('#ver-detalles').hide();
}
function mostrarDashboard(){
    $('#dataTable2').hide();
    $('#dashboard2').show();
    $('#ver-detalles').show();
}