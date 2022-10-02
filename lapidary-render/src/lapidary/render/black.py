from black import Mode, format_file_contents, TargetVersion, NothingChanged


def format_code(code: str) -> str:
    try:
        return format_file_contents(
            src_contents=code,
            fast=False,
            mode=Mode(target_versions={TargetVersion.PY39}),
        )
    except NothingChanged:
        return code
