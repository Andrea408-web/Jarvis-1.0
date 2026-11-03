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
python tests/browser/hub.py
python tests/browser/voice_cancellation.py
python tests/browser/natural_voice.py
```

The hub uses controlled public-provider fixtures and verifies persistence, planner, country filters, real job state and mobile layout. Voice cancellation verifies that muting conversational speech leaves background export rendering intact. The natural voice check requires the separately downloaded and checksum-verified Linux runtime/model under `/tmp/jarvis-natural-test`; unlike the other browser checks it uses actual neural model weights. Those files are development artifacts and are not included in the update ZIP. Native macOS inference and live provider availability are not established by these checks.
