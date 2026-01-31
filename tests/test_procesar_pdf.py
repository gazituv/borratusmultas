"""Tests for procesar_pdf() — PDF text extraction and fine parsing."""

from unittest.mock import patch, MagicMock
from io import BytesIO

from freezegun import freeze_time

from app import procesar_pdf
from tests.conftest import (
    VALID_PDF_TEXT,
    VALID_PDF_TEXT_NO_PRESCRIBIBLE,
    INVALID_PDF_TEXT,
)


def _mock_pdf_open(text):
    """Create a mock for pdfplumber.open that returns the given text."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = text

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = lambda self: self
    mock_pdf.__exit__ = MagicMock(return_value=False)

    return mock_pdf


class TestProcesarPdfValidDocument:
    """Tests with a well-formed certificate."""

    @freeze_time("2026-01-31")
    @patch("app.pdfplumber.open")
    def test_extracts_patente(self, mock_open):
        mock_open.return_value = _mock_pdf_open(VALID_PDF_TEXT)
        datos, multas = procesar_pdf(BytesIO(b"fake"))
        assert datos is not None
        assert datos["patente"] == "BBFC12"

    @freeze_time("2026-01-31")
    @patch("app.pdfplumber.open")
    def test_extracts_rut(self, mock_open):
        mock_open.return_value = _mock_pdf_open(VALID_PDF_TEXT)
        datos, _ = procesar_pdf(BytesIO(b"fake"))
        assert "12.345.678-9" in datos["rut"]

    @freeze_time("2026-01-31")
    @patch("app.pdfplumber.open")
    def test_extracts_nombre(self, mock_open):
        mock_open.return_value = _mock_pdf_open(VALID_PDF_TEXT)
        datos, _ = procesar_pdf(BytesIO(b"fake"))
        assert "JUAN" in datos["nombre"]
        assert "PEREZ" in datos["nombre"]

    @freeze_time("2026-01-31")
    @patch("app.pdfplumber.open")
    def test_finds_prescribible_fines(self, mock_open):
        mock_open.return_value = _mock_pdf_open(VALID_PDF_TEXT)
        _, multas = procesar_pdf(BytesIO(b"fake"))
        assert len(multas) == 2
        roles = {m["rol"] for m in multas}
        assert "123-2020" in roles
        assert "456-2021" in roles

    @freeze_time("2026-01-31")
    @patch("app.pdfplumber.open")
    def test_fine_has_required_keys(self, mock_open):
        mock_open.return_value = _mock_pdf_open(VALID_PDF_TEXT)
        _, multas = procesar_pdf(BytesIO(b"fake"))
        for multa in multas:
            assert "juzgado" in multa
            assert "rol" in multa
            assert "fecha_ingreso" in multa


class TestProcesarPdfNoFinesPrescribible:
    """All fines are too recent — none should be returned."""

    @freeze_time("2026-01-31")
    @patch("app.pdfplumber.open")
    def test_returns_empty_list_when_no_prescribible(self, mock_open):
        mock_open.return_value = _mock_pdf_open(VALID_PDF_TEXT_NO_PRESCRIBIBLE)
        datos, multas = procesar_pdf(BytesIO(b"fake"))
        assert datos is not None
        assert multas == []


class TestProcesarPdfInvalidDocument:
    """Document that is not a traffic fines certificate."""

    @patch("app.pdfplumber.open")
    def test_returns_none_for_invalid_document(self, mock_open):
        mock_open.return_value = _mock_pdf_open(INVALID_PDF_TEXT)
        datos, multas = procesar_pdf(BytesIO(b"fake"))
        assert datos is None
        assert multas is None


class TestProcesarPdfErrorHandling:
    """Verify graceful failure when pdfplumber throws."""

    @patch("app.pdfplumber.open", side_effect=Exception("corrupt file"))
    def test_returns_none_on_exception(self, mock_open):
        datos, multas = procesar_pdf(BytesIO(b"fake"))
        assert datos is None
        assert multas is None
