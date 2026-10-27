# Consulta general sobre AEMET OpenData y automatización de descargas

**Canal recomendado:** formulario de consultas de la Sede electrónica de AEMET: https://sede.aemet.gob.es/AEMET/es/GestionPeticiones/NuevaConsulta

**Asunto:** Consulta técnica sobre AEMET OpenData, automatización de descargas y solicitud de datos no disponibles

Estimado equipo de AEMET:

Les escribo en representación de HIDRONEXO. Estamos desarrollando `idf_analyzer`, una aplicación de escritorio para análisis hidrológico que actualmente carga series de precipitación desde CSV. Estamos evaluando incorporar una conexión con AEMET OpenData para que los usuarios puedan consultar productos disponibles y descargar series de forma asistida o automatizada.

Antes de diseñar e implementar esa integración, agradeceríamos su orientación sobre el procedimiento correcto y el alcance permitido. No se trata por ahora de una solicitud de datos para una estación o período concretos ni de un encargo de extracción; queremos entender el flujo general y qué pasos debe completar la empresa o cada usuario.

En particular, agradeceríamos información sobre los siguientes puntos:

1. **Alta y credenciales:** ¿Cómo debe solicitarse y administrarse actualmente la API Key para una aplicación de escritorio? ¿Se emite a una persona o puede asociarse a una organización? ¿Cuál es su vigencia, cómo se renueva y qué práctica recomiendan para credenciales de desarrollo y producción?
2. **Automatización:** ¿El acceso para desarrolladores está destinado a descargas iniciadas por el usuario y también a procesos periódicos automatizados dentro de una aplicación de terceros? ¿Hay condiciones adicionales para integrar el acceso de AEMET en una herramienta utilizada por clientes o usuarios de HIDRONEXO?
3. **Catálogo de precipitación:** ¿Qué recursos/endpoints ofrecen series históricas de precipitación y sus metadatos? Nos interesa conocer la resolución temporal disponible (en particular, si existen series subdiarias adecuadas para análisis IDF), cobertura histórica, disponibilidad por estación, controles/flags de calidad y limitaciones de los datos diarios.
4. **Flujo de la API:** Entendemos que las peticiones de consulta pueden devolver enlaces a los datos y metadatos. ¿Es correcto que la aplicación debe consumir esos enlaces inmediatamente? ¿Qué formatos, caducidad y secuencia de peticiones debemos contemplar para implementar una descarga robusta?
5. **Cuotas y resiliencia:** ¿Cuáles son los límites vigentes por clave, usuario o recurso, y cómo recomiendan tratar respuestas HTTP 429, errores temporales y solicitudes de gran volumen? ¿Existe alguna política de espera, reintento o ventana de mantenimiento que debamos respetar?
6. **Uso y distribución:** ¿Qué atribución y condiciones de reutilización debemos mostrar en la aplicación y en los resultados? ¿Podemos conservar localmente los ficheros originales descargados para que el usuario los procese después? ¿Hay restricciones para redistribuir datos, incluso como parte de informes generados por la aplicación?
7. **Datos fuera de OpenData:** Si la resolución, estación o antigüedad requerida no está disponible en el catálogo, ¿cuál es el procedimiento general para solicitar esos datos o una extracción adaptada? ¿Qué conceptos pueden tener coste, cómo se determina el presupuesto y qué canal de entrega se utiliza? En esta fase solo necesitamos conocer el procedimiento y los criterios, no solicitar una cotización concreta.
8. **Material técnico:** ¿Podrían indicarnos la documentación vigente para desarrolladores, ejemplos oficiales de cliente Python, catálogo de endpoints y cualquier guía o contacto técnico recomendado para validar esta integración?

Nuestra intención es implementar un cliente que use el catálogo oficial, respete las cuotas, proteja las credenciales y permita conservar la procedencia y los metadatos de cada descarga. Si para integrar OpenData basta con seguir la documentación pública y solicitar una API Key individual, agradeceríamos que nos lo confirmaran; si se requiere autorización, registro o trámite específico para una aplicación distribuida a usuarios, agradeceríamos que nos indicaran cuál.

Muchas gracias por su atención. Quedamos pendientes de sus recomendaciones sobre el procedimiento y el canal adecuado para consultas técnicas o solicitudes de datos no incluidos en OpenData.

Atentamente,

[Nombre y apellidos]  
[Cargo / área]  
HIDRONEXO  
[Teléfono]  
[Correo electrónico]

---

## Notas de documentación consultada

- AEMET documenta OpenData como API REST y distingue el acceso general del acceso de desarrolladores, que admite consultas periódicas/programadas desde aplicaciones. La descarga del catálogo publicado es gratuita y requiere API Key.
- La documentación dinámica de desarrolladores presenta HATEOAS, ejemplos de clientes y una biblioteca Python oficial.
- La FAQ vigente indica un límite general publicado de 40 consultas por minuto, con posibles límites adicionales por recurso y respuestas 429. La integración debe respetar los límites y confirmar con AEMET cualquier uso voluminoso.
- El flujo de respuesta de API puede incluir URLs separadas para los datos y sus metadatos; la FAQ indica que son temporales (aprox. cinco minutos). La implementación deberá recuperarlas en la misma ejecución y conservar los metadatos necesarios.
- La FAQ actual informa de renovación de API Keys cada tres meses y de que las claves antiguas sin fecha de caducidad dejaron de aceptarse desde el 15 de octubre de 2026. Conviene confirmar el procedimiento vigente con AEMET antes de desplegar la integración.
- La FAQ indica que algunos productos no abiertos o adaptaciones específicas se solicitan por la Sede electrónica o registro y pueden llevar coste por preparación/suministro. Los datos entregados a medida pueden tener condiciones distintas de los del catálogo OpenData.

Fuentes oficiales:

- [AEMET OpenData: información y acceso](https://opendata.aemet.es/centrodedescargas/info)
- [FAQ AEMET OpenData](https://opendata.aemet.es/centrodedescargas/faqs)
- [FAQ en PDF (versión 1.4, 28/07/2025)](https://opendata.aemet.es/centrodedescargas/docs/FAQs220424.pdf)
- [Acceso para desarrolladores, documentación HATEOAS y ejemplos](https://opendata.aemet.es/centrodedescargas/AEMETApi)
- [Consultas en la Sede electrónica de AEMET](https://sede.aemet.gob.es/AEMET/es/GestionPeticiones/NuevaConsulta)
- [Solicitud de certificados y datos en la Sede electrónica](https://sede.aemet.gob.es/AEMET/es/GestionPeticiones/solicitudes)
