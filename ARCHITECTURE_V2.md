# BrainWorkshop - Modular Architecture (Deep Analysis)

## Critical Question: What is the Core Domain?

For web app preparation, we need to answer: **What game logic can work with ANY frontend (desktop, web, mobile)?**

### Pure Game Logic (Platform Independent)
```python
# This should work identically whether it's:
# - Desktop Pyglet app
# - Web app (React + FastAPI)
# - Mobile app
# - Command-line version

class GameSession:
    """Core game session - no UI dependencies"""
    def start_session(n_back: int, mode: Mode) -> None
    def generate_next_stimulus() -> Stimulus
    def check_input(input_type: str, timestamp: float) -> MatchResult
    def end_session() -> SessionStats
```

### UI-Specific (Platform Dependent)
```python
# Desktop (Pyglet)
class PygletRenderer:
    def render_square(position: int) -> None
    def play_sound(sound: str) -> None

# Web (React + Web Audio API)
class WebRenderer:
    def render_square(position: int) -> JSON
    def play_sound(sound: str) -> AudioBuffer
```

## Architecture Option Analysis

### Option A: Traditional Layered (Current ARCHITECTURE.md)
```
core/ → models/ → config/ → ui/
```
**Pros**: Familiar, straightforward
**Cons**: Still couples game logic to specific implementations

### Option B: Hexagonal/Clean Architecture (RECOMMENDED)
```
domain/         # Pure game logic, zero dependencies
  ↓
ports/          # Interfaces (contracts)
  ↓
adapters/       # Implementations (Pyglet, Web, etc.)
```
**Pros**: Complete UI independence, testable, future-proof
**Cons**: More complex initially

### Option C: Feature Modules
```
game/ audio/ stats/ rendering/
```
**Pros**: Clear feature boundaries
**Cons**: Doesn't separate concerns well for multi-platform

## RECOMMENDED: Clean Hexagonal Architecture

```
brainworkshop/
│
├── domain/                    # PURE GAME LOGIC (no external deps)
│   ├── __init__.py
│   ├── game_session.py        # Session lifecycle and state
│   ├── stimulus_generator.py  # N-back stimulus generation
│   ├── match_checker.py       # Match validation and scoring
│   ├── mode_engine.py         # Mode logic and progression
│   └── jaeggi.py             # Jaeggi protocol compliance
│
├── models/                    # DATA STRUCTURES (pure Python)
│   ├── __init__.py
│   ├── mode.py               # Mode definition
│   ├── stimulus.py           # Stimulus data
│   ├── session_state.py      # Session state
│   ├── stats.py              # Statistics data
│   └── config.py             # Config model
│
├── ports/                     # INTERFACES (contracts)
│   ├── __init__.py
│   ├── renderer.py           # IRenderer interface
│   ├── audio_player.py       # IAudioPlayer interface
│   ├── input_handler.py      # IInputHandler interface
│   ├── stats_repository.py   # IStatsRepository interface
│   └── config_provider.py    # IConfigProvider interface
│
├── adapters/                  # IMPLEMENTATIONS
│   ├── __init__.py
│   │
│   ├── desktop/              # Desktop (Pyglet) implementation
│   │   ├── __init__.py
│   │   ├── pyglet_renderer.py    # Implements IRenderer
│   │   ├── pyglet_audio.py       # Implements IAudioPlayer
│   │   ├── pyglet_input.py       # Implements IInputHandler
│   │   ├── window.py             # Pyglet window management
│   │   └── menus.py              # Desktop menu system
│   │
│   ├── storage/              # Persistence implementations
│   │   ├── __init__.py
│   │   ├── file_stats.py         # File-based stats storage
│   │   ├── file_config.py        # INI config provider
│   │   └── pickle_sessions.py    # Session pickle storage
│   │
│   └── web/                  # Future web implementation
│       ├── __init__.py
│       ├── web_renderer.py       # JSON/WebSocket renderer
│       ├── web_audio.py          # Audio URLs/streaming
│       └── api_input.py          # REST API input handler
│
├── application/               # APPLICATION SERVICES (orchestration)
│   ├── __init__.py
│   ├── game_controller.py    # Orchestrates domain + adapters
│   ├── config_service.py     # Config management
│   └── stats_service.py      # Stats aggregation
│
├── utils/                     # UTILITIES
│   ├── __init__.py
│   ├── paths.py
│   └── debug.py
│
├── __init__.py
├── __main__.py               # Desktop entry point
└── api_main.py               # Future: Web API entry point
```

## How This Enables Web App

