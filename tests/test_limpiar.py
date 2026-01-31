"""Tests for limpiar_texto() and limpiar_juzgado()."""

from app import limpiar_texto, limpiar_juzgado


class TestLimpiarTexto:

    def test_removes_double_quotes(self):
        assert limpiar_texto('"JUAN"') == "JUAN"

    def test_removes_commas(self):
        assert limpiar_texto("PEREZ, JUAN") == "PEREZ JUAN"

    def test_strips_whitespace(self):
        assert limpiar_texto("  JUAN  ") == "JUAN"

    def test_uppercases(self):
        assert limpiar_texto("juan perez") == "JUAN PEREZ"

    def test_combined_cleaning(self):
        assert limpiar_texto('  "juan, perez"  ') == "JUAN PEREZ"

    def test_empty_string(self):
        assert limpiar_texto("") == ""

    def test_none_returns_empty(self):
        assert limpiar_texto(None) == ""

    def test_preserves_chilean_characters(self):
        result = limpiar_texto("ñuñoa")
        assert "Ñ" in result or "ñ" in result.lower()

    def test_accented_vowels(self):
        result = limpiar_texto("josé maría")
        assert result == "JOSÉ MARÍA"


class TestLimpiarJuzgado:

    def test_removes_juzgado_de_policia_local(self):
        result = limpiar_juzgado("JUZGADO DE POLICIA LOCAL DE SANTIAGO")
        assert "JUZGADO" not in result
        assert "POLICIA LOCAL" not in result
        assert "SANTIAGO" in result

    def test_removes_juzgado_policia_local_without_de(self):
        result = limpiar_juzgado("JUZGADO POLICIA LOCAL PROVIDENCIA")
        assert "JUZGADO" not in result
        assert "PROVIDENCIA" in result

    def test_removes_tribunal(self):
        result = limpiar_juzgado("TRIBUNAL DE ÑUÑOA")
        assert "TRIBUNAL" not in result
        assert "ÑUÑOA" in result or "ñuñoa" in result.lower()

    def test_uppercases_input(self):
        result = limpiar_juzgado("juzgado de policia local santiago")
        assert "JUZGADO" not in result
        assert "SANTIAGO" in result

    def test_preserves_remaining_text(self):
        result = limpiar_juzgado("JUZGADO DE POLICIA LOCAL DE LAS CONDES")
        assert "LAS CONDES" in result
