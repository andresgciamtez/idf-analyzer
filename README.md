# HIDRONEXO — idf_analyzer

Base de proyecto para análisis de frecuencia de precipitación, derivación de curvas intensidad–duración–frecuencia (IDF) y generación de tormentas de diseño. Se plantea como una biblioteca Python independiente; QGIS y sewer_sizer se conectarán mediante adaptadores en fases posteriores.

> **Estado:** prototipo de GUI y especificación inicial del núcleo. La interfaz calcula AMS anual con Gumbel por momentos y ajusta curvas tipo Sherman exploratorias; todavía no es una herramienta validada ni debe usarse para dimensionamiento.

## Objetivos

- Ingerir series pluviométricas de CSV y, con credenciales y permisos adecuados, AEMET OpenData.
- Mantener unidades, zona horaria, resolución, estación, procedencia y controles de calidad en cada conjunto de datos.
- Extraer máximos anuales (AMS) y excedencias sobre umbral (POT), dejando explícito el año hidrológico y las reglas de independencia de eventos.
- Ajustar Gumbel y GEV en la primera etapa estadística; dejar interfaces extensibles para SQRT-ETmax y Log-Pearson III.
- Estimar precipitaciones por duración y período de retorno, ajustar una relación IDF tipo Sherman y comparar resultados con la metodología aplicable de la Norma 5.2-IC.
- Generar hietogramas de diseño a partir de curvas aprobadas y exportar resultados reproducibles a JSON, YAML y CSV.

## Estructura

```text
idf_analyzer/
├── README.md
├── PLAN_DESARROLLO.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── src/idf_analyzer/
│   ├── adapters/       # contratos comunes, CSV, cliente AEMET
│   ├── statistics/     # AMS/POT, distribuciones y diagnósticos
│   ├── idf/            # cuantiles, Sherman y comparación 5.2-IC
│   ├── storms/         # bloques alternos y perfiles temporales
│   ├── exporters/      # JSON, YAML y CSV
│   └── integrations/   # futuras interfaces QGIS y sewer_sizer
├── tests/{unit,integration}/
├── examples/
├── docs/
├── data/{raw,processed}/
└── scripts/
```

Los ficheros de datos de usuario no deben versionarse. `data/` queda reservado para trabajo local; los ejemplos distribuirán datos sintéticos o con licencia compatible.

## Flujo previsto

1. Importar datos con intervalo temporal y unidades conocidos; validar monotonía, duplicados, huecos, valores negativos y cobertura.
2. Convertir a una base temporal uniforme sin imputar silenciosamente. Registrar cualquier filtro, agregación o exclusión.
3. Extraer extremos por duración. Para AMS, conservar un máximo por año y duración. Para POT, aplicar umbral, declustering y corrección de exposición para estimar frecuencia; no interpretar POT como AMS.
4. Ajustar distribuciones por duración, estimar incertidumbre y revisar ajuste, valores atípicos y estabilidad.
5. Obtener cuantiles para los períodos de retorno solicitados, ajustar Sherman y comprobar coherencia entre duraciones y unidades.
6. Comparar por separado con 5.2-IC, identificando datos, tablas, ecuaciones y supuestos normativos usados.
7. Construir tormentas de diseño con suma de bloques consistente con la precipitación objetivo y exportar datos, parámetros, método y trazabilidad.

Una serie diaria permite estudiar duraciones diarias y superiores; no recupera la estructura subdiaria. Las IDF subdiarias requieren datos de resolución subdiaria o una metodología regional/normativa apropiada, que debe identificarse como tal.

## Interfaz gráfica (prototipo)

La GUI de escritorio usa Tkinter, incluido en Python, y se lanza en Windows con:

```powershell
.\scripts\launch_gui.ps1
```

La aplicación carga CSV, permite seleccionar fecha y precipitación, calcula AMS por año calendario para duraciones que sean múltiplos del intervalo declarado, ajusta Gumbel por momentos, muestra una gráfica preliminar y exporta CSV/JSON con parámetros Sherman exploratorios. El CSV debe tener una fila por intervalo uniforme, fechas ISO 8601 y precipitación acumulada en mm por intervalo. La app detecta huecos, marcas repetidas e intervalos irregulares y exige al menos tres años, pero no descarta automáticamente años incompletos. Use UTC o una zona horaria explícita y revise la cobertura anual.

