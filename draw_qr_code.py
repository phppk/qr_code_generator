from PIL import Image
from qr_code_calc import generate_qr_code_data
from variables import error_correction_level, version

# Size aus Version berechnet. Statisches Formular.
def matrix_size(v):
    return ((v - 1) * 4) + 21

# Leere Matrix zum Befüllen mit zu zeichnenden Bits.
def create_empty_matrix(size):
    return [[None for _ in range(size)] for _ in range(size)]


def set_module(matrix, function_modules, row, col, value):
    matrix[row][col] = value
    # Function Module sind protected und werden nicht ueberschrieben.
    function_modules.add((row, col))

# Schreiben der Finder-Pattern. 7x7 in den Ecken.
def draw_finder_with_separator(matrix, function_modules, top, left):
    finder = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    size = len(matrix)

    for d_row in range(7):
        for d_col in range(7):
            set_module(matrix, function_modules, top + d_row, left + d_col, finder[d_row][d_col])

    for d_row in range(-1, 8):
        for d_col in range(-1, 8):
            row = top + d_row
            col = left + d_col
            if not (0 <= row < size and 0 <= col < size):
                continue
            if d_row in (-1, 7) or d_col in (-1, 7):
                if (top <= row <= top + 6) and (left <= col <= left + 6):
                    continue
                set_module(matrix, function_modules, row, col, 1)

# Zeichnet das 5x5 Alignment Pattern (Unten Rechts)
def draw_alignment_pattern(matrix, function_modules, center_row, center_col):
    pattern = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    top = center_row - 2
    left = center_col - 2
    for d_row in range(5):
        for d_col in range(5):
            set_module(matrix, function_modules, top + d_row, left + d_col, pattern[d_row][d_col])

# Altering Pixel in einer Horizontalen und Vertikalen Linie zwischen den Finder Patterns.
def draw_timing_patterns(matrix, function_modules):
    size = len(matrix)
    for i in range(8, size - 8):
        value = i % 2
        set_module(matrix, function_modules, 6, i, value)
        set_module(matrix, function_modules, i, 6, value)

# Reservieren der Statischen Pattern damit diese nicht ersetzt werden.
def reserve_format_information_cells(matrix, function_modules):
    size = len(matrix)

    left_top_copy = [
        (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5),
        (8, 7), (8, 8), (7, 8),
        (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8),
    ]
    second_copy = [
        (size - 1, 8), (size - 2, 8), (size - 3, 8), (size - 4, 8),
        (size - 5, 8), (size - 6, 8), (size - 7, 8),
        (8, size - 8), (8, size - 7), (8, size - 6), (8, size - 5),
        (8, size - 4), (8, size - 3), (8, size - 2), (8, size - 1),
    ]

    for row, col in left_top_copy + second_copy:
        if matrix[row][col] is None:
            set_module(matrix, function_modules, row, col, 1)
        else:
            function_modules.add((row, col))

# statischer schwarzer Pixel.
def draw_dark_module(matrix, function_modules, v):
    row = 4 * v + 9
    col = 8
    set_module(matrix, function_modules, row, col, 0)

# Format Bits (Info bzgl. ECC Level und welche Maske genutzt wird.)
def create_format_bits(ecc_level, mask_pattern):
    ecc_map = {"L": 1, "M": 0, "Q": 3, "H": 2}
    if ecc_level not in ecc_map:
        raise ValueError(f"Unsupported ECC level: {ecc_level}")
    if not 0 <= mask_pattern <= 7:
        raise ValueError("Mask pattern must be in range 0..7.")

    data = (ecc_map[ecc_level] << 3) | mask_pattern
    shifted = data << 10
    generator = 0b10100110111

    for i in range(14, 9, -1):
        if (shifted >> i) & 1:
            shifted ^= generator << (i - 10)

    format_bits = (data << 10) | shifted
    format_bits ^= 0b101010000010010
    return format(format_bits, "015b")

# Format Info wird an Zwei stellen geschrieben, jeweils neben den Finder Patterns.
def write_format_information(matrix, ecc_level, mask_pattern):
    bits = create_format_bits(ecc_level, mask_pattern)
    size = len(matrix)

    left_top_copy = [
        (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5),
        (8, 7), (8, 8), (7, 8),
        (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8),
    ]
    second_copy = [
        (size - 1, 8), (size - 2, 8), (size - 3, 8), (size - 4, 8),
        (size - 5, 8), (size - 6, 8), (size - 7, 8),
        (8, size - 8), (8, size - 7), (8, size - 6), (8, size - 5),
        (8, size - 4), (8, size - 3), (8, size - 2), (8, size - 1),
    ]

    for i, (row, col) in enumerate(left_top_copy):
        matrix[row][col] = 0 if bits[i] == "1" else 1
    for i, (row, col) in enumerate(second_copy):
        matrix[row][col] = 0 if bits[i] == "1" else 1

