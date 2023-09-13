def center_align_string(s, length):
    """
    Center aligns a string within a given length using spaces.
    
    Args:
    - s (str): The string to be center aligned.
    - length (int): The length within which the string should be centered.
    
    Returns:
    - str: A string of the specified length with the input string center aligned.
    """
    
    if len(s) >= length:
        return s[:length]
    
    # Calculate the spaces required on the left and right
    total_spaces = length - len(s)
    left_spaces = total_spaces // 2
    right_spaces = total_spaces - left_spaces
    
    if left_spaces != right_spaces:
        if left_spaces > right_spaces:
            right_spaces = left_spaces
        else:
            left_spaces = right_spaces

    # Return the center aligned string
    return ' ' * left_spaces + s + ' ' * right_spaces #U+2003	EM SPACE (mutton)

import math

def round_up_to_nearest_5(n):
    return math.ceil(n / 5) * 5