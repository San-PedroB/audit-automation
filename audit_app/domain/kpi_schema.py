"""Shared KPI definitions used across dashboard, processing, and Excel export."""

CAMERA_COLUMN = "C\u00e1mara"
GENDER_COVERAGE = "Cobertura G\u00e9nero"
GENDER_COVERAGE_PCT = "% Cobertura G\u00e9nero"
GENDER_PRECISION = "Precisi\u00f3n de G\u00e9nero"
GENDER_PRECISION_PCT = "% Precisi\u00f3n de G\u00e9nero"
AGE_PRECISION = "Precisi\u00f3n de Edad"
AGE_PRECISION_PCT = "% Precisi\u00f3n de Edad"
EVENT_PRECISION_PCT = "% Precisi\u00f3n de Eventos"
BAD_EVENTS = "Eventos Malos del Sistema"
BAD_EVENTS_PCT = "% Eventos Malos sobre Total"

KPI_COLUMNS = [
    "Zona",
    "Fecha",
    "Hora_inicio",
    "Hora_termino",
    CAMERA_COLUMN,
    "Total Eventos",
    "Eventos Registrados por el Sistema",
    "% Eventos Registrados por el Sistema",
    "Eventos NO Registrados (Manuales)",
    "% Eventos NO Registrados (Manuales)",
    "Eventos Correctos del Sistema",
    EVENT_PRECISION_PCT,
    "% Eventos Correctos sobre Registrados",
    BAD_EVENTS,
    BAD_EVENTS_PCT,
    "Cobertura Identity",
    "% Cobertura Identity",
    "Identity Unknown",
    "% Identity Unknown",
    GENDER_COVERAGE,
    GENDER_COVERAGE_PCT,
    GENDER_PRECISION,
    GENDER_PRECISION_PCT,
    "Cobertura Edad",
    "% Cobertura Edad",
    AGE_PRECISION,
    AGE_PRECISION_PCT,
    "Tipo_sensor",
]

COUNT_COLUMNS = [
    "Total Eventos",
    "Eventos Registrados por el Sistema",
    "Eventos NO Registrados (Manuales)",
    "Eventos Correctos del Sistema",
    BAD_EVENTS,
    GENDER_PRECISION,
    AGE_PRECISION,
    "Identity Unknown",
    GENDER_COVERAGE,
    "Cobertura Edad",
    "Cobertura Identity",
]

TOP_METRIC_COLUMNS = [
    "Total Eventos",
    "Eventos Registrados por el Sistema",
    EVENT_PRECISION_PCT,
    BAD_EVENTS,
    "Eventos NO Registrados (Manuales)",
]

GLOBAL_SUMMARY_COLUMNS = [
    "Zona",
    "Total Eventos",
    "Eventos Correctos del Sistema",
    EVENT_PRECISION_PCT,
    "% Eventos Correctos sobre Registrados",
    BAD_EVENTS,
    BAD_EVENTS_PCT,
]

TOTAL_SUMMARY_COLUMNS = [
    "Total Eventos",
    "% Eventos Registrados por el Sistema",
    EVENT_PRECISION_PCT,
    "% Eventos Correctos sobre Registrados",
    BAD_EVENTS_PCT,
    "% Eventos NO Registrados (Manuales)",
]

CAMERA_SUMMARY_COLUMNS = [
    "Zona",
    CAMERA_COLUMN,
    "Total Eventos",
    "Eventos Registrados por el Sistema",
    "Eventos Correctos del Sistema",
    EVENT_PRECISION_PCT,
    "% Eventos Correctos sobre Registrados",
    BAD_EVENTS,
    BAD_EVENTS_PCT,
    "% Cobertura Identity",
]

UNKNOWN_COLUMNS = [
    "Zona",
    "Eventos Registrados por el Sistema",
    "Identity Unknown",
    "% Identity Unknown",
]

DATA_TABLE_SECTIONS = {
    "Contexto": ["Zona", "Fecha", "Hora_inicio", "Hora_termino", CAMERA_COLUMN],
    "Eventos": [
        "Zona",
        "Total Eventos",
        "Eventos Registrados por el Sistema",
        "% Eventos Registrados por el Sistema",
        "Eventos NO Registrados (Manuales)",
        "% Eventos NO Registrados (Manuales)",
        "Eventos Correctos del Sistema",
        EVENT_PRECISION_PCT,
        "% Eventos Correctos sobre Registrados",
        BAD_EVENTS,
        BAD_EVENTS_PCT,
    ],
    "Identity": [
        "Zona",
        "Cobertura Identity",
        "% Cobertura Identity",
        "Identity Unknown",
        "% Identity Unknown",
    ],
    "Genero": [
        "Zona",
        GENDER_COVERAGE,
        GENDER_COVERAGE_PCT,
        GENDER_PRECISION,
        GENDER_PRECISION_PCT,
    ],
    "Edad": [
        "Zona",
        "Cobertura Edad",
        "% Cobertura Edad",
        AGE_PRECISION,
        AGE_PRECISION_PCT,
    ],
    "Sensor": [
        "Zona",
        "Tipo_sensor",
    ],
}
