# BrainWorkshop - Modular Architecture Plan

## Current State
- Single file: `brainworkshop.py` (5,416 lines)
- All functionality in one module
- Tight coupling between UI and business logic

## Target Architecture

```
brainworkshop/
├── __init__.py
├── __main__.py              # Entry point (python -m brainworkshop)
├── core/
│   ├── __init__.py
│   ├── game.py              # Main game loop and session management
│   ├── stimulus.py          # Stimulus generation logic
│   └── scoring.py           # Scoring and match checking
├── models/
│   ├── __init__.py
│   ├── mode.py              # Mode class and game mode definitions
│   ├── stats.py             # Stats class and data structures
│   └── config.py            # Configuration data model
├── config/
│   ├── __init__.py
│   ├── parser.py            # Config file parsing
│   ├── defaults.py          # Default configuration
│   └── settings.py          # Settings management
├── ui/
│   ├── __init__.py
│   ├── window.py            # MyWindow class
│   ├── field.py             # Field class
│   ├── visual.py            # Visual class
│   ├── menus.py             # Menu hierarchy
│   ├── labels.py            # Label classes
│   └── geometry.py          # Window geometry helpers
├── audio/
│   ├── __init__.py
│   ├── player.py            # Audio playback management
│   └── resources.py         # Sound resource loading
├── stats/
│   ├── __init__.py
│   ├── tracker.py           # Statistics tracking
│   ├── persistence.py       # File I/O for stats
│   └── analysis.py          # Performance analysis
└── utils/
    ├── __init__.py
    ├── paths.py             # Path helpers
    └── debug.py             # Debug and error utilities
```

## Module Responsibilities

### `core/` - Game Logic (Platform Independent)
**Purpose**: Pure game logic with no UI dependencies
- Game session management
- Stimulus generation algorithms
- N-back matching logic
- Trial progression
- Jaeggi mode compliance

**Key Classes/Functions**:
- `new_session()`
- `end_session()`
- `update(dt)`
- `generate_stimulus()`
- `check_match()`
- `compute_bt_sequence()`

### `models/` - Data Models
**Purpose**: Data structures and business entities
- Mode configurations
- Statistics data structures
- Game state

**Key Classes**:
- `Mode` - Game mode definitions
- `Stats` - Performance tracking
- `Config` - Configuration object

### `config/` - Configuration Management
**Purpose**: Config file handling and settings
- Parse config.ini files
- Default configurations
- User preferences
- Platform-specific settings

**Key Functions**:
- `parse_config()`
- `load_last_user()`
- `save_last_user()`
- `rewrite_configfile()`

### `ui/` - Pyglet UI Layer
**Purpose**: All Pyglet-specific rendering and interaction
- Window management
- Visual rendering
- Menu system
- Event handling
- Label rendering

**Key Classes**:
- `MyWindow`
- `Field`
- `Visual`
- `Menu` hierarchy
- All label classes

### `audio/` - Audio Management
**Purpose**: Sound and music playback
- Resource loading
- Playback control
- Volume management

**Key Functions**:
- `play_music()`
- `play_applause()`
- `sound_stop()`
- `fade_out()`

### `stats/` - Statistics
**Purpose**: Performance tracking and persistence
- Session statistics
- History tracking
- File I/O
- Analysis and charts

**Key Classes**:
- `Stats` (if separated from models)
- `Graph`

### `utils/` - Utilities
**Purpose**: Cross-cutting concerns
- Path helpers
- Debug utilities
- Error handling

## Dependency Flow

```
┌─────────────────┐
│   __main__.py   │
└────────┬────────┘
         │
    ┌────▼─────┐
    │    ui/   │
    │  window  │
    └────┬─────┘
         │
    ┌────▼─────┐         ┌──────────┐
    │  core/   │────────▶│  models/ │
    │   game   │         └──────────┘
    └────┬─────┘
         │
    ┌────▼─────┐
    │  stats/  │
    └──────────┘
         │
    ┌────▼─────┐
    │ config/  │
    └──────────┘
```

## Migration Strategy

### Phase 1: Create Package Structure
1. Create directory structure
2. Add `__init__.py` files
3. Create `__main__.py` entry point

### Phase 2: Extract Models (Least Dependencies)
1. Extract `Mode` class → `models/mode.py`
2. Extract `Stats` class → `models/stats.py`
3. Extract `dotdict` → `models/config.py`

### Phase 3: Extract Utilities
1. Path helpers → `utils/paths.py`
2. Debug functions → `utils/debug.py`
3. Window geometry → `ui/geometry.py`

### Phase 4: Extract Configuration
1. Config parsing → `config/parser.py`
2. Default config → `config/defaults.py`
3. User settings → `config/settings.py`

### Phase 5: Extract Audio
1. Audio functions → `audio/player.py`
2. Resource loading → `audio/resources.py`

### Phase 6: Extract Stats
1. Stats tracking → `stats/tracker.py`
2. File I/O → `stats/persistence.py`
3. Graph → `stats/analysis.py`

### Phase 7: Extract Core Game Logic
1. Session management → `core/game.py`
2. Stimulus generation → `core/stimulus.py`
3. Scoring → `core/scoring.py`

### Phase 8: Extract UI (Last - Most Dependencies)
1. Window → `ui/window.py`
2. Field → `ui/field.py`
3. Visual → `ui/visual.py`
4. Menus → `ui/menus.py`
5. Labels → `ui/labels.py`

### Phase 9: Create Entry Point
1. Create `__main__.py`
2. Update imports
3. Test execution

## Benefits for Web App

### Separation of Concerns
- `core/` contains game logic usable by any frontend
- UI layer is pluggable (Pyglet now, web later)
- Easy to add REST API layer

### Testability
- Core game logic testable without UI
- Mock UI for integration tests
- Clear module boundaries

### Parallel Development
- Frontend team works on `ui/`
- Backend team works on `core/` and API
- Clear interfaces between modules

## Next Steps
1. Create directory structure
2. Begin with models extraction (cleanest dependencies)
3. Progressively move code maintaining tests
4. Update imports incrementally
5. Verify application runs after each module extraction
