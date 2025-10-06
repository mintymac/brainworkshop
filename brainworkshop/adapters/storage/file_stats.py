"""File-based statistics repository implementation.

This adapter implements the IStatsRepository interface using CSV files
for session data storage, matching the original BrainWorkshop format.
"""
from __future__ import annotations

import datetime
import pickle
from datetime import date
from pathlib import Path
from time import strftime
from typing import Any, Dict, List, Optional

from brainworkshop.ports.stats_repository import IStatsRepository


class FileStatsRepository(IStatsRepository):
    """File-based stats storage using CSV format.

    Implements statistics persistence using text files (stats.txt) and
    optional binary session logs (logfile.dat) for detailed trial data.

    Attributes:
        stats_file: Path to CSV stats file
        session_log_file: Path to binary session log file
        separator: Field separator character (tab or comma)
        rollover_hour: Hour when "today" rolls over (default 4 AM)
    """

    def __init__(
        self,
        stats_file: Path,
        session_log_file: Optional[Path] = None,
        separator: str = '\t',
        rollover_hour: int = 4
    ) -> None:
        """Initialize file stats repository.

        Args:
            stats_file: Path to stats CSV file
            session_log_file: Path to binary session log (optional)
            separator: Field separator (default tab)
            rollover_hour: Hour when day rolls over (default 4 AM)
        """
        self.stats_file = stats_file
        self.session_log_file = session_log_file
        self.separator = separator
        self.rollover_hour = rollover_hour

        # Ensure stats file exists
        if not self.stats_file.exists():
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            self.stats_file.touch()

    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Save session statistics to file.

        Args:
            session_data: Dictionary containing:
                - timestamp: Session time string
                - mode_short_name: Short mode name (e.g., 'D3B')
                - percent: Overall percentage
                - mode: Mode ID
                - n_back: N-back level
                - ticks_per_trial: Ticks per trial
                - num_trials: Number of trials
                - manual: Manual mode flag
                - session_number: Session number
                - category_percents: Dict of percentages by modality
                - session_time: Duration in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            sep = self.separator

            # Build CSV line matching original format
            outlist = [
                session_data.get('timestamp', strftime("%Y-%m-%d %H:%M:%S")),
                session_data.get('mode_short_name', ''),
                str(session_data.get('percent', 0)),
                str(session_data.get('mode', 0)),
                str(session_data.get('n_back', 0)),
                str(session_data.get('ticks_per_trial', 0)),
                str(session_data.get('num_trials', 0)),
                str(int(session_data.get('manual', False))),
                str(session_data.get('session_number', 0)),
            ]

            # Add category percentages (original has 15+ columns)
            category_percents = session_data.get('category_percents', {})
            for key in ['position1', 'audio', 'color', 'visvis', 'audiovis',
                       'arithmetic', 'image', 'visaudio', 'audio2',
                       'position2', 'position3', 'position4',
                       'vis1', 'vis2', 'vis3', 'vis4']:
                outlist.append(str(category_percents.get(key, 0)))

            # Add session time
            outlist.append(str(session_data.get('session_time', 0)))

            line = sep.join(outlist) + '\n'

            # Append to stats file
            with open(self.stats_file, 'a') as f:
                f.write(line)

            # Save detailed session log if configured
            if self.session_log_file and session_data.get('save_detailed', False):
                self._save_session_log(session_data)

            return True

        except Exception as e:
            # Log error but don't crash
            print(f"Error saving session: {e}")
            return False

    def _save_session_log(self, session_data: Dict[str, Any]) -> None:
        """Save detailed binary session log using pickle.

        Args:
            session_data: Full session data including trial details
        """
        try:
            with open(self.session_log_file, 'ab') as f:
                session = {
                    'summary': session_data.get('summary', []),
                    'cfg': session_data.get('cfg', {}),
                    'timestamp': session_data.get('timestamp', ''),
                    'mode': session_data.get('mode', 0),
                    'n': session_data.get('n_back', 0),
                    'manual': session_data.get('manual', False),
                    'trial_duration': session_data.get('trial_duration', 0.1),
                    'trials': session_data.get('num_trials', 0),
                    'session': session_data.get('trial_data', {}),
                }
                pickle.dump(session, f)
        except Exception as e:
            print(f"Error saving session log: {e}")

    def load_user_history(self, username: str = '') -> List[List[Any]]:
        """Load user's complete session history.

        Args:
            username: Username (not used in file-based storage)

        Returns:
            List of session records: [session_num, mode, n_back, percent, manual]
        """
        full_history = []

        if not self.stats_file.exists():
            return full_history

        try:
            with open(self.stats_file, 'r') as f:
                for line in f:
                    if not line or line == '\n':
                        continue
                    if not line[0].isdigit():
                        continue

                    # Parse line
                    separator = '\t' if '\t' in line else ','
                    fields = line.split(separator)

                    if len(fields) < 9:
                        continue

                    try:
                        session_number = int(fields[8])
                        mode = int(fields[3])
                        n_back = int(fields[4])
                        percent = int(fields[2])
                        manual = bool(int(fields[7]))

                        if manual:
                            session_number = 0

                        full_history.append([session_number, mode, n_back, percent, manual])
                    except (ValueError, IndexError):
                        continue

        except Exception as e:
            print(f"Error loading history: {e}")

        return full_history

    def get_today_sessions(self, username: str = '') -> List[List[Any]]:
        """Get sessions for today only.

        Args:
            username: Username (not used in file-based storage)

        Returns:
            List of today's session records
        """
        today_sessions = []

        if not self.stats_file.exists():
            return today_sessions

        try:
            today = date.today()
            yesterday = date.fromordinal(today.toordinal() - 1)

            with open(self.stats_file, 'r') as f:
                for line in f:
                    if not line or line == '\n':
                        continue
                    if not line[0].isdigit():
                        continue

                    try:
                        # Parse datestamp
                        datestamp = date(int(line[:4]), int(line[5:7]), int(line[8:10]))
                        hour = int(line[11:13])

                        # Check if "today" based on rollover hour
                        is_today = False
                        current_hour = int(strftime('%H'))

                        if current_hour < self.rollover_hour:
                            # Before rollover: include yesterday after rollover hour
                            if datestamp == today or \
                               (datestamp == yesterday and hour >= self.rollover_hour):
                                is_today = True
                        else:
                            # After rollover: only today after rollover hour
                            if datestamp == today and hour >= self.rollover_hour:
                                is_today = True

                        if is_today:
                            separator = '\t' if '\t' in line else ','
                            fields = line.split(separator)

                            if len(fields) < 9:
                                continue

                            session_number = int(fields[8])
                            mode = int(fields[3])
                            n_back = int(fields[4])
                            percent = int(fields[2])
                            manual = bool(int(fields[7]))

                            if manual:
                                session_number = 0

                            today_sessions.append([session_number, mode, n_back, percent, manual])

                    except (ValueError, IndexError):
                        continue

        except Exception as e:
            print(f"Error loading today's sessions: {e}")

        return today_sessions

    def clear_history(self, username: str = '') -> bool:
        """Clear all history by truncating the stats file.

        Args:
            username: Username (not used in file-based storage)

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.stats_file.exists():
                self.stats_file.unlink()
                self.stats_file.touch()

            if self.session_log_file and self.session_log_file.exists():
                self.session_log_file.unlink()

            return True
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False

    def get_session_count(self) -> int:
        """Get total number of sessions recorded.

        Returns:
            Number of sessions in stats file
        """
        if not self.stats_file.exists():
            return 0

        try:
            with open(self.stats_file, 'r') as f:
                return sum(1 for line in f if line and line[0].isdigit())
        except Exception:
            return 0
