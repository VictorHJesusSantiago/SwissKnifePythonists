from __future__ import annotations

import re
from typing import Any, Callable

_DIGITS = re.compile(r"\d")


def mask_partial(value: str, keep_start: int = 2, keep_end: int = 2, mask_char: str = "*") -> str:
    text = str(value)
    if len(text) <= keep_start + keep_end:
        return mask_char * len(text)
    middle = mask_char * (len(text) - keep_start - keep_end)
    return f"{text[:keep_start]}{middle}{text[len(text) - keep_end:]}"


def mask_document(value: str) -> str:
    digits = _DIGITS.findall(str(value))
    if len(digits) < 4:
        return "*" * len(str(value))
    masked = ["*"] * len(digits)
    for index in range(max(0, len(digits) - 4), len(digits)):
        masked[index] = digits[index]
    result = list(str(value))
    digit_iter = iter(masked)
    for index, char in enumerate(result):
        if char.isdigit():
            result[index] = next(digit_iter)
    return "".join(result)


def mask_credit_card(value: str) -> str:
    digits = _DIGITS.findall(str(value))
    if len(digits) < 4:
        return "*" * len(str(value))
    return "**** **** **** " + "".join(digits[-4:])


MASKERS: dict[str, Callable[[str], str]] = {
    "partial": mask_partial,
    "document": mask_document,
    "credit_card": mask_credit_card,
    "full": lambda value: "*" * len(str(value)),
}


def apply_masking(rows: list[dict[str, Any]], rules: dict[str, str]) -> list[dict[str, Any]]:
    output = []
    for original in rows:
        row = dict(original)
        for column, rule in rules.items():
            if column not in row or row[column] is None:
                continue
            masker = MASKERS.get(rule)
            if masker is None:
                raise ValueError(f"Regra de mascaramento desconhecida: {rule}")
            row[column] = masker(str(row[column]))
        output.append(row)
    return output