Esta versión todavía no implementa POT, GEV, SQRT-ETmax, Log-Pearson III, método 5.2-IC ni tormentas de diseño. Las curvas Sherman exploratorias no equivalen a una curva aprobada o normativa. Los resultados no deben usarse para diseño hasta validar métodos, datos y casos de referencia.

## Solicitud y carga de datos AEMET

1. Enviar la consulta general de `docs/SOLICITUD_DATOS_AEMET.md` por el canal de consultas de la Sede electrónica: confirmar API Key, política de integración, catálogo y resolución histórica de precipitación, cuotas, metadatos y condiciones de reutilización.
2. Para productos publicados en AEMET OpenData, solicitar y custodiar una API Key y consultar la documentación HATEOAS del acceso para desarrolladores.
3. La API devuelve un primer JSON con el estado y enlaces a datos/metadatos; descargarlos inmediatamente porque son temporales. Respetar cuotas, controlar HTTP 429 y renovar las claves según su vigencia.
4. Si un producto no está publicado o necesita adaptación, preguntar por el trámite general de solicitud, costes aplicables y condiciones antes de pedirlo.
5. Conservar los datos y metadatos recibidos con su procedencia, versión, fecha de descarga y condiciones de uso. La GUI actual todavía solo importa CSV; el cliente AEMET se desarrollará después de confirmar estas condiciones.

Plantilla de consulta: [`docs/SOLICITUD_DATOS_AEMET.md`](docs/SOLICITUD_DATOS_AEMET.md).
## Instalación de desarrollo

Se propone Python 3.11 o posterior. La versión mínima se confirmará en la fase 0 según compatibilidad con dependencias y QGIS objetivo.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Dependencias previstas

- Núcleo numérico: NumPy y SciPy (ajustes y estadística); pandas opcional para interoperabilidad tabular.
- Formatos: PyYAML para YAML; JSON y CSV con biblioteca estándar.
- Calidad: pytest, Ruff y mypy como herramientas de desarrollo previstas.
- Conectividad AEMET: cliente HTTP estándar o httpx, seleccionando una sola opción tras revisar API, reintentos, cuotas y política de credenciales.
- QGIS: API PyQGIS solo en el adaptador de integración; no como dependencia del núcleo.

Las versiones exactas y licencias se fijarán en `pyproject.toml`/archivo de bloqueo tras una revisión de compatibilidad. No se incorporará `idf-analysis` como dependencia ni se copiará su código sin una decisión explícita de arquitectura y revisión de licencia; sirve como referencia metodológica externa. Su repositorio declara MIT y describe implementación de DWA-A 531, que no sustituye la metodología española 5.2-IC.

## Licencia

La licencia propuesta para el código nuevo de HIDRONEXO es **MIT**, sujeta a confirmación del titular del proyecto antes de publicar. El archivo `LICENSE` es una plantilla que debe completarse con el titular y año correctos. Datos AEMET, datos de terceros y texto normativo conservan sus condiciones propias; esta licencia no los relicencia.

## Validación técnica

Consulta [PLAN_DESARROLLO.md](PLAN_DESARROLLO.md) para fases, pruebas, criterios de aceptación e hitos. Ningún resultado se presentará como conforme a 5.2-IC hasta implementar y verificar sus ecuaciones/tablas vigentes con casos de referencia independientes y documentados.

## Referencias iniciales

- [AEMET OpenData](https://opendata.aemet.es/centrodedescargas/inicio): acceso a información, API key y condiciones de reutilización.
- [Orden FOM/298/2016 (BOE)](https://www.boe.es/eli/es/o/2016/02/15/fom298): aprobación de la Norma 5.2-IC; revisar correcciones y actualizaciones aplicables antes de codificar.
- [Versión consolidada de 5.2-IC (Ministerio de Transportes)](https://cdn.transportes.gob.es/portal-web-transportes/carreteras/normativa_tecnica/07_drenaje/52ic_fom2982016_err_fom1852017_res180326_consolidado.pdf).
- [idf-analysis (Markus Pichler)](https://github.com/MarkusPic/intensity_duration_frequency_analysis): referencia de diseño de software y análisis de lluvia intensa, licencia MIT indicada en el repositorio; no implica equivalencia normativa.




