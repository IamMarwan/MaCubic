"""Convenient development server launcher."""

import uvicorn

from app.core.settings import get_settings


if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env.lower() == "development",
        log_level=settings.log_level.lower(),
    )
    