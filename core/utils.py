""" Validation and Custom Error Handling Extraction """
def extract_error_message(detail):
    """
    Recursively extract the first error message from a DRF ValidationError detail.
    """
    if isinstance(detail, str):
        return detail
    elif isinstance(detail, list) and detail:
        return extract_error_message(detail[0])
    elif isinstance(detail, dict):
        for value in detail.values():
            return extract_error_message(value)
    elif hasattr(detail, 'detail'):
        return extract_error_message(detail.detail)
    return "Validation error"
