"""Statistics and session tracking models."""
from __future__ import annotations

import pickle
import datetime
from datetime import date
from pathlib import Path
from time import strftime
from typing import Any, Dict, List

# TODO: These dependencies need to be properly injected
# For now, this is extracted but not yet fully integrated


class Stats:
    """Session tracking and performance statistics manager.

    Manages all statistical data including session history, performance metrics,
    and user progress tracking. Handles parsing and writing of stats files,
    automatic level advancement/fallback, and session-by-session data recording.

    The stats system tracks performance both for today and across all time,
    supporting rollover hours for daily boundaries and maintaining detailed
    trial-by-trial data for research purposes.

    Attributes:
        session: Dict storing current session data by modality (position, audio, etc.)
            Each modality has arrays for stimuli, user inputs, and reaction times
        history: List of session records for today [session_num, mode, n_back, percent, manual]
        full_history: List of all session records across all time (same format as history)
        sessions_today: Count of completed sessions today
        time_today: Total play time today in seconds
        time_thours: Play time in the last T hours (configurable threshold)
        sessions_thours: Session count in the last T hours

    Methods:
        parse_statsfile(): Parse stats.txt and populate history/full_history
        retrieve_progress(): Determine current N-back level based on recent performance
        initialize_session(): Clear current session data structures
        save_input(): Record user input for current trial
        clear(): Reset all statistical data
    """
    def __init__(self) -> None:
        # set up data variables
        self.initialize_session()
        self.history: List = []
        self.full_history: List = [] # not just today
        self.sessions_today: int = 0
        self.time_today: int = 0
        self.time_thours: int = 0
        self.sessions_thours: int = 0

    def parse_statsfile(self, cfg: Any, mode: Any,
                       get_data_dir_func: Any,
                       debug_msg_func: Any,
                       quit_with_error_func: Any,
                       translation_func: Any = None) -> None:
        """Parse statistics file and load history.

        Args:
            cfg: Configuration object
            mode: Mode object
            get_data_dir_func: Function to get data directory
            debug_msg_func: Debug message function
            quit_with_error_func: Error handling function
            translation_func: Translation function (gettext)
        """
        _ = translation_func if translation_func else lambda x: x
        self.clear()
        statsfile_path = Path(get_data_dir_func()) / cfg.STATSFILE
        if statsfile_path.is_file():
            try:
                last_mode = 0
                last_back = 0
                is_today = False
                is_thours = False
                today = date.today()
                yesterday = date.fromordinal(today.toordinal() - 1)
                tomorrow = date.fromordinal(today.toordinal() + 1)
                with open(statsfile_path, 'r') as statsfile:
                    for line in statsfile:
                        if line == '': continue
                        if line == '\n': continue
                        if line[0] not in '0123456789': continue
                        datestamp = date(int(line[:4]), int(line[5:7]), int(line[8:10]))
                        hour = int(line[11:13])
                        mins = int(line[14:16])
                        sec = int(line[17:19])
                        thour = datetime.datetime.today().hour
                        tmin = datetime.datetime.today().minute
                        tsec = datetime.datetime.today().second
                        if int(strftime('%H')) < cfg.ROLLOVER_HOUR:
                            if datestamp == today or (datestamp == yesterday and hour >= cfg.ROLLOVER_HOUR):
                                is_today = True
                        elif datestamp == today and hour >= cfg.ROLLOVER_HOUR:
                            is_today = True
                        if datestamp == today or (datestamp == yesterday and (hour > thour or (hour == thour and (mins > tmin or (mins == tmin and sec > tsec))))):
                            is_thours = True
                        if '\t' in line:
                            separator = '\t'
                        else: separator = ','
                        newline = line.split(separator)
                        newmode = int(newline[3])
                        newback = int(newline[4])
                        newpercent = int(newline[2])
                        newmanual = bool(int(newline[7]))
                        newsession_number = int(newline[8])
                        try:
                            sesstime = int(round(float(newline[25])))
                        except Exception as e:
                            debug_msg_func(e)
                            # this session wasn't performed with this version of BW, and is therefore
                            # old, and therefore the session time doesn't matter
                            sesstime = 0
                        if newmanual:
                            newsession_number = 0
                        self.full_history.append([newsession_number, newmode, newback, newpercent, newmanual])
                        if is_thours:
                            self.sessions_thours += 1
                            self.time_thours += sesstime
                        if is_today:
                            self.sessions_today += 1
                            self.time_today += sesstime
                            self.history.append([newsession_number, newmode, newback, newpercent, newmanual])
                # Note: retrieve_progress() needs to be called separately with proper context

            except Exception as e:
                debug_msg_func(e)
                quit_with_error_func(_(f'Error parsing stats file\n{statsfile_path}'),
                                _('\nPlease fix, delete or rename the stats file.'),
                                quit=False)

    def retrieve_progress(self, cfg: Any, mode: Any,
                         default_nback_mode_func: Any,
                         get_threshold_advance_func: Any,
                         get_threshold_fallback_func: Any) -> tuple:
        """Determine current N-back level based on recent performance.

        Args:
            cfg: Configuration object
            mode: Mode object
            default_nback_mode_func: Function to get default n-back for mode
            get_threshold_advance_func: Function to get advancement threshold
            get_threshold_fallback_func: Function to get fallback threshold
        """
        if cfg.RESET_LEVEL:
            sessions = [s for s in self.history if s[1] == mode.mode]
        else:
            sessions = [s for s in self.full_history if s[1] == mode.mode]
        mode.enforce_standard_mode()
        if sessions:
            ls = sessions[-1]
            mode.back = ls[2]
            if ls[3] >= get_threshold_advance_func():
                mode.back += 1
            mode.session_number = ls[0]
            mode.progress = 0
            for s in sessions:
                if s[2] == mode.back and s[3] < get_threshold_fallback_func():
                    mode.progress += 1
                elif s[2] != mode.back:
                    mode.progress = 0
            if mode.progress >= cfg.THRESHOLD_FALLBACK_SESSIONS:
                mode.progress = 0
                mode.back -= 1
                if mode.back < 1:
                    mode.back = 1
        else: # no sessions today for this user and this mode
            mode.back = default_nback_mode_func(mode.mode)
        mode.num_trials_total = mode.num_trials + mode.num_trials_factor * mode.back ** mode.num_trials_exponent

    def initialize_session(self) -> None:
        """Initialize/clear current session data structures."""
        self.session: Dict[str, List] = {}
        for name in ('position1', 'position2', 'position3', 'position4',
             'vis1', 'vis2', 'vis3', 'vis4',
            'color', 'image', 'audio', 'audio2'
            ):
            self.session[name] = []
            self.session[f"{name}_input"] = []
            self.session[f"{name}_rt"] = [] # reaction times
        for name in ('vis', 'numbers', 'operation', 'visvis_input',
            'visaudio_input', 'audiovis_input', 'arithmetic_input', 'visvis_rt',
            'visaudio_rt', 'audiovis_rt' # , 'arithmetic_rt'
            ):
            self.session[name] = []

    def save_input(self, mode: Any, arithmetic_answer_label: Any = None) -> None:
        """Record user input for current trial.

        Args:
            mode: Mode object with current stimuli and inputs
            arithmetic_answer_label: Label object for arithmetic answer parsing (optional)
        """
        for k, v in mode.current_stim.items():
            if k == 'number':
                self.session['numbers'].append(v)
            else:
                self.session[k].append(v)
            if k == 'vis': # goes to both self.session['vis'] and ['image']
                self.session['image'].append(v)
        for k, v in mode.inputs.items():
            self.session[k + '_input'].append(v)
        for k, v in mode.input_rts.items():
            self.session[k + '_rt'].append(v)

        self.session['operation'].append(mode.current_operation)
        if arithmetic_answer_label:
            self.session['arithmetic_input'].append(arithmetic_answer_label.parse_answer())
        else:
            self.session['arithmetic_input'].append(0)


    def submit_session(self, percent: float, category_percents: Dict[str, float],
                      mode: Any, cfg: Any,
                      get_data_dir_func: Any,
                      debug_msg_func: Any,
                      quit_with_error_func: Any,
                      translation_func: Any = None,
                      # Optional callbacks for game logic
                      circles_update_callback: Any = None,
                      play_applause_callback: Any = None,
                      play_music_callback: Any = None,
                      congrats_label_update_callback: Any = None,
                      get_threshold_advance_func: Any = None,
                      get_threshold_fallback_func: Any = None,
                      attempt_to_save_stats: bool = True,
                      stats_separator: str = '\t') -> None:
        """Submit completed session and update statistics.

        This is a complex method that needs refactoring. Many dependencies
        are temporarily passed as callbacks.

        Args:
            percent: Overall session performance percentage
            category_percents: Dict of performance by modality
            mode: Mode object
            cfg: Configuration object
            get_data_dir_func: Function to get data directory
            debug_msg_func: Debug message function
            quit_with_error_func: Error handling function
            translation_func: Translation function (gettext)
            circles_update_callback: Optional callback to update circles UI
            play_applause_callback: Optional callback to play applause
            play_music_callback: Optional callback to play music
            congrats_label_update_callback: Optional callback to update congrats label
            get_threshold_advance_func: Function to get advancement threshold
            get_threshold_fallback_func: Function to get fallback threshold
            attempt_to_save_stats: Whether to save stats to file
            stats_separator: Separator character for stats file
        """
        _ = translation_func if translation_func else lambda x: x
        self.history.append([mode.session_number, mode.mode, mode.back, percent, mode.manual])

        if attempt_to_save_stats:
            try:
                sep = stats_separator
                statsfile_path = Path(get_data_dir_func()) / cfg.STATSFILE
                outlist = [strftime("%Y-%m-%d %H:%M:%S"),
                           mode.short_name(),
                           str(percent),
                           str(mode.mode),
                           str(mode.back),
                           str(mode.ticks_per_trial),
                           str(mode.num_trials_total),
                           str(int(mode.manual)),
                           str(mode.session_number),
                           str(category_percents['position1']),
                           str(category_percents['audio']),
                           str(category_percents['color']),
                           str(category_percents['visvis']),
                           str(category_percents['audiovis']),
                           str(category_percents['arithmetic']),
                           str(category_percents['image']),
                           str(category_percents['visaudio']),
                           str(category_percents['audio2']),
                           str(category_percents['position2']),
                           str(category_percents['position3']),
                           str(category_percents['position4']),
                           str(category_percents['vis1']),
                           str(category_percents['vis2']),
                           str(category_percents['vis3']),
                           str(category_percents['vis4']),
                           str(round(mode.num_trials_total * mode.ticks_per_trial * 0.1))]
                line = sep.join(outlist) + '\n'

                with open(statsfile_path, 'a') as statsfile:
                    statsfile.write(line)

                if cfg.SAVE_SESSIONS:
                    with open(Path(get_data_dir_func()) / cfg.SESSION_STATS, 'ab') as picklefile:
                        session = {} # it's not a dotdict because we want to pickle it
                        session['summary'] = outlist # that's what goes into stats.txt
                        session['cfg'] = cfg.__dict__ if hasattr(cfg, '__dict__') else dict(cfg)
                        session['timestamp'] = strftime("%Y-%m-%d %H:%M:%S")
                        session['mode']   = mode.mode
                        session['n']      = mode.back
                        session['manual'] = mode.manual
                        session['trial_duration'] = mode.ticks_per_trial * 0.1  # TICK_DURATION
                        session['trials']  = mode.num_trials_total
                        session['session'] = self.session
                        pickle.dump(session, picklefile)
            except Exception as e:
                debug_msg_func(e)
                quit_with_error_func(_(f'Error writing to stats file\n{statsfile_path}'),
                                _('\nPlease check file and directory permissions.'))

        # Game logic - level advancement/fallback
        perfect = awesome = great = good = advance = fallback = False

        if not mode.manual and get_threshold_advance_func and get_threshold_fallback_func:
            if percent >= get_threshold_advance_func():
                mode.back += 1
                mode.num_trials_total = (mode.num_trials +
                    mode.num_trials_factor * mode.back ** mode.num_trials_exponent)
                mode.progress = 0
                if circles_update_callback:
                    circles_update_callback()
                if cfg.USE_APPLAUSE and play_applause_callback:
                    play_applause_callback()
                advance = True
            elif mode.back > 1 and percent < get_threshold_fallback_func():
                if cfg.JAEGGI_MODE:
                    mode.back -= 1
                    fallback = True
                else:
                    if mode.progress == cfg.THRESHOLD_FALLBACK_SESSIONS - 1:
                        mode.back -= 1
                        mode.num_trials_total = mode.num_trials + mode.num_trials_factor * mode.back ** mode.num_trials_exponent
                        fallback = True
                        mode.progress = 0
                        if circles_update_callback:
                            circles_update_callback()
                    else:
                        mode.progress += 1
                        if circles_update_callback:
                            circles_update_callback()

            if percent == 100: perfect = True
            elif percent >= get_threshold_advance_func(): awesome = True
            elif percent >= (get_threshold_advance_func() + get_threshold_fallback_func()) // 2: great = True
            elif percent >= get_threshold_fallback_func(): good = True

            if congrats_label_update_callback:
                congrats_label_update_callback(True, advance, fallback, awesome, great, good, perfect)

        if mode.manual and not cfg.USE_MUSIC_MANUAL:
            return

        if cfg.USE_MUSIC and play_music_callback:
            play_music_callback(percent)

    def clear(self) -> None:
        """Reset all statistical data."""
        self.history = []
        self.sessions_today = 0
        self.time_today = 0
        self.sessions_thours = 0
        self.time_thours = 0
