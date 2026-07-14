from __future__ import annotations

from fastapi import FastAPI

from opscore import __version__

app = FastAPI(title="OPSCORE API", version=__version__)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "opscore", "version": __version__}


def main() -> None:
    import uvicorn

    uvicorn.run("opscore.api:app", host="127.0.0.1", port=8000)
