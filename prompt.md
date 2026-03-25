## Repository Overview
1. Monorepo con múltiples SaaS independientes. Todos los backends están **fusionados en `backend_micro/`** como un solo servidor FastAPI y Mariadb. Los frontends son apps React+Vite independientes que apuntan al mismo backend.
2. Los frontend deben estar en carpetas separadas
3. El backend debe estar todo en una carpeta para que pueda retomar las mismas keys de .env, como por ejemplo la de paypal para cobrar los SaaS
4. El url del sitio es micro-servicios.com.mx
5. Debe haber una landing page inicial que redirija a los SaaS, cada SaaS debe tener su propia ruta o url por ejemplo https://micro-servicios.com.mx/Saas1, https://micro-servicios.com.mx/Saas2, https://micro-servicios.com.mx/Saas3 ... https://micro-servicios.com.mx/SaasN
5. Todos los servicios deben estar separados y ser independientes uno de otro, es decir, yo como usuario de SaaS1 en mi página de perfil de usuario no tengo porque ver otros servicios en los cuales no me he registrado.
6. La identidad del sitio debe ser igual en todos los servicios, colores, logo, estilos, etc.

## Stack (opcional, modifica si crees que es mejor algo)
Usa skill de /senior-backend para el diseño
Backend: FastAPI, SQLAlchemy async, MySQL/MariaDB, httpx, pydantic
Frontend: React + Vite, Axios, PayPal JS SDK

## Landing Page
Crear una Landing Page usando el skill /frontend-design, con estilos, usando colores, estilos y efectos parecidos a la siguiente página: https://techy-xi.vercel.app/?storefront=envato-elements 
La página tiene el objetivo de mostrar algunos servicios web, los cuales deberan tener una tarjeta de acceso, así como también ser parte de los menús.
Genera descripciones para cada micro-servicio, la idea es venderlos por medio de publicidad CEO, usa palabras y estilos que promuevan esas características.
Agrega imágenes relacionadas desde catálogos de imagenes gratuitas en la web
Escribe la página en español.
Estos son los micro-servicios:

## Servicios SaaS

### PROMPT SaaS IQTest
Es un cuestionario estilo wizard, con botones siguiente y atras, el cual hace preguntas para evaluar el Coeficiente Intelectual del usuario. El cuestionario realiza un recuento del tiempo utilizado para contestar el cuestionario, mostrando un reloj en la parte superior y evalúa las preguntas contestadas correctamente para emitir un veredicto con el resultado final, mostrando valores un gráfico con los resultados del test. Se utiliza un script para consultar API de un servicio de inteligencia artificial, ya sea gemini, openai o openrouter (El servicio se debe configurar en un archvo de configuración) para generar las preguntas, las cuales se almacenan en una base de datos y se seleccionan preguntas de manera aleatoria para presentarlas al usuario. Al final, se emite un resultado sencillo general pero se ofrece emitir graficas detalladas y un diploma con QR para descargar. Los ámbitos a evaluar serían comprensión lectora, razonamiento fluido, procesamiento visoespacial, memoria de trabqajo, velocidad de procesamiento y razonamiento cualitativo. El costo por descargar un informe detallado es de 1 dolar estadounidense.
Modelo de negocio: pago por resultados

### PROMPT SaaS Convertir tablas a Excel
Se permite subir un archivo pdf o en imagen y convertir las tablas a Excel, por medio del uso de un servicio de IA con un modelo de imagen combinado con pdfplumber y algún framework de ocr de python, dando un especial cuidado en las cantidades, las cuales deben corresponder y cuadrar con el archivo subido. El servicio es por suscripción y ofrece una prueba gratis por 10 archivos. La IA sirve para leer los datos, rectificar que se haya hecho bien el proceso y control de calidad. 
Pago mensual.
| Plan      | Conversiones  | Precio    | Por conversión    |
|------     |-------------  |--------   |----------------   |
| Básico    | 200           | $200 MXN  | ~$1.00 MXN        |
| Estándar  | 400           | $300 MXN  | ~$0.75 MXN        |
| Premium   | 600           | $350 MXN  | ~$0.58 MXN        |