### Current Desktop Flow:
```
User Input → Pyglet Event → Game Logic → Pyglet Render
                    ↓
              All in one file
```

### Modular Desktop Flow:
```
User Input → PygletInput (adapter) → GameController (app)
    ↓
GameSession (domain) → generates stimulus
    ↓
PygletRenderer (adapter) → renders to screen
```

### Future Web Flow (SAME DOMAIN LOGIC):
```
HTTP Request → WebInputAdapter → GameController (app)
    ↓
GameSession (domain) → generates stimulus
    ↓
WebRenderer (adapter) → returns JSON
    ↓
Frontend (React) → renders in browser
```

## Key Interfaces (Ports)

### IRenderer (ports/renderer.py)
```python
from abc import ABC, abstractmethod

class IRenderer(ABC):
    """Interface for rendering stimuli to any display"""

    @abstractmethod
    def show_square(self, position: int, color: tuple) -> None:
        """Show visual square at grid position"""
        pass

    @abstractmethod
    def show_image(self, position: int, image_name: str) -> None:
        """Show image sprite at grid position"""
        pass

    @abstractmethod
    def clear_display(self) -> None:
        """Clear all visual stimuli"""
        pass
```

### IAudioPlayer (ports/audio_player.py)
```python
class IAudioPlayer(ABC):
    """Interface for playing audio stimuli"""

    @abstractmethod
    def play_sound(self, sound_name: str, channel: int = 1) -> None:
        """Play audio stimulus"""
        pass

    @abstractmethod
    def play_music(self, music_name: str, volume: float) -> None:
        """Play background music"""
        pass
```

### IStatsRepository (ports/stats_repository.py)
```python
class IStatsRepository(ABC):
    """Interface for stats persistence"""

    @abstractmethod
    def save_session(self, session_data: SessionStats) -> None:
        """Save session statistics"""
        pass

    @abstractmethod
    def load_user_history(self, username: str) -> list[SessionStats]:
        """Load user's session history"""
        pass
```

## Migration Benefits

### 1. Complete UI Independence
```python
# domain/game_session.py - works with ANY UI
class GameSession:
    def __init__(self, mode: Mode, renderer: IRenderer, audio: IAudioPlayer):
        self.mode = mode
        self.renderer = renderer  # Could be Pyglet OR Web OR CLI
        self.audio = audio        # Could be Pyglet OR Web Audio API
```

### 2. Easy Testing
```python
# tests/test_game_session.py
from domain.game_session import GameSession
from tests.mocks import MockRenderer, MockAudio

def test_dual_nback():
    renderer = MockRenderer()
    audio = MockAudio()
    session = GameSession(mode=Mode.DUAL_NBACK, renderer=renderer, audio=audio)

    session.generate_next_stimulus()
    assert renderer.last_position in range(9)
    assert audio.last_sound in ['c', 'h', 'k', 'l', 'q', 'r', 's', 't']
```

### 3. Parallel Development
- **Team A**: Works on domain/ and models/ (pure game logic)
- **Team B**: Works on adapters/web/ (REST API + React frontend)
- **Team C**: Maintains adapters/desktop/ (existing Pyglet app)

### 4. Multiple Frontends from Same Logic
```
domain/game_session.py (one implementation)
         ↓
    ┌────┴────┬────────┬────────┐
    ↓         ↓        ↓        ↓
Desktop    Web App   Mobile   CLI
(Pyglet)   (React)   (React   (Text)
                     Native)
```

## Dependency Rules

### Golden Rule: Dependencies point INWARD
```
adapters/ → depends on → ports/ → depends on → domain/
   (outer)                                       (inner)

domain/ → depends on → NOTHING (pure Python)
```

### What This Means:
- ✅ `domain/game_session.py` imports NOTHING external
- ✅ `ports/renderer.py` defines interface, no implementation
- ✅ `adapters/desktop/pyglet_renderer.py` imports Pyglet
- ❌ `domain/` NEVER imports Pyglet, Flask, or any framework

## Example: Game Session in New Architecture

