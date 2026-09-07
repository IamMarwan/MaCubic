"""Factory for selecting the configured multimodal vision provider."""

from app.core.settings import Settings, get_settings
from app.services.mock_vision_provider import MockVisionProvider
from app.services.openai_vision_provider import OpenAIVisionProvider
from app.services.vision_provider import VisionProvider


def create_vision_provider(
    settings: Settings | None = None,
) -> VisionProvider:
    """Create the vision provider selected in application settings."""
    active_settings = settings or get_settings()

    if active_settings.vision_provider == "mock":
        return MockVisionProvider()

    if active_settings.vision_provider == "openai":
        return OpenAIVisionProvider(active_settings)

    raise ValueError(
        f"Unsupported vision provider: {active_settings.vision_provider}"
    )