# Berechnen der Masken selber - Je nachdem welche Maske genutzt wird.
# Returned eine Funktion um zu berechnen, welche Pixel XOR'd werden.
def mask_condition(mask, row, col):
    if mask == 0:
        return (row + col) % 2 == 0
    if mask == 1:
        return row % 2 == 0
    if mask == 2:
        return col % 3 == 0
    if mask == 3:
        return (row + col) % 3 == 0
    if mask == 4:
        return (row // 2 + col // 3) % 2 == 0
    if mask == 5:
        return ((row * col) % 2) + ((row * col) % 3) == 0
    if mask == 6:
        return (((row * col) % 2) + ((row * col) % 3)) % 2 == 0
    if mask == 7:
        return (((row + col) % 2) + ((row * col) % 3)) % 2 == 0
    raise ValueError("Mask pattern must be in range 0..7.")

# Schreiben der eigentlichen daten_bits die in qr_code_calc.py berechnet werden.
def place_data_bits(matrix, bitstream, function_modules):
    size = len(matrix)
    col = size - 1
    bit_index = 0
    direction_up = True
    data_positions = []

    while col > 0:
        if col == 6:
            col -= 1

        rows = range((size - 1), -1, -1) if direction_up else range(size)
        for row in rows:
            for current_col in (col, col - 1):
                # Statische Pattern werden geskippt. Diese sind in function_modules hinterlegt.
                if (row, current_col) in function_modules:
                    continue
                if bit_index < len(bitstream):
                    matrix[row][current_col] = 0 if bitstream[bit_index] == "1" else 1
                    bit_index += 1
                else:
                    matrix[row][current_col] = 1
                # Data_positions wird genutzt um anzuzeigen, welche bits datenbits sind.
                # So wird die Maske nur auf Datenbits angewendet und nicht auf statische Bits.
                data_positions.append((row, current_col))

        col -= 2
        # Direction muss bei jedem Durchlauf gewechselt werden.
        direction_up = not direction_up

    # Error Handling falls nicht alle Datenbits genutzt wurden.
    if bit_index != len(bitstream):
        raise ValueError(
            f"Bitstream not fully consumed. Used {bit_index} of {len(bitstream)} bits."
        )
    return data_positions


def apply_mask(matrix, data_positions, mask):
    for row, col in data_positions:
        if mask_condition(mask, row, col):
            # Bitwise XOR mit dem Masking Pattern.
            # Führt zu besserer Lesbarkeit fuer den Scanner.
            matrix[row][col] ^= 1

# Validieren der Matrix vor dem zeichnen.
def validate_matrix(matrix, expected_size):
    if len(matrix) != expected_size or any(len(row) != expected_size for row in matrix):
        raise ValueError(f"Matrix muss {expected_size}x{expected_size} groß sein.")

    missing = sum(1 for row in matrix for value in row if value is None)
    if missing != 0:
        raise ValueError(f"Matrix hat immernoch {missing} None Module.")


def render_matrix_to_png(matrix, output_path="qr_code.png", scale=10, quiet_zone=4):

    # quiet_zone ist die weiße Area außerhalb des eigentlich codes.
    # Genutzt, damit der scanner genau den code abgrenzen kann.

    # benutzten einen variablen scale multiplier, damit der qrcode keine 29x29 pixel klein ist.
    
    size = len(matrix)
    full_size = size + 2 * quiet_zone
    image = Image.new("1", (full_size * scale, full_size * scale), 1)

    for row in range(size):
        for col in range(size):
            value = matrix[row][col]
            pixel = 0 if value == 0 else 1
            top = (row + quiet_zone) * scale
            left = (col + quiet_zone) * scale
            for dy in range(scale):
                for d_col in range(scale):
                    image.putpixel((left + d_col, top + dy), pixel)

    image.save(output_path)


def build_qr_code_v3_l(mask_pattern=0, output_path="qr_code.png"):
    if version != 3:
        raise ValueError("Falsche Version des QR-Codes. Aktuell ist nur Version 3 in Scope.")
    if error_correction_level != "L":
        raise ValueError("Falsches Error Correction Level. Aktuell ist nur Level L in Scope.")

    size = matrix_size(version)
    matrix = create_empty_matrix(size)
    function_modules = set()

    # Finder (+ Seperator).
    # Oben Links
    draw_finder_with_separator(matrix, function_modules, 0, 0)
    # Unten Links
    draw_finder_with_separator(matrix, function_modules, 0, size - 7)
    # Oben Rechts
    draw_finder_with_separator(matrix, function_modules, size - 7, 0)

    # Alignemnt Pattern, Kleine Box Unten Rechts.
    draw_alignment_pattern(matrix, function_modules, 22, 22)
    draw_timing_patterns(matrix, function_modules)
    reserve_format_information_cells(matrix, function_modules)

    # Statischer schwarzer Pixel
    draw_dark_module(matrix, function_modules, version)

    bitstream = generate_qr_code_data()
    if len(bitstream) != 567:
        raise ValueError(f"Falsche Bit-String laenge. Sollte 567 sein. Ist: {len(bitstream)}.")

    data_positions = place_data_bits(matrix, bitstream, function_modules)
    apply_mask(matrix, data_positions, mask_pattern)
    write_format_information(matrix, error_correction_level, mask_pattern)
    draw_dark_module(matrix, function_modules, version)

    validate_matrix(matrix, size)
    render_matrix_to_png(matrix, output_path=output_path, scale=10, quiet_zone=4)
    return matrix


if __name__ == "__main__":
    build_qr_code_v3_l()