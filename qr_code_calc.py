from variables import *

# Validieren..
input = "https://www.youtube.com/watch?v=QEqwf71CuQM"


def encodeToBinary(message):
    return "".join(format(ord(char), "08b") for char in message)

def mode_indicator():
    # Gibt den genutzten Datentyp zum speichern wieder.
    return mode


def char_count_indicator(message):
    # Gibt den Binary-String der Laenge des Input-Strings wieder.
    input_len = len(message)
    return format(input_len, f"0{char_count_indicator_len}b")

def req_bits():
    # Berechnet die Anzahl benoetigter Daten-Bits
    return total_nr_codewords * 8


def add_terminator(bin_string):
    # Terminator: bis zu 4 Null-Bits, aber niemals ueber die Data-Kapazitaet hinaus.
    req_bits_amount = req_bits()
    remaining = req_bits_amount - len(bin_string)
    if remaining < 0:
        raise ValueError("Input ist zu lang fuer Version 3-L im Byte-Mode.")
    terminator_len = min(4, remaining)
    return bin_string + ("0" * terminator_len)


def pad_to_byte_boundary(bin_string):
    # Mit 0 auffuellen bis die Bitlaenge ein Vielfaches von 8 ist.
    mod = len(bin_string) % 8
    if mod == 0:
        return bin_string
    return bin_string + ("0" * (8 - mod))

# 11101100 00010001 - Pad Bytes
# Werden benoetigt, sollte der Datenstring nicht den gesamten QR-Code fuellen.
def pad_bytes(bin_string):
    pad_patterns = ("11101100", "00010001")
    idx = 0
    while len(bin_string) < req_bits():
        bin_string += pad_patterns[idx % 2]
        idx += 1
    if len(bin_string) != req_bits():
        raise ValueError("Pad-Bytes konnten Datenkapazitaet nicht exakt fuellen.")
    return bin_string


def convert_to_byte_string(bin_string):
    #Validieren vom bin_string (muss 440 bits lang sein)
    if len(bin_string) != 440:
        raise ValueError("Bin_String falsch berechnet. Laenge ungleich 440 bits.")

    #Valider bin_string wird in data_bytes umgerechnet
    data_bytes = bytes(int(bin_string[i:i + 8], 2) for i in range(0, len(bin_string), 8))
    return data_bytes


def gf_mul(a, b, exp_table, log_table):
    if a == 0 or b == 0:
        return 0
    return exp_table[(log_table[a] + log_table[b]) % 255]


def build_gf_tables():
    exp_table = [0] * 512
    log_table = [0] * 256
    x = 1
    for i in range(255):
        exp_table[i] = x
        log_table[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        exp_table[i] = exp_table[i - 255]
    return exp_table, log_table


def rs_generator_poly(ec_len, exp_table, log_table):
    generator = [1]
    for i in range(ec_len):
        factor = [1, exp_table[i]]
        result = [0] * (len(generator) + 1)
        for gi, gv in enumerate(generator):
            result[gi] ^= gf_mul(gv, factor[0], exp_table, log_table)
            result[gi + 1] ^= gf_mul(gv, factor[1], exp_table, log_table)
        generator = result
    return generator


def generate_error_correction_bits(byte_string):
    ec_len = 15
    exp_table, log_table = build_gf_tables()
    generator = rs_generator_poly(ec_len, exp_table, log_table)

    # Polynom Division in Galois Field 256
    remainder = [0] * ec_len
    for data_byte in byte_string:
        factor = data_byte ^ remainder[0]
        remainder = remainder[1:] + [0]
        if factor != 0:
            for i in range(ec_len):
                remainder[i] ^= gf_mul(generator[i + 1], factor, exp_table, log_table)

    return "".join(f"{byte:08b}" for byte in remainder)

# Bei einem Version 3 QR-Code, 7 "Remainder Bits" (0) um QR Code zu fuellen.
def add_remainder_bits(bin_string):
    if len(bin_string) != 560:
        raise ValueError("Error Correction Bits (wahrscheinlich) Falsch gerechnet. Laenge ungleich 560 bits.")
    bin_string += "0000000"
    return bin_string

def generate_qr_code_data():
    part_1 = mode_indicator() + char_count_indicator(input) + encodeToBinary(input)
    part_2 = add_terminator(part_1)
    part_3 = pad_to_byte_boundary(part_2)
    part_4 = pad_bytes(part_3)
    qr_code_data = part_4 + generate_error_correction_bits(convert_to_byte_string(part_4))
    final_qr_code = add_remainder_bits(qr_code_data)
    return final_qr_code

if __name__ == "__main__":
    print(generate_qr_code_data())