import re

class CMFDataSanitizer:
    """
    Filtro de privacidad para cumplimiento normativo CMF (Chile).
    Anonimiza RUTs y números de tarjetas/cuentas en trazas ISO 8583.
    """
    
    @staticmethod
    def sanitize_rut(text: str) -> str:
        # Detecta RUTs con o sin puntos y guión (ej: 12.345.678-K, 12345678-9)
        rut_pattern = r'\b(\d{1,2}\.?\d{3}\.?\d{3}-[\dkK])\b'
        return re.sub(rut_pattern, '[RUT_ANONIMIZADO_CMF]', text)

    @staticmethod
    def sanitize_pan(text: str) -> str:
        # Detecta números de tarjeta PAN (16 dígitos) o cuentas bancarias largas
        pan_pattern = r'\b(\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}|\d{10,18})\b'
        return re.sub(pan_pattern, '[PAN_CUENTA_ANONIMIZADA_CMF]', text)

    @classmethod
    def sanitize_log(cls, raw_log: str) -> str:
        """Aplica todas las reglas de sanitización a un log ISO 8583."""
        clean_text = cls.sanitize_rut(raw_log)
        clean_text = cls.sanitize_pan(clean_text)
        return clean_text

if __name__ == "__main__":
    test_log = "Error en ISO 8583 MTI 0200. RUT Cliente: 18.765.432-1, Tarjeta: 4509-1234-5678-9012. DE39=51"
    print("--- PRUEBA DE SANITIZACIÓN CMF ---")
    print("Original :", test_log)
    print("Sanitizado:", CMFDataSanitizer.sanitize_log(test_log))