# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BrainWorkshop is a Python-based brain training application implementing the Dual N-Back cognitive exercise. This is a fork of the original BrainWorkshop that adds Python 3 compatibility while maintaining Python 2 support. The project is a single-file application (~4900 lines) built on Pyglet for cross-platform GUI and audio support.

## Development Commands

### Running the Application
```bash
python brainworkshop.py
```

### Building Executable (Windows)
```bash
./tools/freeze.bat  # Windows
./tools/freeze.sh   # Unix/Linux/Mac
```

### Dependencies
```bash
pip install -r requirements.txt  # Installs pyglet>=2
```

### Debug Mode
```bash
python brainworkshop.py --debug  # Enables debug output
```

### Command Line Options
- `--configfile <path>` - Specify custom config file
- `--statsfile <path>` - Specify custom stats file  
- `--datadir <path>` - Specify data directory
- `--resdir <path>` - Specify resources directory
- `--novbo` - Disable vertex buffer objects (for old graphics cards)

## High-Level Architecture

### Single-File Design
The entire application is contained in `brainworkshop.py` with logical separation of concerns:

**Core Components:**
- `MyWindow` class - Main window extending pyglet.window.Window
- `Mode` class - Game mode definitions and parameters (15+ variants)
- `Stats` class - Session tracking and performance analysis
- `Menu` hierarchy - Navigation system with keyboard controls
- `Visual` class - Stimulus display and animations
- `Field` class - Game area with responsive scaling

### Configuration System
- `cfg` global object using ConfigParser for `config.ini` files
- User-specific config files: `{username}-config.ini`
- Default configuration embedded as `CONFIGFILE_DEFAULT_CONTENTS`
- Platform-specific settings paths via `get_settings_path()`

### Game Flow Architecture
1. **Session Initialization** - `new_session()` sets up trials and stimuli
2. **Game Loop** - `update(dt)` runs at 10Hz managing trial progression  
3. **Stimulus Generation** - Randomized patterns with N-back matching logic
4. **Session End** - `end_session()` saves stats and handles level progression

### Data Storage
- Text-based stats in `stats.txt` (CSV format)
- Binary session data in `logfile.dat` for research/clinical use
- Configuration files in platform-specific user directories
- User progress tracking with automatic level adjustment

## Game Modes System

The application supports 15+ brain training modes:
- **Dual N-Back** - Position + Audio (default research protocol)  
- **Triple/Quad N-Back** - Additional color/image modalities
- **Arithmetic N-Back** - Mathematical operations with N-back memory
- **Combination modes** - Cross-modal matching tasks
- **Variable N-Back** - Dynamic difficulty within sessions
- **Crab modes** - Reverse stimulus ordering
- **Multi-stimulus** - Multiple simultaneous objects

Each mode is defined by:
- Modalities list (position, audio, color, image, arithmetic)
- Default parameters (n-back level, trials, timing)
- Scoring and progression rules

## Resource Management

### Directory Structure
- `res/` - All game resources
  - `sounds/` - Audio sets (letters, numbers, nato, morse, etc.)
  - `sprites/` - Visual stimulus sets  
  - `music/` - Background music by performance level
  - `i18n/` - Translation files
- `data/` - User data and statistics
- `tools/` - Build scripts and utilities

### Adding Content
- **Sound sets**: Create subfolder in `res/sounds/` with 8+ audio files
- **Image sets**: Create subfolder in `res/sprites/` with 8+ PNG files  
- **Music**: Add files to `res/music/{advance|good|great}/`

## Key Development Patterns

### Configuration-Driven Behavior
Most game behavior is controlled through config files rather than code changes. Important settings:
- Game mode defaults and timing
- Visual appearance (colors, fonts, scaling)
- Audio preferences and channel selection
- Research protocol compliance (Jaeggi mode)

### Responsive Scaling
All UI elements scale based on window size using:
- `from_width_center()` - Position calculations
- `calc_fontsize()` - Dynamic font sizing
- Percentage-based positioning throughout

### Event-Driven Menu System
Navigation uses pyglet event handlers with:
- Menu stack management (push/pop handlers)
- Keyboard-only controls for accessibility
- Dynamic value cycling with `Cycler` classes

## Clinical/Research Features

The application includes research-grade features:
- **Clinical Mode** - Minimal UI with tamper-resistant data logging
- **Jaeggi Protocol** - Exact replication of original study parameters
- **Session Data Export** - Detailed trial-by-trial analysis
- **Binary Logging** - Secure data storage for research use

## Platform Compatibility

Designed for cross-platform deployment:
- Python 2.7 and 3.x compatibility using `__future__` imports
- Pyglet for OpenGL graphics and audio across Windows/Mac/Linux
- Platform-specific configuration paths and file handling
- Executable generation via cx_Freeze

## Important Files

- `brainworkshop.py` - Main application (all functionality)
- `requirements.txt` - Python dependencies  
- `config.ini` - User configuration (auto-generated)
- `data/stats.txt` - Session statistics
- `tools/freeze.sh|.bat` - Build executable
- `Readme-instructions.txt` - Game tutorial and modes explanation
- `Readme-resources.txt` - Resource customization guide