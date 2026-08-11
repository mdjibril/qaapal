import re

def sanitize_text_input(text, max_length=150):
    """
    Sanitizes standard text inputs (names, roles, etc.)
    - Trims leading/trailing whitespace
    - Enforces maximum length
    - Removes non-printable/control characters (except basic whitespace)
    """
    if not text:
        return ""
    
    # Remove non-printable characters (keep standard ASCII and basic unicode)
    # \x00-\x1F and \x7F are control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(text))
    
    text = text.strip()
    return text[:max_length]

def sanitize_notes_input(text, max_length=2000):
    """
    Sanitizes larger text areas (observation notes).
    - Trims leading/trailing whitespace
    - Enforces maximum length
    - Escapes critical XML-like tags to prevent prompt injection boundary breaking
    """
    if not text:
        return ""
    
    text = str(text).strip()
    
    # Prevent breaking out of our prompt injection XML delimiters
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    
    return text[:max_length]
