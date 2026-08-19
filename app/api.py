"""HTTP entry point for the Financial News Morning Brief MVP."""

from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool

from app.batch_runs import BatchRun, get_batch_run, list_batch_runs
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
            "batch_run_id": payload["batch_run_id"],
            "article_count": payload["article_count"],
            "articles_file": payload["articles_path"].name,
            "report_file": payload["report_path"].name,
        }

    @app.get("/batch-runs", tags=["batch"])
    def batch_run_list(
        limit: int = Query(default=20, ge=1, le=100),
    ) -> dict[str, list[dict[str, object]]]:
        """Return recent batch execution records, newest first."""
        runs = list_batch_runs(limit=limit)
        return {"items": [asdict(run) for run in runs]}

    @app.get("/batch-runs/{batch_run_id}", tags=["batch"])
    def batch_run_detail(batch_run_id: int) -> dict[str, object]:
        """Return one batch execution record by ID."""
        run: BatchRun | None = get_batch_run(batch_run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="배치 실행 이력을 찾을 수 없습니다.",
            )
        return asdict(run)

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
