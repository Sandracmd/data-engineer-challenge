Este proyecto consiste en dos microservicios en Python para procesar coordenadas geográficas y obtener códigos postales del Reino Unido mediante la API pública [postcodes.io](https://postcodes.io/). 

- El microservicio 1 recibe un archivo CSV con coordenadas, valida su contenido y guarda los datos en una base de datos PostgreSQL.
- El microservicio 2 consulta las coordenadas almacenadas, llama a la API para obtener el código postal más cercano, actualiza la base de datos con el resultado o registra errores en caso de fallo.

## Arquitectura

- Dos microservicios independientes y desacoplados.
- Comunicación mediante base de datos compartida.
- Control de errores para garantizar que todas las coordenadas tengan un código postal o un mensaje de error.
- Contenerización con Docker para facilitar el despliegue.
- Orquestación con Docker Compose para levantar ambos servicios y la base de datos simultáneamente.

+----------------+          +----------------+          +----------------+
| Microservicio 1|          |  Base de Datos |          | Microservicio 2|
| - Recibe CSV   |  <-----> |  PostgreSQL    |  <-----> | - Consume DB   |
| - Valida CSV   |          |                |          | - Consulta API |
+----------------+          +----------------+          +----------------+
                                    |
                                    |
                          +----------------------+
                          |   API postcodes.io   |
                          |    (Externa, UK)     |
                          +----------------------+

## Cómo correr el proyecto

1. Clonar el repositorio.
2. Configurar variables de entorno si es necesario (opcional).
3. Levantar los servicios y la base de datos en CMD con docker-compose up --build
4. Usar el comando curl.exe -v -X POST "http://localhost:8080/upload" -H "accept: application/json" -F "file=@coordenates.csv" para levantar el microservicio 1
5. Usar el comando http://localhost:8001/update-postcodes para levantar el microservicio 2
6. El microservicio 1 escucha en http://localhost:8000 y expone el endpoint para subir el archivo CSV (POST /upload)
7. El microservicio 2 escucha en http://localhost:8001 y expone el endpoint para actualizar postcodes (GET /update-postcodes)