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
