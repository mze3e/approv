import argparse
import json
import sys

from postal.parser import parse_address


def _normalize_components(components):
    labeled = {}
    ordered = []
    for value, label in components:
        ordered.append({"label": label, "value": value})
        labeled.setdefault(label, []).append(value)
    return ordered, labeled


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Parse an address into components using libpostal."
    )
    parser.add_argument(
        "address",
        nargs="+",
        help="Address string to parse. Wrap in quotes for multi-word addresses.",
    )
    args = parser.parse_args(argv)
    address = " ".join(args.address).strip()
    if not address:
        parser.error("Address must not be empty.")

    components = parse_address(address)
    ordered, labeled = _normalize_components(components)
    payload = {
        "input": address,
        "components": ordered,
        "labels": labeled,
    }
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