### PROMPT SaaS Historia clínica con IA
Generar 
Similar a https://clinicnet.app/

4. Restauración de fotografías antiguas con IA
Permite reparar una fotografía por 1 dolar o 20 pesos mexicanos. Se debe subir la imagen escaneada en alta resolución y la imagen debe ser tratada con IA con la API de Nanobanana. Permite descargar la imagen, enviarla por correo y almacenarla en una url por un mes.
Similar a https://picsart.com/es/ai-image-enhancer/photo-restoration/

5. Quinielas entra amigos
Este servicio retoma los partidos de la liga MX de la jornada actual, los consulta por medio de scraping o por medio de una consulta con servicio de IA. Crea un formulario con formato de quiniela con las opciones: Gana local, empata y Gana visitante. 
Existe un usuario organizador que puede crear la quiniela, modificarla, agregar o quitar equipos, agregar las fechas de los partidos y una fecha de cierre, después invitar a los participantes por medio de correo electrónico o por medio de un link.
Por cada resultado atinado, se le asigna un punto al ganador. Al momento de ingresar una quiniela se hace el pago de 100 pesos y el monto se va acumulando en una bolsa. En el pago de la quiniela se hace un cobro de 115 pesos de comisión por el servicio de pasarela de pagos y procesamiento. El servicio envía un correo electrónico con el registro de la quiniela y además el usuario cuenta con un panel donde se ve los participantes y sus elecciones. El participante puede poner un alias en su nombre. Al momento de cerrar las apuestas 15 minutos antes de que empiece el primer partido se envía otro correo a los usuarios participantes. Al finalizar el último partido, el servicio revisa los resultados por medio de scraping o servicio de IA, envía un correo al organizador con los resultados. El organizador puede ingresar cuando se generan los resultados para corregir o ratificar los resultados, en ese momento, la quiniela se debe enviar un correo con los resultados y solicitar el número de clave interbancaria (CLABE) para depositar a los ganadores que tengan más cantidad de puntos.
El mínimo de partidos debe de ser de 9, que son los que se juegan en cada jornada.
El servicio debe estar pendiente en el servidor, ya sea con un cron o con otra estrategia para determinar cuando se inicia con el primer partido y se termina con el último partido.

6. Cuestionarios para alumnos en clase


7. Generador de QR
8. Generador de QR de menú, subir menú
9. Test de orientación vocacional
10. Lectura de Tarot
11. Acortador de enlace
12. Te digo tu futuro
13. De imagen a diagrama en powerpoint
14. Desarrollo de Landing Page
15. Generación de Curriculum
16. Estructura Política
17. Mesa de Regalos

## Puntualizaciones
Genera todos los archivos adicionales del código: .gitignore .env requirements.txt 
Debe permitir el registro con google o facebook o con un correo electrónico
Todos los SaaS pueden funcionar con el mismo registro, por lo mismo se usa un solo backend con endpoints para cada servicio
Todos los servicios se cobran usando paypal
Cada servicio debe contener una página de información con los datos del usuario y pagos realizados
Se debe crear un log para registrar las actividades del sistema, como eventos, pagos, registro, logueo, etc.


## Crea una estructura de Directorios (Orientada a IA)**
```text
micro-servicios-app/
├── .env                  
├── .gitignore            
├── CLAUDE.md             # Reglas base de IA, stack, dominio e idioma
├── docs/                 
│   ├── architecture.md
│   ├── decisions/        
│   └── runbooks/         
├── tools/
│   └── scripts/          
├── backend/
│   ├── requirements.txt  # FastAPI, httpx, bs4, sqlalchemy, paypalrestsdk, etc.
│   ├── main.py
│   └── app/
│       ├── core/         
│       ├── models/       
│       ├── routers/      
│       └── services/     # paypal_service.py
└── frontend1/
│   ├── package.json
│   └── src/
└── frontend2/
│   ├── package.json
│   └── src/
└── frontend3/
    ├── package.json
    └── src/
```

