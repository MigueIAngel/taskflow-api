from fastapi import FastAPI

app = FastAPI(
    title="TaskFlow API",
    description="Task management REST API with JWT authentication.",
    version="1.0.0",
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
