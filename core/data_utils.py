from pathlib import Path
import shutil


def data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"

def result_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "result"


def ensure_data_dir() -> Path:
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d

def ensure_result_dir() -> Path:
    d = result_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_data_path(name: str) -> Path:
    return ensure_data_dir() / name

def get_result_path(name: str) -> Path:
    return ensure_result_dir() / name


def copy_input_file(src: str) -> Path:
    ensure_data_dir()
    sp = Path(src)
    if not sp.exists():
        raise FileNotFoundError(src)
    dest = data_dir() / sp.name
    if sp.resolve() != dest.resolve():
        shutil.copy2(str(sp), str(dest))
    return dest
