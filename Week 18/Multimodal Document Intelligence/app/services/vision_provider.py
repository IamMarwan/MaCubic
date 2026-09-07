"""Common interface implemented by multimodal vision providers."""

from abc import ABC, abstractmethod

from app.models.schemas import ExtractedItem
from app.services.pdf_processor import ProcessedPage


class VisionProvider(ABC):
    """Interface for visual document-analysis providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""

    @abstractmethod
    async def analyze_page(
        self,
        page: ProcessedPage,
    ) -> list[ExtractedItem]:
        """Analyze one rendered document page."""