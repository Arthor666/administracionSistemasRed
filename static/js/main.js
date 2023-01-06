/* LISTENERS */
// Documento
document.addEventListener('DOMContentLoaded', cargarTopologia);

/* FUNCIONES */
async function cargarTopologia() { // Consultamos la API para obtener la topologia
    const response = await fetch('http://localhost:5000/topologia',
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'ip': '192.168.0.1',
                'name': 'R1',
                'user': 'r1router',
                'password': 'secret12'
            })
        }
    );
    // Obtenemos la imagen y la asignamos
    const blob = await response.blob();
    document.querySelector("#imagen-topologia").src = window.URL.createObjectURL(blob);
};
