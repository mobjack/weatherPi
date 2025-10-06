# Raspberry Pi Weather & Time Wallpaper Generator

This project generates a full set of background images for a small Raspberry Pi display (e.g., in a bathroom clock/weather station).
It combines **time of day** from [`conf/day_night.json`](./conf/day_night.json) with **weather conditions** from [`conf/gcp_conditions.json`](./conf/gcp_conditions.json) and uses the OpenAI Images API to render a unique wallpaper for each combination.

---

## Features

- **Time × Weather combinations**: Loops through every entry in both JSON maps.
  - Time examples: `sunrise`, `morning`, `midday`, `afternoon`, `sunset`, `dusk`, `evening`, `night`:contentReference[oaicite:0]{index=0}
  - Weather examples: `CLEAR`, `PARTLY_CLOUDY`, `RAIN`, `SNOW`, `THUNDERSTORM`, etc.:contentReference[oaicite:1]{index=1}
- **Style packs**: Choose from multiple art directions (e.g., *minimal-gradient*, *flat-illustration*, *neon-glow*).
- **Prompt saving**: Each generated image has its prompt stored in `_prompts/` for audit/re-use.
- **Auto-resize/crop**: By default, images are center-cropped to `800x600` to match the main display.
- **CLI options**: Control style, size, backoff timing, output directories, etc.

---

## Requirements

- Python 3.9+
- Dependencies:
  `pip install openai pillow`
