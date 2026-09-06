from __future__ import annotations

from abc import ABC, abstractmethod

from app.retrieval.models import (
    RetrievalQuery,
    RetrievalResult,
)


class Retriever(ABC):
    """
    Abstract interface for repository retrieval.
    """

    @abstractmethod
    def retrieve(
        self,
        query: RetrievalQuery,
    ) -> RetrievalResult:
        """
        Retrieve repository context for a query.
        """
        raise NotImplementedError
