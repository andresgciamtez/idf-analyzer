# Plan de desarrollo — idf_analyzer

## 1. Propósito y límites

Desarrollar para HIDRONEXO una biblioteca Python trazable que transforme observaciones de precipitación en cuantiles por duración y período de retorno, curvas IDF y tormentas de diseño. El núcleo será independiente de QGIS, AEMET y sewer_sizer; cada conexión se implementará mediante adaptadores.

La comparación con la Norma 5.2-IC tendrá dos niveles claramente separados: (a) comparación numérica con sus procedimientos y datos tabulados vigentes, y (b) uso de 5.2-IC cuando sus hipótesis y ámbito sean aplicables. Un ajuste estadístico local de extremos no se etiquetará automáticamente como cálculo normativo. Antes de certificar conformidad se revisarán el texto consolidado, correcciones, tablas actualizadas, unidades y ámbito de aplicación.

Estado a 27 de octubre de 2026: se añadió y lanzó un prototipo de GUI de escritorio para CSV, AMS anual, Gumbel por momentos, curvas exploratorias y exportación CSV/JSON. Esta entrega adelanta una interfaz básica; los criterios de validación estadística, POT, GEV, 5.2-IC, tormentas de diseño e integración QGIS/sewer_sizer continúan pendientes según las fases siguientes.

La resolución de origen limita la duración mínima inferible. No se derivarán intensidades subdiarias observadas de datos diarios. Los resultados de alta extrapolación incluirán incertidumbre y advertencias de soporte muestral.

## 2. Arquitectura y paquetes

```text
src/idf_analyzer/
  domain/             # modelos de observación, serie, evento, ajuste y curva
  adapters/           # protocolo de entrada, CSV y AEMET
  quality/            # validación temporal, cobertura y controles de calidad
  statistics/         # AMS, POT, Gumbel, GEV y diagnósticos
  idf/                # conversión profundidad-intensidad, Sherman, 5.2-IC
  storms/             # bloques alternos y perfiles de tormenta
  exporters/          # JSON, YAML, CSV y metadatos
  integrations/       # fronteras QGIS y sewer_sizer
```

El dominio solo contendrá modelos y reglas hidrológicas; las dependencias de API, interfaz y SIG vivirán fuera. Cada resultado debe poder reproducirse con versión del programa, método, parámetros, unidad, resolución, estación, período analizado, filtros y huella del conjunto de entrada.

### Contratos principales

- `PrecipitationSeries`: tiempos, precipitación, unidad, intervalo, estación, zona horaria, fuente y control de calidad.
- `ExtremeSample`: duración, tipo AMS/POT, valores, exposición y definición del año hidrológico o declustering.
- `FrequencyFit`: distribución, método de estimación, parámetros, diagnóstico, incertidumbre y dominio válido.
- `IDFCurve`: profundidades e intensidades por duración y retorno, parametrización, unidad y trazabilidad.
- `DesignStorm`: pasos temporales, lluvia por paso, duración total, precipitación objetivo y método de ordenación.

Los nombres son contratos propuestos; se concretarán con tipado y versionado en fase 1.

## 3. Fases, hitos y criterios de aceptación

### Fase 0 — Decisiones y especificación

- Confirmar titular y licencia del código, Python objetivo, entorno de despliegue y versiones de QGIS/sewer_sizer que se quieran soportar.
- Crear inventario de productos y resolución histórica de lluvia, e investigar API Key, uso en software de terceros, cuotas, caducidad, URLs temporales, reutilización y solicitud adaptada usando `docs/SOLICITUD_DATOS_AEMET.md`.
- Elegir convenciones: UTC y presentación local, zona hidrológica, unidades, tratamiento de faltantes, acumulaciones móviles y años incompletos.
- Revisar 5.2-IC consolidada y cambios de tablas, recopilar ejemplos verificables y aclarar el alcance de comparación.

**Hito H0:** decisiones registradas y conjunto mínimo de datos de prueba aprobado. **Aceptación:** cada elección metodológica tiene dueño, evidencia y efecto documentado.

### Fase 1 — Esqueleto del paquete y contratos

- Configurar paquete `src/`, metadatos, formato, análisis estático, documentación y CI.
- Definir modelos tipados, errores, interfaces de adaptadores, metadatos de procedencia y esquema de exportación versionado.
- Documentar unidades (mm, mm/h), timestamps, intervalos y convenciones de bordes.

**Hito H1:** paquete instalable y contratos revisados. **Aceptación:** ejemplos de dominio válidos, errores de entrada comprensibles, importación del núcleo sin QGIS/API y esquema JSON validable.

