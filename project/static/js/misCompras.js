function mostrarPendientes() {
    document.querySelectorAll('.ventasAp').forEach(element => element.classList.add('d-none'));
    document.querySelectorAll('.ventas').forEach(element => element.classList.remove('d-none'));
    document.querySelector('#btn-en-camino').classList.remove('active');
    document.querySelector('#btn-pendientes').classList.add('active');
  }

  // Función para ocultar las compras pendientes y mostrar las en camino
  function mostrarEnCamino() {
    document.querySelectorAll('.ventas').forEach(element => element.classList.add('d-none'));
    document.querySelectorAll('.ventasAp').forEach(element => element.classList.remove('d-none'));
    document.querySelector('#btn-pendientes').classList.remove('active');
    document.querySelector('#btn-en-camino').classList.add('active');

  }

  function mostrarSoloBotones() {
    document.querySelectorAll('.ventas').forEach(element => element.classList.add('d-none'));
    document.querySelectorAll('.ventasAp').forEach(element => element.classList.add('d-none'));
    document.querySelector('#btn-en-camino').classList.remove('active');
    document.querySelector('#btn-pendientes').classList.add('active');
  }


  // Asignar las funciones a los botones correspondientes
  document.querySelector('#btn-pendientes').addEventListener('click', mostrarPendientes);
  document.querySelector('#btn-en-camino').addEventListener('click', mostrarEnCamino);