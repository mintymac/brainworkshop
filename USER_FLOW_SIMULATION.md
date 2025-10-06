# User Flow Simulation - Modular Architecture

## Scenario: User Plays a Dual 2-Back Session

### Setup
- User: Alice
- Mode: Dual 2-Back (position + audio)
- Platform: Desktop (Pyglet)

---

## Flow 1: Starting a Session (Desktop)

### User Action: Clicks "Start Game"

```
┌─────────────────────────────────────────────────────────────┐
│ USER CLICKS "START GAME" BUTTON                             │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ adapters/desktop/window.py                                  │
│                                                              │
│ def on_key_press(symbol, modifiers):                        │
│     if symbol == key.S:  # Start                            │
│         app_controller.start_session(mode=DUAL_2BACK)       │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ application/game_controller.py                              │
│                                                              │
│ def start_session(self, mode: Mode):                        │
│     # Inject adapters (dependency injection)                │
│     renderer = PygletRenderer()                             │
│     audio = PygletAudioPlayer()                             │
│     stats_repo = FileStatsRepository()                      │
│                                                              │
│     self.session = GameSession(                             │
│         mode=mode,                                          │
│         renderer=renderer,                                  │
│         audio=audio,                                        │
│         stats_repo=stats_repo                               │
│     )                                                        │
│     self.session.initialize()                               │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ domain/game_session.py                                      │
│                                                              │
│ def initialize(self):                                       │
│     self.trial_number = 0                                   │
│     self.stimuli_history = []                               │
│     self.n_back = 2                                         │
│     self.generate_all_stimuli()  # Pre-generate sequence    │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ domain/stimulus_generator.py                                │
│                                                              │
│ def generate_sequence(trials=20, n_back=2):                 │
│     # Pure algorithm - no UI dependencies                   │
│     positions = [random.randint(0, 8) for _ in range(20)]   │
│     sounds = [random.choice(['c','h','k','l','q','r','s',   │
│               't']) for _ in range(20)]                     │
│     return [Stimulus(pos=p, sound=s)                        │
│             for p, s in zip(positions, sounds)]             │
└─────────────────────────────────────────────────────────────┘

✅ Session created, ready for Trial 1
```

---

## Flow 2: Trial 1 - Display Stimulus

### User Action: Game automatically shows first stimulus

```
┌─────────────────────────────────────────────────────────────┐
│ GAME LOOP TICK (every 100ms)                                │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ adapters/desktop/window.py                                  │
│                                                              │
│ def update(dt):                                             │
│     app_controller.update(dt)                               │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ application/game_controller.py                              │
│                                                              │
│ def update(self, dt):                                       │
│     if self.session.should_show_stimulus():                 │
│         self.session.show_next_stimulus()                   │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ domain/game_session.py                                      │
│                                                              │
│ def show_next_stimulus(self):                               │
│     stimulus = self.stimuli[self.trial_number]              │
│     # Stimulus(position=4, sound='k')                       │
│                                                              │
│     # Use injected adapters (polymorphism!)                 │
│     self.renderer.show_square(stimulus.position)            │
│     self.audio.play_sound(stimulus.sound)                   │
│                                                              │
│     self.trial_number += 1                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├──────────────────────┬────────────────────┐
                  ↓                      ↓                    ↓
┌──────────────────────────┐  ┌──────────────────────────────┐
│ adapters/desktop/        │  │ adapters/desktop/            │
│   pyglet_renderer.py     │  │   pyglet_audio.py            │
│                          │  │                              │
│ def show_square(pos):    │  │ def play_sound(sound):       │
│     # Calculate coords   │  │     player = Player()        │
│     x = POSITIONS[pos].x │  │     source = load(f'{sound}' │
│     y = POSITIONS[pos].y │  │              '.wav')         │
│                          │  │     player.queue(source)     │
│     # Draw with Pyglet   │  │     player.play()            │
│     sprite.position =    │  │                              │
│         (x, y)           │  │                              │
│     sprite.draw()        │  │                              │
└──────────────────────────┘  └──────────────────────────────┘

✅ User sees: White square at center position
✅ User hears: Sound "k" through speakers
```

---

## Flow 3: Trial 3 - User Responds to Match

### User Action: Presses 'A' key (audio match)

