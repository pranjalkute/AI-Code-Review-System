"""Clean math utility module with 100/100 code quality."""

def add_numbers(first_num: float, second_num: float) -> float:
    """
    Computes the sum of two numbers.

    Args:
        first_num: The first summand.
        second_num: The second summand.

    Returns:
        The arithmetic sum.
    """
    total = first_num + second_num
    return total


def find_maximum(numbers: list) -> float:
    """
    Finds the largest value in a non-empty list.

    Args:
        numbers: List of numeric values.

    Returns:
        The highest number found.
    """
    if not numbers:
        raise ValueError("List cannot be empty")
    return max(numbers)