### domain/game_session.py (Pure Logic)
```python
from models.mode import Mode
from models.stimulus import Stimulus
from ports.renderer import IRenderer
from ports.audio_player import IAudioPlayer

class GameSession:
    """Core game session - platform independent"""

    def __init__(self, mode: Mode, renderer: IRenderer, audio: IAudioPlayer):
        self.mode = mode
        self.renderer = renderer
        self.audio = audio
        self.trial_number = 0
        self.stimuli_history = []

    def generate_stimulus(self) -> Stimulus:
        """Generate next stimulus - pure logic"""
        # Generate position (0-8)
        position = self._calculate_position()

        # Generate sound
        sound = self._calculate_sound()

        stimulus = Stimulus(position=position, sound=sound)
        self.stimuli_history.append(stimulus)
        return stimulus

    def render_stimulus(self, stimulus: Stimulus) -> None:
        """Render using provided renderer (could be ANY renderer)"""
        self.renderer.show_square(stimulus.position, color=(255,255,255))
        self.audio.play_sound(stimulus.sound)

    def check_match(self, input_type: str) -> bool:
        """Check if input matches n-back stimulus"""
        if len(self.stimuli_history) < self.mode.n_back + 1:
            return False

        current = self.stimuli_history[-1]
        n_back = self.stimuli_history[-(self.mode.n_back + 1)]

        if input_type == 'position':
            return current.position == n_back.position
        elif input_type == 'audio':
            return current.sound == n_back.sound
```

### adapters/desktop/desktop_app.py (Pyglet Implementation)
```python
from domain.game_session import GameSession
from adapters.desktop.pyglet_renderer import PygletRenderer
from adapters.desktop.pyglet_audio import PygletAudioPlayer

class DesktopApp:
    """Desktop application using Pyglet"""

    def __init__(self):
        self.renderer = PygletRenderer()
        self.audio = PygletAudioPlayer()
        self.session = None

    def start_game(self, mode: Mode):
        """Start new game session"""
        self.session = GameSession(
            mode=mode,
            renderer=self.renderer,  # Inject Pyglet renderer
            audio=self.audio          # Inject Pyglet audio
        )

    def on_update(self, dt: float):
        """Pyglet update loop"""
        if self.session:
            stimulus = self.session.generate_stimulus()
            self.session.render_stimulus(stimulus)

    def on_key_press(self, symbol, modifiers):
        """Pyglet keyboard event"""
        if symbol == key.A:
            match = self.session.check_match('audio')
            # Handle match feedback
```

### adapters/web/api.py (Future Web Implementation)
```python
from fastapi import FastAPI
from domain.game_session import GameSession
from adapters.web.web_renderer import WebRenderer
from adapters.web.web_audio import WebAudioPlayer

app = FastAPI()
sessions = {}  # Session storage

@app.post("/session/start")
async def start_session(mode: Mode, user_id: str):
    """Start new web game session"""
    renderer = WebRenderer()
    audio = WebAudioPlayer()

    session = GameSession(
        mode=mode,
        renderer=renderer,  # Inject Web renderer
        audio=audio         # Inject Web audio
    )

    sessions[user_id] = session
    return {"status": "started", "session_id": user_id}

@app.get("/session/next")
async def next_stimulus(user_id: str):
    """Get next stimulus"""
    session = sessions[user_id]
    stimulus = session.generate_stimulus()

    return {
        "position": stimulus.position,
        "sound": stimulus.sound,
        "sound_url": f"/audio/{stimulus.sound}.wav"
    }

@app.post("/session/input")
async def check_input(user_id: str, input_type: str):
    """Check user input"""
    session = sessions[user_id]
    is_match = session.check_match(input_type)

    return {"is_match": is_match}
```

## Migration Plan (Revised)

### Phase 1: Create Structure (1 hour)
- Create all directories
- Create `__init__.py` files
- Create interface definitions in `ports/`

### Phase 2: Extract Models (30 min)
- Move `Mode` class → `models/mode.py`
- Move `Stats` class → `models/stats.py`
- Create `models/stimulus.py`, `models/session_state.py`

### Phase 3: Extract Domain Logic (2 hours)
- Extract session management → `domain/game_session.py`
- Extract stimulus generation → `domain/stimulus_generator.py`
- Extract scoring → `domain/match_checker.py`

### Phase 4: Create Adapters (1.5 hours)
- Implement `adapters/desktop/pyglet_renderer.py`
- Implement `adapters/desktop/pyglet_audio.py`
- Implement `adapters/storage/file_stats.py`
- Implement `adapters/storage/file_config.py`

### Phase 5: Wire Everything Together (1 hour)
- Update `__main__.py` to use new architecture
- Test desktop app still works
- Verify all functionality

**Total estimated time: 6 hours**

## Decision Point

This is a MUCH cleaner architecture for web app preparation, but requires more upfront work.

**Should we:**
1. ✅ Proceed with Clean Hexagonal Architecture (recommended for web)
2. ⚠️ Use simpler layered architecture from ARCHITECTURE.md (faster)
3. 🔬 Build small proof-of-concept first (1-2 modules only)