### Fase 2 — Entradas y calidad de datos

- Implementar CSV configurable (delimitador, columnas, decimal, formato fecha, unidad e intervalo explícitos).
- Implementar chequeos de duplicados, orden, huecos, valores físicamente imposibles, cobertura y consistencia de intervalo.
- Añadir reporte de calidad reproducible; no interpolar ni descartar datos sin una opción registrada.
- Construir cliente AEMET solo tras confirmar endpoint/producto, API key, políticas de reintento/cuota, términos y coste. El flujo documentado es consulta REST → respuesta con URLs temporales de datos/metadatos → descarga inmediata; soportar 401, 403, 404 y 429 y respetar el límite general publicado (40 consultas/minuto, sujeto a límites adicionales del recurso). Proteger y renovar la clave, no registrarla en logs, y guardar procedencia/metadatos con los datos. Para productos fuera del catálogo, orientar a la Sede electrónica para consultar procedimiento y posibles costes de adaptación/suministro.

**Hito H2:** importación de archivos reproducible. **Aceptación:** fixtures sintéticos con huecos, duplicados, cambios de horario y datos inválidos producen reportes esperados; ningún dato se altera en silencio.

### Fase 3 — Series extremas y distribuciones

- AMS: máximos por año y duración, reglas explícitas para años parciales y datos faltantes.
- POT: umbral, separación/decluster de eventos, duración de exposición y tasa de excedencias; documentar fórmula de período de retorno compatible con el modelo adoptado.
- Ajustar Gumbel y GEV por métodos definidos en fase 0 (p. ej. máxima verosimilitud y/o momentos L), con cuantiles, intervalos de confianza y diagnósticos.
- Diseñar interfaz para SQRT-ETmax y Log-Pearson III, que se incorporarán solo después de especificar convenciones y validar datos de referencia.

**Hito H3:** motor de frecuencia validado en casos de referencia. **Aceptación:** parámetros y cuantiles concuerdan con cálculos independientes dentro de tolerancias preestablecidas; límites de soporte, muestras pequeñas, no convergencia e incertidumbre se informan.

### Fase 4 — Curvas IDF tipo Sherman y contraste 5.2-IC

- Calcular acumulaciones para duraciones compatibles con el paso de datos, manteniendo clara la distinción entre acumulación deslizante y bloques fijos.
- Obtener cuantiles de lluvia por duración y retorno, convertir profundidad a intensidad con unidades comprobadas.
- Ajustar una forma Sherman configurable, por ejemplo `i(t,T)=a(T)/(t+b)^n`, y registrar parámetros, rango de ajuste, residuos y pesos. Evaluar ajuste conjunto o por retorno antes de fijar la parametrización.
- Implementar una comparación identificable con 5.2-IC: procedimiento, ecuación, tablas/versión, entradas, diferencias y limitaciones. No sustituir las tablas oficiales por una curva local sin declarar el cambio.

**Hito H4:** curvas y comparación reproducibles. **Aceptación:** intensidades no negativas; coherencia de unidades; monotonicidad física revisada; curva evaluada dentro del rango observado y diagnóstico explícito fuera de él; ejemplo de contraste contrastado independientemente.

### Fase 5 — Tormentas de diseño y exportación

- Construir hietogramas por bloques alternos como método inicial, conservando profundidad acumulada de las curvas objetivo para las duraciones definidas.
- Tratar orden, intervalo y duración como parámetros. Añadir otros perfiles solo con referencias de uso acordadas.
- Exportar JSON, YAML y CSV con esquema versionado, metadatos, unidades, método, fuente y trazabilidad. Rechazar exportaciones incompletas o no finitas.

**Hito H5:** artefactos intercambiables. **Aceptación:** relectura de exportación reproduce los valores (dentro de precisión documentada), masa de precipitación se conserva y los metadatos identifican el cálculo.

### Fase 6 — Integración y publicación

- Crear integración QGIS delgada: selección de capas/estaciones, parámetros, progreso, reporte y resultados; no duplicar cálculo.
- Crear puente de intercambio con sewer_sizer (formato estable, unidades declaradas y versiones compatibles).
- Preparar guía de usuario, ejemplos con datos sintéticos, changelog, versionado semántico y publicación interna.

**Hito H6:** versión candidata integrada. **Aceptación:** flujos de extremo a extremo repetibles en entornos soportados; instalación limpia y compatibilidad documentada; informe de limitaciones y validación revisado.

## 4. Validación y pruebas

Las pruebas acompañarán a cada fase; no basta con que el software ejecute.

