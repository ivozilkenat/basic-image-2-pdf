import os

def is_valid_filename(filename):
    # Define invalid characters based on the operating system
    if os.name == 'nt':  # Windows
        invalid_chars = '<>:"/\\|?*'
        reserved_names = {"CON", "PRN", "AUX", "NUL"} | \
                         {f"COM{i}" for i in range(1, 10)} | \
                         {f"LPT{i}" for i in range(1, 10)}
    else:  # Unix/Linux/MacOS
        invalid_chars = '/'
        reserved_names = set()

    # Check for invalid characters
    if any(char in invalid_chars for char in filename):
        return False

    # Check for reserved names
    if filename in reserved_names:
        return False

    # Check for length (255 characters is a common limit)
    if not 0 < len(filename) <= 255:
        return False

    return True