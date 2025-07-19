import logging
from abc import ABC, abstractmethod

from briefex.core import Container

logger = logging.getLogger(__name__)


class Workflow(ABC):
    """Abstract base class for all workflows in the application.

    This class defines the common interface and functionality for all workflow
    implementations. Workflows represent high-level business processes that
    coordinate multiple components of the application.

    Attributes:
        c: Container instance providing access to application dependencies.
    """

    def __init__(self, container: Container) -> None:
        """Initialize the workflow with a dependency container.

        Args:
            container: Container instance with all required dependencies.
        """
        self.c = container

    @abstractmethod
    def run(self) -> None:
        """Execute the workflow.

        This method must be implemented by all concrete workflow classes to
        define the specific business logic of the workflow.
        """
        ...
