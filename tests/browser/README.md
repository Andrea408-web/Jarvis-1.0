# Optional browser integration checks

These checks require Python Playwright, `/usr/bin/chromium`, local sockets and, for the product check, `ffprobe` and `ffmpeg`. They are development-only requirements, not application dependencies. No actual user microphone, cloud credentials or model weights are used.

From the repository root:

```
python tests/browser/voice.py
python tests/browser/conversation.py
python tests/browser/product.py
python tests/browser/navigation.py
```

Voice generation and PCM decoding are real, with system voices prohibited. Conversation recognition and microphone input are simulated; synthesized double-clap audio is passed through the actual detector. Local language-model outputs are controlled fixtures. The product check uploads a generated product image through the normal dispatch path, exports actual video with the real bundled narration, and probes both encoded tracks. It does not verify native macOS Vision, Safari or a physical microphone. Generated outputs live in `/tmp`.

The navigation check verifies the narrow mobile layout, Germany filter, sports source links, explicit camera capture to an agent preview and camera-stream cleanup. Provider websites are not live-tested.

Additional checks:

```
python tests/browser/astra.py
python tests/browser/voice_cancellation.py
python tests/browser/natural_voice.py
```

The hub uses controlled public-provider fixtures and verifies persistence, planner, country filters, real job state and mobile layout. Voice cancellation verifies that muting conversational speech leaves background export rendering intact. The natural voice check requires the separately downloaded and checksum-verified Linux runtime/model under `/tmp/jarvis-natural-test`; unlike the other browser checks it uses actual neural model weights. Those files are development artifacts and are not included in the update ZIP. Native macOS inference and live provider availability are not established by these checks.

The former hub browser check now runs its Astra/world replacement. Astra verifies text-triggered identity animation, country news, plan review, actual driver calls using a controlled driver, independent mute, popup web controls and mobile layout. Native CoreGraphics events, AppKit panel creation and macOS accessibility permission are not verified on Linux.

Astra now additionally checks saved backend identity, Spotify and arbitrary website requests, the token-free browser popup, spoken cancellation and a reviewed real-geometry scene plan. Run `python tests/blender_smoke.py` separately for actual installed Blender: creates and reopens car/house/robot mesh files and verifies cancellation. It downloads nothing and does not verify macOS AppKit or mouse hardware.

`python tests/browser/reference_style.py` checks sleeping/running/completed clickable island desks using an actual controlled local job, then exports a procedural low-poly 720p video and verifies it with ffprobe. No image-generation model or remote assets are used.

`python tests/browser/autospeech.py` verifies repeated real automatic speech under gesture-required Chromium autoplay, including after ending the conversation, without clicking replay for each reply. Safari/macOS output hardware is not emulated.

`python tests/browser/audio_banner.py` reproduces blocked audio inside a modal voice dialog and checks top-layer clickability, dismissal without repeated reopening and successful activation.

`python tests/browser/notes.py` verifies a note task with stale 3D/game history, no language-model call and completion only after a controlled Notes adapter acknowledgement. It does not claim an actual macOS Notes run.
