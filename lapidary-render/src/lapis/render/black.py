from black import Mode, format_file_contents


def format_code(code: str) -> str:
    return format_file_contents(
        src_contents=code,
        fast=False,
        mode=Mode(),
    )
