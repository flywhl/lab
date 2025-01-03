from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    root: Path = Path(__file__).parent.parent  # @bug: this won't work when installed
    spec_root: Path = root / "spec"
