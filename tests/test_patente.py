"""Tests for buscar_patente_universal() — license plate extraction."""

from app import buscar_patente_universal


class TestBuscarPatenteUniversal:
    """Tests for the three regex strategies used to find plates."""

    # --- Strategy 1: Explicit label (PLACA/PATENTE/PPU) ---

    def test_placa_patente_label_new_format(self):
        text = "PLACA PATENTE: BBFC12 algo más"
        assert buscar_patente_universal(text) == "BBFC12"

    def test_ppu_label_with_dash(self):
        text = "PPU: BBFC-12 resto del texto"
        assert buscar_patente_universal(text) == "BBFC12"

    def test_patente_label_old_format(self):
        text = "PATENTE AB-1234 info"
        assert buscar_patente_universal(text) == "AB1234"

    def test_placa_label_with_dots_not_handled(self):
        """BUG: label regex does not handle dots between letter groups (BB.FC.12).
        The regex expects the plate as a contiguous alphanumeric group after the label.
        This test documents the current (broken) behavior."""
        text = "PLACA PATENTE BB.FC.12 datos"
        assert buscar_patente_universal(text) == "NO_DETECTADA"

    def test_placa_label_with_spaces_not_handled(self):
        """BUG: label regex does not handle spaces between letter groups (BB FC 12).
        This test documents the current (broken) behavior."""
        text = "PLACA PATENTE: BB FC 12 datos"
        assert buscar_patente_universal(text) == "NO_DETECTADA"

    # --- Strategy 2: Free search — New format (4 consonants + 2 digits) ---

    def test_new_format_plain(self):
        text = "BBFC12 " + "x" * 1000
        assert buscar_patente_universal(text) == "BBFC12"

    def test_new_format_with_dash(self):
        text = "DRTV-99 " + "x" * 1000
        assert buscar_patente_universal(text) == "DRTV99"

    def test_new_format_with_dot(self):
        text = "DRTV.99 " + "x" * 1000
        assert buscar_patente_universal(text) == "DRTV99"

    # --- Strategy 3: Free search — Old format (2 letters + 4 digits) ---

    def test_old_format_plain(self):
        text = "AB1234 " + "x" * 1000
        assert buscar_patente_universal(text) == "AB1234"

    def test_old_format_with_dash(self):
        text = "ZZ-0001 " + "x" * 1000
        assert buscar_patente_universal(text) == "ZZ0001"

    # --- No match ---

    def test_no_plate_returns_no_detectada(self):
        text = "Este texto no tiene patente " + "x" * 1000
        assert buscar_patente_universal(text) == "NO_DETECTADA"

    def test_empty_string(self):
        assert buscar_patente_universal("") == "NO_DETECTADA"

    # --- Searches only in first 1000 chars for free search strategies ---

    def test_plate_beyond_header_not_found_by_free_search(self):
        """Free-search strategies only look in the first 1000 chars."""
        text = "x" * 1001 + "BBFC12"
        # No label strategy match either (no PLACA/PATENTE/PPU keyword)
        assert buscar_patente_universal(text) == "NO_DETECTADA"

    def test_label_strategy_works_beyond_1000_chars(self):
        """Label-based strategy searches the full text."""
        text = "x" * 1500 + " PLACA PATENTE: BBFC12 más datos"
        assert buscar_patente_universal(text) == "BBFC12"

    # --- Priority: label match beats free search ---

    def test_label_match_takes_priority(self):
        """When both label and free search could match, label should win."""
        text = "PLACA PATENTE: DRTV99 " + "x" * 500 + " AB1234"
        assert buscar_patente_universal(text) == "DRTV99"
