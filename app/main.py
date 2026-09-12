import shutil
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from starlette.background import BackgroundTask

from app.generator import generate_proxy_pdf


app = FastAPI(
    title="TCG Proxy Lab",
    description="Generate printable playtest proxies from Limitless-format decklists.",
    version="0.1.0",
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return Path(__file__).with_name("index.html").read_text(encoding="utf-8")


@app.post("/api/v1/proxies")
def create_proxies(
    decklist: str = Form(...),
    paper_size: str = Form("a4"),
) -> FileResponse:
    try:
        output_path, work_dir = generate_proxy_pdf(decklist, paper_size)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="Unable to resolve cards or generate the PDF") from error

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="playtest-proxies.pdf",
        background=BackgroundTask(shutil.rmtree, work_dir, ignore_errors=True),
    )