**Context**:
- Trial 1: position=4, sound='k'
- Trial 2: position=7, sound='l'
- Trial 3: position=2, sound='k' ← Matches Trial 1 sound!

```
┌─────────────────────────────────────────────────────────────┐
│ USER PRESSES 'A' KEY (audio input)                          │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ adapters/desktop/window.py                                  │
│                                                              │
│ def on_key_press(symbol, modifiers):                        │
│     if symbol == key.A:  # Audio match                      │
│         app_controller.handle_input('audio')                │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ application/game_controller.py                              │
│                                                              │
│ def handle_input(self, input_type: str):                    │
│     result = self.session.check_match(input_type)           │
│     self.show_feedback(result)                              │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ domain/match_checker.py                                     │
│                                                              │
│ def check_match(self, input_type: str) -> MatchResult:      │
│     current_trial = 3                                       │
│     n_back_trial = 3 - 2 = 1                                │
│                                                              │
│     current = self.stimuli[current_trial]                   │
│     # Stimulus(position=2, sound='k')                       │
│                                                              │
│     n_back = self.stimuli[n_back_trial]                     │
│     # Stimulus(position=4, sound='k')                       │
│                                                              │
│     if input_type == 'audio':                               │
│         is_match = (current.sound == n_back.sound)          │
│         # 'k' == 'k' → TRUE                                 │
│                                                              │
│     # Record result                                         │
│     self.inputs.append(Input(                               │
│         trial=current_trial,                                │
│         type='audio',                                       │
│         is_correct=is_match,                                │
│         response_time=time.time() - stimulus_time           │
│     ))                                                      │
│                                                              │
│     return MatchResult(correct=True, type='audio')          │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ adapters/desktop/pyglet_renderer.py                         │
│                                                              │
│ def show_feedback(result: MatchResult):                     │
│     if result.correct:                                      │
│         # Flash green border                                │
│         border.color = (0, 255, 0, 255)                     │
│         schedule_once(hide_border, 0.5)                     │
└─────────────────────────────────────────────────────────────┘

✅ User sees: Green flash (correct!)
✅ Score: Audio matches: 1/1 (100%)
```

---

## Flow 4: Session End - Save Statistics

### User Action: Completes 20 trials

```
┌─────────────────────────────────────────────────────────────┐
│ TRIAL 20 COMPLETED                                          │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ domain/game_session.py                                      │
│                                                              │
│ def check_if_session_complete(self):                        │
│     if self.trial_number >= self.total_trials:              │
│         stats = self.calculate_session_stats()              │
│         self.stats_repo.save_session(stats)                 │
│         return stats                                        │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ domain/match_checker.py                                     │
│                                                              │
│ def calculate_session_stats(self) -> SessionStats:          │
│     # Pure calculation - no I/O                             │
│     audio_correct = sum(1 for i in self.inputs              │
│                        if i.type=='audio' and i.is_correct) │
│     audio_total = sum(1 for i in self.inputs                │
│                      if i.type=='audio')                    │
│                                                              │
│     position_correct = sum(1 for i in self.inputs           │
│                           if i.type=='position' and         │
│                              i.is_correct)                  │
│     position_total = sum(1 for i in self.inputs             │
│                         if i.type=='position')              │
│                                                              │
│     return SessionStats(                                    │
│         mode=self.mode,                                     │
│         n_back=self.n_back,                                 │
│         audio_score=audio_correct/audio_total,              │
│         position_score=position_correct/position_total,     │
│         timestamp=datetime.now()                            │
│     )                                                       │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ adapters/storage/file_stats.py                              │
│                                                              │
│ def save_session(self, stats: SessionStats):                │
│     # Implementation detail: CSV file                       │
│     csv_line = (                                            │
│         f"{stats.timestamp},"                               │
│         f"{stats.mode},"                                    │
│         f"{stats.n_back},"                                  │
│         f"{stats.audio_score:.2f},"                         │
│         f"{stats.position_score:.2f}\n"                     │
│     )                                                       │
│                                                              │
│     stats_file = Path(DATA_DIR) / 'stats.txt'               │
│     with open(stats_file, 'a') as f:                        │
│         f.write(csv_line)                                   │
└─────────────────────────────────────────────────────────────┘

✅ Session saved to: data/stats.txt
✅ Results: Audio 85%, Position 90% → Overall 87.5%
```

