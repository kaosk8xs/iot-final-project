# List your names: 


def decode(payload):
    """
    Decode the payload buffer into a temperature value.

    This function returns the temperature value.
    """

    # print(f"payload: {payload}")
    # return None

    # Convert the payload to a string
    payload_str = ''.join([format(byte, '02x') for byte in payload])
    # print(f"Payload: {payload_str}")

    # Convert hex to binary first
    hex_value = ''.join(reversed([payload_str[i:i+2] for i in range(0, len(payload_str), 2)]))
    
    # Convert hex to binary
    binary_string = bin(int(hex_value, 16))[2:].zfill(32)


    # IEEE 754 format details
    sign_bit = int(binary_string[0])
    exponent_bits = binary_string[1:9]
    fraction_bits = binary_string[9:]

    # Calculate the actual values
    sign = (-1) ** sign_bit
    exponent = int(exponent_bits, 2) - 127
    fraction = 1 + sum(int(b) * 2 ** (-i) for i, b in enumerate(fraction_bits, start=1))

    # Calculate the floating point number
    float_value = sign * fraction * (2 ** exponent)
    sign_bit, exponent_bits, fraction_bits, float_value


    # Update this function to return the temperature value.
    return float_value
