import pytest


@pytest.fixture
def sample_datos():
    """Minimal valid datos dict as returned by procesar_pdf."""
    return {
        "patente": "BBFC12",
        "rut": "12.345.678-9",
        "nombre": "JUAN PEREZ GONZALEZ",
    }


@pytest.fixture
def sample_multas():
    """List of prescribible fines grouped for one court."""
    return [
        {
            "juzgado": "JUZGADO DE POLICIA LOCAL DE SANTIAGO",
            "rol": "123-2020",
            "fecha_ingreso": "15-03-2020",
        },
        {
            "juzgado": "JUZGADO DE POLICIA LOCAL DE SANTIAGO",
            "rol": "456-2021",
            "fecha_ingreso": "10-06-2021",
        },
    ]


@pytest.fixture
def sample_multas_multiple_courts():
    """Fines spread across two different courts."""
    return [
        {
            "juzgado": "JUZGADO DE POLICIA LOCAL DE SANTIAGO",
            "rol": "123-2020",
            "fecha_ingreso": "15-03-2020",
        },
        {
            "juzgado": "TRIBUNAL DE ÑUÑOA",
            "rol": "789-2019",
            "fecha_ingreso": "22-11-2019",
        },
    ]


VALID_PDF_TEXT = """CERTIFICADO DE REGISTRO DE MULTAS DE TRANSITO NO PAGADAS

R.U.N. : 12.345.678-9
Nombre : JUAN PEREZ GONZALEZ

PLACA PATENTE: BBFC12

ID MULTA : 001
TRIBUNAL : JUZGADO DE POLICIA LOCAL DE SANTIAGO
ROL : 123-2020
FECHA INGRESO RMNP : 15-03-2020 00:00:00

ID MULTA : 002
TRIBUNAL : JUZGADO DE POLICIA LOCAL DE SANTIAGO
ROL : 456-2021
FECHA INGRESO RMNP : 10-06-2021 00:00:00
"""

VALID_PDF_TEXT_NO_PRESCRIBIBLE = """CERTIFICADO DE REGISTRO DE MULTAS DE TRANSITO NO PAGADAS

R.U.N. : 12.345.678-9
Nombre : MARIA LOPEZ SOTO

PLACA PATENTE: XYZW34

ID MULTA : 001
TRIBUNAL : JUZGADO DE POLICIA LOCAL DE PROVIDENCIA
ROL : 999-2025
FECHA INGRESO RMNP : 01-06-2025 00:00:00
"""

INVALID_PDF_TEXT = """ESTE ES UN DOCUMENTO CUALQUIERA
No tiene nada que ver con multas de tránsito.
"""