---

## Same Flow with WEB Frontend (Future)

### Key Difference: Different Adapters, SAME Domain Logic!

```
┌─────────────────────────────────────────────────────────────┐
│ USER CLICKS "START GAME" BUTTON (in browser)                │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ Frontend (React)                                            │
│                                                              │
│ fetch('/api/session/start', {                               │
│     method: 'POST',                                         │
│     body: JSON.stringify({mode: 'DUAL_2BACK'})              │
│ })                                                          │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ adapters/web/api.py (FastAPI)                               │
│                                                              │
│ @app.post("/session/start")                                 │
│ async def start_session(mode: Mode):                        │
│     renderer = WebRenderer()  # ← Different adapter!        │
│     audio = WebAudioPlayer()  # ← Different adapter!        │
│     stats_repo = DatabaseStatsRepository()  # ← DB not file!│
│                                                              │
│     session = GameSession(  # ← SAME domain logic!          │
│         mode=mode,                                          │
│         renderer=renderer,                                  │
│         audio=audio,                                        │
│         stats_repo=stats_repo                               │
│     )                                                       │
│     sessions[session_id] = session                          │
│     return {"session_id": session_id}                       │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ domain/game_session.py                                      │
│                                                              │
│ ← IDENTICAL CODE AS DESKTOP VERSION                         │
│ ← No changes needed! Works with ANY adapter!                │
└─────────────────────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ adapters/web/web_renderer.py                                │
│                                                              │
│ def show_square(self, position: int):                       │
│     # Instead of drawing with Pyglet...                     │
│     # Return JSON for frontend to render                    │
│     self.pending_updates.append({                           │
│         "type": "show_square",                              │
│         "position": position,                               │
│         "timestamp": time.time()                            │
│     })                                                      │
└─────────────────────────────────────────────────────────────┘

✅ Frontend polls: GET /session/updates
✅ Receives: {"type": "show_square", "position": 4}
✅ React renders square at position 4
✅ Web Audio API plays sound 'k'
```

---

## Key Observations

### 1. **Domain Logic is Identical**
```python
# This code works for BOTH desktop and web:
domain/game_session.py
domain/stimulus_generator.py
domain/match_checker.py
```

### 2. **Adapters are Swappable**
```python
# Desktop
renderer = PygletRenderer()

# Web
renderer = WebRenderer()

# CLI (hypothetical)
renderer = TextRenderer()  # Prints to console

# All implement IRenderer interface!
```

### 3. **Easy to Test**
```python
# tests/test_game_session.py
def test_audio_match():
    renderer = MockRenderer()  # Test double
    audio = MockAudioPlayer()   # Test double

    session = GameSession(mode, renderer, audio)
    # Test pure logic without real UI!
```

### 4. **Clear Dependencies**
```
User Input
    ↓
Adapter (Pyglet or Web)
    ↓
Application Controller
    ↓
Domain (pure logic)
    ↓
Models (data structures)
```

---

## Comparison: Monolithic vs Modular

### Current Monolithic (brainworkshop.py)
```python
def show_stimulus():
    # Tightly coupled to Pyglet
    sprite.position = (x, y)
    sprite.draw()
    pyglet.media.load('k.wav').play()

    # Game logic mixed with rendering
    if check_match():
        # More Pyglet code
        ...
```

**Problem**: Cannot reuse logic for web app!

### Modular Architecture
```python
# domain/game_session.py (pure logic)
def show_stimulus(self):
    stimulus = self.get_next_stimulus()
    self.renderer.show(stimulus)  # ← Works with ANY renderer!

# adapters/desktop/pyglet_renderer.py
class PygletRenderer(IRenderer):
    def show(self, stimulus):
        sprite.position = (x, y)
        sprite.draw()

# adapters/web/web_renderer.py
class WebRenderer(IRenderer):
    def show(self, stimulus):
        return {"position": stimulus.position}  # JSON for frontend
```

**Solution**: Same logic, different frontends!

---

## User Experience: No Difference!

**Important**: Users see NO difference in the desktop app.

- Same gameplay
- Same visuals
- Same performance
- Same features

**But developers get**:
- Testable code
- Reusable logic
- Web app ready
- Clear structure

This is the power of clean architecture! 🎉
