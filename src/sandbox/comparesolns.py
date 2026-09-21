import re
import sys
import numpy as np


def read_sol(filename):
    """
    Reads a .sol file of the form:
        x1 = 3.456
        x7 = -1.23
        ...
        END

    Variables with value 0 may be omitted.

    Returns:
        dict mapping variable index -> value
    """
    values = {}

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue
            if line == "END":
                break

            var, value = line.split("=")
            var = var.strip()
            value = float(value.strip())

            # Extract the index from x123
            idx = int(re.match(r"x(\d+)", var).group(1))
            values[idx] = value

    return values


def dict_to_array(d, n):
    """Convert a sparse dictionary to a dense NumPy array of length n."""
    x = np.zeros(n)
    for idx, value in d.items():
        x[idx - 1] = value  # x1 goes in position 0
    return x


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <a.sol> <b.sol>")
        sys.exit(1)

    a_dict = read_sol(sys.argv[1])
    b_dict = read_sol(sys.argv[2])

    # Dimension is the largest variable index appearing in either file
    n = max(max(a_dict.keys(), default=0), max(b_dict.keys(), default=0))

    a = dict_to_array(a_dict, n)
    b = dict_to_array(b_dict, n)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    distance = np.linalg.norm(a - b)

    print(f"vector from file {sys.argv[1]}:")
    print(a)
    print(f"norm: {norm_a}")

    print(f"vector from file {sys.argv[2]}:")
    print(b)
    print(f"norm: {norm_b}")

    print(f"Dimension: {n}")
    print(f"Euclidean distance: {distance}")
    print(f"Relative distance: {distance / norm_a}")


if __name__ == "__main__":
    main()