- **Unitarias:** conversión mm↔mm/h, delimitación de años, extremos por duración, declustering POT, fórmulas de cuantiles, Sherman, conservación de masa y serialización.
- **Propiedades:** ninguna profundidad negativa; intensidad = profundidad/duración con conversión coherente; tormenta suma la precipitación objetivo; resultados deterministas con iguales entradas/semilla.
- **Regresión:** conjuntos sintéticos deterministas y casos de referencia calculados independientemente, con tolerancia numérica documentada y versiones de referencia.
- **Integración:** CSV/AEMET simulado → control de calidad → extremos → ajuste → IDF → tormenta → exportación y lectura de vuelta.
- **Normativa:** comparación de resultados intermedios con ejemplos y tablas aplicables de 5.2-IC, revisión por especialista y registro de edición/correcciones consultadas.
- **Robustez:** huecos, intervalos irregulares, cambios horario verano/invierno, series cortas, valores repetidos, outliers, retorno extremo y errores de red/cuota.

Métricas mínimas por fase: cobertura de código orientativa ≥80% para módulos hidrológicos críticos; cobertura no sustituye revisión de casos. Criterios cuantitativos de tolerancia se fijarán antes de comparar resultados, según precisión de referencias y redondeo publicado.

## 5. Dependencias, licencias y datos

- Propuesta de licencia del código nuevo: MIT, pendiente de confirmación de titularidad; completar `LICENSE` antes de publicar.
- NumPy/SciPy para cálculo; pandas solo si aporta interoperabilidad; PyYAML para YAML; cliente HTTP único para AEMET. Validar licencias de dependencias y fijar versiones compatibles en cada release.
- QGIS/PyQGIS queda como extra o integración externa, evitando que la instalación base dependa de una versión concreta de QGIS.
- `idf-analysis` se usa como referencia técnica externa (su repositorio indica MIT), no como dependencia automática. Revisar compatibilidad metodológica: implementa DWA-A 531 y eso no acredita conformidad con 5.2-IC.
- Las condiciones de AEMET, datos adquiridos y normativa prevalecen sobre la licencia del código. No publicar observaciones protegidas ni credenciales; conservar citas y atribución requerida.

## 6. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Datos diarios usados para inferir intensidades subdiarias | Validar resolución y bloquear extrapolación no justificada; marcar claramente métodos regionales. |
| Muestra corta y retornos muy altos | Mostrar incertidumbre, rango de soporte y advertencia; no presentar extrapolación como observación. |
| POT con eventos dependientes o exposición incorrecta | Parametrizar declustering y tasa, documentar hipótesis y validar sensibilidad. |
| Diferencia entre ajuste estadístico y procedimiento normativo | Reportar ambos por separado y versionar tablas/ecuaciones de 5.2-IC. |
| Cambios o límites de acceso AEMET | Aislar con adaptador, simular red en pruebas, tratar cuotas y no almacenar claves. |
| Dependencias incompatibles con PyQGIS | Mantener núcleo independiente y matriz explícita de versiones. |
| Licencias/redistribución de datos no claras | Revisión antes de descarga/publicación y atribución en metadatos. |

## 7. Hitos de entrega

| Hito | Entregable |
|---|---|
| H0 | Decisiones metodológicas, licencia y fuentes documentadas |
| H1 | Paquete base y contratos de datos/resultados |
| H2 | Adaptadores CSV y calidad de datos; AEMET condicionado a acceso aprobado |
| H3 | AMS/POT, Gumbel/GEV y diagnósticos validados |
| H4 | Curvas Sherman y comparación documentada con 5.2-IC |
| H5 | Tormentas y exportación JSON/YAML/CSV |
| H6 | Integraciones QGIS y sewer_sizer, guía y versión candidata |

Los plazos se estimarán tras H0, cuando se conozcan datos, resolución objetivo, disponibilidad del especialista normativo y alcance de integración.

## 8. Fuentes de partida

- AEMET OpenData: https://opendata.aemet.es/centrodedescargas/inicio
- Orden FOM/298/2016 y referencias posteriores: https://www.boe.es/eli/es/o/2016/02/15/fom298
- Texto consolidado de 5.2-IC: https://cdn.transportes.gob.es/portal-web-transportes/carreteras/normativa_tecnica/07_drenaje/52ic_fom2982016_err_fom1852017_res180326_consolidado.pdf
- Referencia de implementación IDF: https://github.com/MarkusPic/intensity_duration_frequency_analysis (MIT declarado en el repositorio; DWA-A 531).





