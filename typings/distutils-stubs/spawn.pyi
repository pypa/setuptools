def spawn(
    cmd: list[str],
    search_path: bool = True,
    verbose: bool = False,
    dry_run: bool = False,
) -> None: ...
def find_executable(executable: str, path: str | None = None) -> str | None: ...
