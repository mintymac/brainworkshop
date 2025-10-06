"""Statistics repository port interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IStatsRepository(ABC):
    """Interface for stats persistence.

    This port defines the contract for storing and retrieving
    session statistics, allowing the domain logic to be independent
    of the storage mechanism (files, database, cloud storage, etc.).
    """

    @abstractmethod
    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Save session statistics.

        Args:
            session_data: Dictionary containing session information including:
                - timestamp: Session completion time
                - mode: Game mode ID
                - n_back: N-back level
                - percent: Performance percentage
                - trial_data: Detailed trial-by-trial data

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def load_user_history(self, username: str) -> List[Dict[str, Any]]:
        """Load user's session history.

        Args:
            username: Username to load history for

        Returns:
            List of session records, each containing:
                [session_num, mode, n_back, percent, manual]
        """
        pass

    @abstractmethod
    def get_today_sessions(self, username: str) -> List[Dict[str, Any]]:
        """Get sessions for today only.

        Args:
            username: Username to load sessions for

        Returns:
            List of today's session records
        """
        pass

    @abstractmethod
    def clear_history(self, username: str) -> bool:
        """Clear all history for a user.

        Args:
            username: Username to clear history for

        Returns:
            True if successful, False otherwise
        """
        pass
