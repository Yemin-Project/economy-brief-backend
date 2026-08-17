"""HTTP entry point for the Financial News Morning Brief MVP."""

from dataclasses import asdict

from fastapi import FastAPI, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.main import BatchResult, StoredReport, read_latest_report, run_batch


def create_app() -> FastAPI:
    app = FastAPI(
        title="Financial News Morning Brief API",
        version="0.1.0",
        description="경제 뉴스 Morning Brief를 위한 로컬 API",
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        """Return a lightweight liveness response without calling external services."""
        return {"status": "ok"}

    @app.post("/batch/run", tags=["batch"], status_code=status.HTTP_201_CREATED)
    async def batch_run() -> dict[str, object]:
        """Generate one report and save its article and Markdown files locally."""
        try:
            result: BatchResult = await run_in_threadpool(run_batch)
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="뉴스 수집 또는 리포트 생성에 실패했습니다.",
            ) from error

        payload = asdict(result)
        return {
            "status": "completed",
            "article_count": payload["article_count"],
            "articles_file": payload["articles_path"].name,
            "report_file": payload["report_path"].name,
        }

    @app.get("/reports/latest", tags=["reports"])
    def latest_report() -> dict[str, str]:
        """Return the latest locally stored Markdown report for the frontend."""
        try:
            report: StoredReport = read_latest_report()
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="아직 생성된 리포트가 없습니다.",
            ) from error
        return asdict(report)

    return app


app = create_app()
