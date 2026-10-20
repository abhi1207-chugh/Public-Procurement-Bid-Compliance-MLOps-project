from fastapi import FastAPI

from . import __version__
from .config import get_settings

app = FastAPI(title="Procurement Bid Compliance Screening", version=__version__)


@app.get("/health")
def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "llm_provider": s.llm_provider,
        "llm_model": s.llm_model,
    }
