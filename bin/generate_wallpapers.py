
import os
import sys
import json
import time
import base64
import argparse
import random
from pathlib import Path
from openai import OpenAI
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Load configuration from weather.conf file


def load_config_value(key, default=None):
    """Load a configuration value from weather.conf file"""
    config_path = "conf/weather.conf"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    value = line.split('=', 1)[1].strip()
                    return value
    return default


# Load API key from config
API_KEY = load_config_value("OPENAI_API_KEY")
if not API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not found in weather.conf", file=sys.stderr)
    sys.exit(1)
else:
    print("✅ Loaded ChatGPT API Key from weather.conf")

# Import the weather service for real weather data
try:
    from .weather_service_openweather import WeatherService
    WEATHER_SERVICE_AVAILABLE = True
    print("✅ Weather service available")
except ImportError:
    WEATHER_SERVICE_AVAILABLE = False
    print("⚠️  Weather service not available - will use fallback conditions")


# Optional: resize to your display (e.g., 800x600)
TRY_RESIZE = True
TARGET_SIZE = (1000, 600)  # (width, height)

if TRY_RESIZE:
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed. Run:  pip install pillow")
        TRY_RESIZE = False

# --- Configure these ---
MODEL = load_config_value("OPENAI_IMAGE_MODEL", "dall-e-3")
DEFAULT_OUTPUT_DIR = Path(load_config_value(
    "OUTPUT_DIR", "images/generated_wallpapers"))
OUT_EXT = ".png"  # png recommended for UI overlays later

# Where your JSONs live. Adjust if running outside this environment.
DEFAULT_DAY_NIGHT_JSON = load_config_value(
    "DAY_NIGHT_JSON", "conf/day_night.json")
DEFAULT_CONDITIONS_JSON = load_config_value(
    "CONDITIONS_JSON", "conf/gcp_conditions.json")

# Mapping from OpenWeatherMap conditions to Google Weather API conditions
OPENWEATHER_TO_GOOGLE_MAPPING = {
    'Clear': 'CLEAR',
    'Clouds': 'CLOUDY',
    'Rain': 'RAIN',
    'Drizzle': 'LIGHT_RAIN',
    'Thunderstorm': 'THUNDERSTORM',
    'Snow': 'SNOW',
    'Mist': 'CLOUDY',
    'Smoke': 'CLOUDY',
    'Haze': 'CLOUDY',
    'Dust': 'CLOUDY',
    'Fog': 'CLOUDY',
    'Sand': 'CLOUDY',
    'Ash': 'CLOUDY',
    'Squall': 'WINDY',
    'Tornado': 'WINDY'
}


def map_openweather_to_google(openweather_condition: str) -> str:
    """
    Map OpenWeatherMap condition to Google Weather API condition format.

    Args:
        openweather_condition: OpenWeatherMap condition (e.g., 'Clear', 'Clouds')

    Returns:
        Google Weather API condition (e.g., 'CLEAR', 'CLOUDY')
    """
    return OPENWEATHER_TO_GOOGLE_MAPPING.get(openweather_condition, 'CLEAR')


# Style packs: short, specific art directions that work well at small sizes.
STYLE_PACKS = {
    "minimal-gradient": " Create a sky view and use a soft, two-tone gradient background with gentle vignetting and simple weather icons implied by shapes. No text. Clean and modern, with large readable forms.",
    "flat-illustration": "Create a sky view and make a Flat, vector-like illustration with big simple shapes, minimal detail, and subtle weather motifs. Avoid clutter, prioritize readability at small size.",
    "paper-cutout": "Create a sky view and and make a Layered paper-cutout style with soft shadows between layers. Keep shapes bold and simple; suggest the weather with silhouettes or cutout symbols.",
    "glassmorphism": "Create a sky view and and make Soft blurred shapes with translucent glass panels and subtle highlights. Keep contrast high and composition simple for small displays.",
    "neon-glow": "Create a sky view and and make Dark background with tasteful neon glow accents that suggest the weather. Keep elements sparse and high-contrast for legibility.",
    "photoreal-soft": "Create a sky view and and make Softly photoreal, but low detail and low noise. Shallow depth-of-field look with simple composition and clear weather cue.",
    "isometric": "Create a sky view and and make a simple isometric composition with minimal geometry and a single focal element hinting at the weather. Keep edges clean and uncluttered."
}

# Initialize OpenAI client with API key from config
client = OpenAI(api_key=API_KEY)


@dataclass
class RenderPlan:
    style_key: str
    time_key: str
    time_desc: str
    cond_key: str
    cond_desc: str

    def safe_name(self, ext: str) -> str:
        ck = self.cond_key.lower().replace(" ", "-")
        return f"{ck}{ext}"


class WallpaperGenerator:
    """
    A class to generate single wallpaper files based on style, time, and weather conditions.
    """

    def __init__(self,
                 day_night_json: str = "conf/day_night.json",
                 conditions_json: str = "conf/gcp_conditions.json",
                 output_dir: str = "images/generated_wallpapers"):
        """
        Initialize the WallpaperGenerator.

        Args:
            day_night_json: Path to conf/day_night.json file
            conditions_json: Path to conf/gcp_conditions.json file
            output_dir: Directory to save generated wallpapers
        """
        self.client = OpenAI(api_key=API_KEY)
        self.day_night_json = day_night_json
        self.conditions_json = conditions_json
        self.output_dir = output_dir
        self.day_night_map = None
        self.conditions_map = None

        # Initialize weather service if available
        self.weather_service = None
        if WEATHER_SERVICE_AVAILABLE:
            try:
                self.weather_service = WeatherService()
                print("✅ Weather service initialized for wallpaper generation")
            except Exception as e:
                print(f"⚠️  Could not initialize weather service: {e}")
                self.weather_service = None

    def _load_maps(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Load the day/night and conditions mapping files."""
        with open(self.day_night_json, "r", encoding="utf-8") as f:
            day_night_map = json.load(f)
        with open(self.conditions_json, "r", encoding="utf-8") as f:
            conditions_map = json.load(f)
        return day_night_map, conditions_map

    def _epoch_to_time_of_day(self, epoch_time: float) -> str:
        """
        Convert epoch time to time of day key.

        Args:
            epoch_time: Unix timestamp

        Returns:
            Time of day key (e.g., 'morning', 'afternoon', etc.)
        """
        dt = datetime.fromtimestamp(epoch_time)
        hour = dt.hour

        # Map hours to time of day based on the day_night.json structure
        if 5 <= hour < 7:  # Sunrise time approximation
            return "sunrise"
        elif 7 <= hour < 11:  # Morning
            return "morning"
        elif 11 <= hour < 13:  # Midday
            return "midday"
        elif 13 <= hour < 16:  # Afternoon
            return "afternoon"
        elif 16 <= hour < 19:  # Sunset time approximation
            return "sunset"
        elif 19 <= hour < 22:  # Dusk/Evening
            return "dusk" if hour < 20 else "evening"
        else:  # Night
            return "night"

    def get_current_weather_condition(self, location: str = "95037") -> str:
        """
        Get current weather condition from OpenWeatherMap API.

        Args:
            location: Location to get weather for

        Returns:
            Google Weather API condition string (e.g., 'CLEAR', 'CLOUDY')
        """
        if not self.weather_service:
            print("⚠️  Weather service not available, using CLEAR condition")
            return "CLEAR"

        try:
            current_weather = self.weather_service.get_current_weather(
                location)
            openweather_condition = current_weather.get('condition', 'Clear')
            google_condition = map_openweather_to_google(openweather_condition)
            print(
                f"🌤️  Current weather: {openweather_condition} -> {google_condition}")
            return google_condition
        except Exception as e:
            print(f"⚠️  Error getting weather condition: {e}, using CLEAR")
            return "CLEAR"

    def get_current_time_epoch(self) -> float:
        """Get current time as epoch timestamp."""
        return time.time()

    def _ensure_directories(self, output_dir: Path, style_key: str, time_key: str) -> Path:
        """Ensure the necessary directories exist and return the target directory."""
        style_dir = output_dir / style_key
        style_dir.mkdir(parents=True, exist_ok=True)
        time_dir = style_dir / time_key.lower().replace(" ", "-")
        time_dir.mkdir(parents=True, exist_ok=True)
        (time_dir / "_prompts").mkdir(parents=True, exist_ok=True)
        return time_dir

    def _build_prompt(self, time_key: str, time_desc: str, cond_key: str, cond_desc: str, style_text: str, target_size: Tuple[int, int]) -> str:
        """Build the prompt for image generation."""
        w, h = target_size
        base = (
            f"Create a sky view wallpaper for a small display with a size of({w}x{h}). "
            f"Theme the scene to the time of day '{time_key}' described as: {time_desc}. "
            f"Weather condition is '{cond_key}' meaning: {cond_desc}. "
            f"CRITICAL: Do not include ANY text, numbers, times, characters, symbols, letters, digits, or written words in the image. "
            f"Avoid any text, logos, watermarks, UI elements, or written content. "
            f"High contrast and clarity at {w}x{h}. "
        )
        style = f"Apply this visual style: {style_text}"
        return base + style

    def _generate_image_b64(self, prompt: str, model: str) -> bytes:
        """Generate image using OpenAI API and return as bytes."""
        result = self.client.images.generate(
            model=model,
            prompt=prompt,
            size="1024x1024",
            n=1,
            response_format="b64_json",
        )
        b64 = result.data[0].b64_json
        return base64.b64decode(b64)

    def _maybe_resize(self, in_png: bytes, target_size: Tuple[int, int], try_resize: bool) -> bytes:
        """Resize image if needed."""
        if not try_resize:
            return in_png

        try:
            from PIL import Image
            from io import BytesIO

            with Image.open(BytesIO(in_png)) as im:
                # Keep aspect: center-crop to target aspect, then resize
                target_w, target_h = target_size
                target_aspect = target_w / target_h
                src_w, src_h = im.size
                src_aspect = src_w / src_h

                if src_aspect > target_aspect:
                    # too wide -> crop width
                    new_w = int(src_h * target_aspect)
                    x0 = (src_w - new_w) // 2
                    box = (x0, 0, x0 + new_w, src_h)
                else:
                    # too tall -> crop height
                    new_h = int(src_w / target_aspect)
                    y0 = (src_h - new_h) // 2
                    box = (0, y0, src_w, y0 + new_h)

                im_cropped = im.crop(box)
                im_resized = im_cropped.resize(
                    (target_w, target_h), Image.LANCZOS)

                out = BytesIO()
                im_resized.save(out, format="PNG")
                return out.getvalue()
        except ImportError:
            print("Pillow not installed. Skipping resize.")
            return in_png

    def generate_wallpaper(self,
                           style: str,
                           epoch_time: float,
                           weather_condition: str,
                           target_size: Optional[Tuple[int, int]] = None,
                           try_resize: Optional[bool] = None,
                           model: Optional[str] = None,
                           save_prompt: Optional[bool] = None) -> Dict[str, str]:
        """
        Generate a single wallpaper file.

        Args:
            style: Style pack name (e.g., 'minimal-gradient', 'photoreal-soft')
            epoch_time: Unix timestamp for time of day determination
            weather_condition: Weather condition key (e.g., 'CLEAR', 'RAIN')
            target_size: Target size for resizing (width, height). Defaults to (1000, 600) if None.
            try_resize: Whether to resize images to target size. Defaults to True if None.
            model: OpenAI model to use for image generation. Defaults to "dall-e-3" if None.
            save_prompt: Whether to save the prompt to a file. Defaults to False if None.

        Returns:
            Dictionary with 'filename' and 'path' keys
        """
        # Set default values for optional parameters
        if target_size is None:
            target_size = (1000, 600)
        if try_resize is None:
            try_resize = True
        if model is None:
            model = "dall-e-3"
        if save_prompt is None:
            save_prompt = False

        # Validate style and handle random selection
        if style == 'random':
            # Randomly select from available styles
            available_styles = list(STYLE_PACKS.keys())
            style = random.choice(available_styles)
            print(f"🎲 Randomly selected style: {style}")
        elif style not in STYLE_PACKS:
            raise ValueError(
                f"Unknown style '{style}'. Available styles: {list(STYLE_PACKS.keys())} + 'random'")

        # Load mapping files
        day_night_map, conditions_map = self._load_maps()

        # Validate weather condition
        if weather_condition not in conditions_map:
            raise ValueError(
                f"Unknown weather condition '{weather_condition}'. Available conditions: {list(conditions_map.keys())}")

        # Convert epoch time to time of day
        time_key = self._epoch_to_time_of_day(epoch_time)
        time_desc = day_night_map[time_key]
        cond_desc = conditions_map[weather_condition]

        # Set up output directory
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Ensure directories exist
        time_dir = self._ensure_directories(output_path, style, time_key)

        # Build prompt
        style_text = STYLE_PACKS[style]
        prompt = self._build_prompt(
            time_key, time_desc, weather_condition, cond_desc, style_text, target_size)

        # Generate filename
        cond_key_safe = weather_condition.lower().replace("_", "_")
        filename = f"{cond_key_safe}.png"
        file_path = time_dir / filename

        # Check if file already exists
        if file_path.exists():
            print(f"⏭️  File already exists: {filename}")
            print(
                f"    Style: {style} | Time: {time_key} | Condition: {weather_condition}")
            return {
                "filename": filename,
                "path": str(file_path)
            }

        # Save prompt if requested
        if save_prompt:
            prompt_path = time_dir / "_prompts" / f"{cond_key_safe}.txt"
            prompt_path.write_text(prompt, encoding="utf-8")

        # Generate image
        raw_png = self._generate_image_b64(prompt, model)

        # Resize if needed
        if try_resize:
            final_png = self._maybe_resize(raw_png, target_size, try_resize)
        else:
            final_png = raw_png

        # Write file
        file_path.write_bytes(final_png)

        return {
            "filename": filename,
            "path": str(file_path)
        }

    def generate_current_weather_wallpaper(self,
                                           style: str = "photoreal-soft",
                                           location: str = "95037",
                                           target_size: Optional[Tuple[int,
                                                                       int]] = None,
                                           try_resize: Optional[bool] = None,
                                           model: Optional[str] = None,
                                           save_prompt: Optional[bool] = None) -> Dict[str, str]:
        """
        Generate a wallpaper based on current real weather conditions.

        Args:
            style: Style pack name (e.g., 'minimal-gradient', 'photoreal-soft')
            location: Location to get weather for
            target_size: Target size for resizing (width, height). Defaults to (1000, 600) if None.
            try_resize: Whether to resize images to target size. Defaults to True if None.
            model: OpenAI model to use for image generation. Defaults to "dall-e-3" if None.
            save_prompt: Whether to save the prompt to a file. Defaults to False if None.

        Returns:
            Dictionary with 'filename' and 'path' keys
        """
        # Get current time and weather
        current_epoch = self.get_current_time_epoch()
        current_weather_condition = self.get_current_weather_condition(
            location)

        print(f"🎨 Generating wallpaper for current conditions:")
        print(
            f"   Time: {datetime.fromtimestamp(current_epoch).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Weather: {current_weather_condition}")
        print(f"   Style: {style}")

        # Use the existing generate_wallpaper method with current data
        return self.generate_wallpaper(
            style=style,
            epoch_time=current_epoch,
            weather_condition=current_weather_condition,
            target_size=target_size,
            try_resize=try_resize,
            model=model,
            save_prompt=save_prompt
        )


def load_maps(day_night_path: str, conds_path: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    with open(day_night_path, "r", encoding="utf-8") as f:
        day_night_map = json.load(f)
    with open(conds_path, "r", encoding="utf-8") as f:
        conditions_map = json.load(f)
    return day_night_map, conditions_map


def ensure_dirs(out_dir: Path, style_key: str = None, time_key: str = None):
    out_dir.mkdir(parents=True, exist_ok=True)
    if style_key and time_key:
        # Create style-specific and time-specific subdirectories
        style_dir = out_dir / style_key
        style_dir.mkdir(parents=True, exist_ok=True)
        time_dir = style_dir / time_key.lower().replace(" ", "-")
        time_dir.mkdir(parents=True, exist_ok=True)
        (time_dir / "_prompts").mkdir(parents=True, exist_ok=True)
    elif style_key:
        # Create style-specific subdirectory
        style_dir = out_dir / style_key
        style_dir.mkdir(parents=True, exist_ok=True)
        (style_dir / "_prompts").mkdir(parents=True, exist_ok=True)
    else:
        # Create general prompts directory for backward compatibility
        (out_dir / "_prompts").mkdir(parents=True, exist_ok=True)


def build_prompt(plan: RenderPlan, style_text: str, target_size: Tuple[int, int]) -> str:
    w, h = target_size
    base = (
        f"Design a clean, modern wallpaper for a small Raspberry Pi display ({w}x{h}). "
        f"Theme the scene to the time of day '{plan.time_key}' described as: {plan.time_desc}. "
        f"Weather condition is '{plan.cond_key}' meaning: {plan.cond_desc}. "
        f"CRITICAL: This image must be completely text-free. Do not include ANY text, numbers, times, characters, symbols, letters, digits, written words, typography, fonts, or readable content. "
        f"Avoid any text, logos, watermarks, UI elements, written content, street signs, building names, license plates, or any readable text. "
        f"The image should be purely visual with no readable elements whatsoever. "
        f"Focus on natural elements, colors, lighting, and atmospheric effects only. "
        f"High contrast and clarity at {w}x{h}. "
    )
    style = f"Apply this visual style: {style_text}"
    return base + style


def validate_image_text_free(image_path: Path) -> bool:
    """
    Basic validation to check if an image appears to be text-free.
    This is a simple heuristic - for production use, consider OCR validation.
    """
    try:
        from PIL import Image
        import numpy as np

        # Load image and convert to grayscale
        img = Image.open(image_path).convert('L')
        img_array = np.array(img)

        # Simple heuristic: check for high contrast horizontal/vertical lines
        # that might indicate text (this is very basic)
        h_edges = np.abs(np.diff(img_array, axis=1))
        v_edges = np.abs(np.diff(img_array, axis=0))

        # If there are many sharp edges in regular patterns, might contain text
        h_edge_density = np.mean(h_edges > 50)  # threshold for "sharp" edges
        v_edge_density = np.mean(v_edges > 50)

        # Very basic check - in practice, you'd want more sophisticated detection
        return h_edge_density < 0.1 and v_edge_density < 0.1

    except Exception as e:
        print(f"Warning: Could not validate image {image_path}: {e}")
        return True  # Assume OK if we can't check


def save_prompt(out_dir: Path, prompt: str, filename_no_ext: str, style_key: str = None, time_key: str = None):
    if style_key and time_key:
        # Save to style and time-specific prompts directory
        time_dir = time_key.lower().replace(" ", "-")
        prompt_path = out_dir / style_key / time_dir / \
            "_prompts" / (filename_no_ext + ".txt")
    elif style_key:
        # Save to style-specific prompts directory
        prompt_path = out_dir / style_key / \
            "_prompts" / (filename_no_ext + ".txt")
    else:
        # Save to general prompts directory for backward compatibility
        prompt_path = out_dir / "_prompts" / (filename_no_ext + ".txt")
    prompt_path.write_text(prompt, encoding="utf-8")


def generate_image_b64(prompt: str) -> bytes:
    result = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )
    b64 = result.data[0].b64_json
    return base64.b64decode(b64)


def maybe_resize(in_png: bytes, target_size: Tuple[int, int]) -> bytes:
    if not TRY_RESIZE:
        return in_png
    from io import BytesIO
    with Image.open(BytesIO(in_png)) as im:
        # Keep aspect: center-crop to target aspect, then resize
        target_w, target_h = target_size
        target_aspect = target_w / target_h
        src_w, src_h = im.size
        src_aspect = src_w / src_h

        if src_aspect > target_aspect:
            # too wide -> crop width
            new_w = int(src_h * target_aspect)
            x0 = (src_w - new_w) // 2
            box = (x0, 0, x0 + new_w, src_h)
        else:
            # too tall -> crop height
            new_h = int(src_w / target_aspect)
            y0 = (src_h - new_h) // 2
            box = (0, y0, src_w, y0 + new_h)

        im_cropped = im.crop(box)
        im_resized = im_cropped.resize((target_w, target_h), Image.LANCZOS)

        out = BytesIO()
        im_resized.save(out, format="PNG")
        return out.getvalue()


def write_png(path: Path, data: bytes):
    path.write_bytes(data)


def make_plans(styles: List[str], day_night_map: Dict[str, str], conditions_map: Dict[str, str]) -> List[RenderPlan]:
    plans: List[RenderPlan] = []
    for s in styles:
        for time_key, time_desc in day_night_map.items():
            for cond_key, cond_desc in conditions_map.items():
                plans.append(RenderPlan(
                    s, time_key, time_desc, cond_key, cond_desc))
    return plans


def example_class_usage():
    """
    Example of how to use the WallpaperGenerator class.
    This function demonstrates generating wallpapers with real weather data.
    """
    print("🎨 WallpaperGenerator Class Example")
    print("=" * 40)

    # Create a generator instance
    generator = WallpaperGenerator(
        day_night_json="conf/day_night.json",
        conditions_json="conf/gcp_conditions.json",
        output_dir="images/generated_wallpapers"
    )

    # Example 1: Generate a wallpaper based on current real weather
    try:
        print("\n🌤️  Example 1: Current Weather Wallpaper")
        result = generator.generate_current_weather_wallpaper(
            style="random",  # Use random style selection for variety
            location="95037",  # Use zip code for better geocoding
            target_size=TARGET_SIZE,  # Use configurable target size
            try_resize=True,
            save_prompt=True
        )

        print(f"✅ Generated current weather wallpaper successfully!")
        print(f"   Filename: {result['filename']}")
        print(f"   Path: {result['path']}")

    except Exception as e:
        print(f"❌ Error generating current weather wallpaper: {e}")

    # Example 2: Generate a wallpaper for specific conditions (legacy method)
    try:
        print("\n🎲 Example 2: Random Style with Specific Weather")
        import time
        current_epoch = time.time()

        result = generator.generate_wallpaper(
            style="random",  # Try "random" for random style selection
            epoch_time=current_epoch,
            weather_condition="CLEAR",
            target_size=TARGET_SIZE,  # Use configurable target size
            try_resize=True,
            save_prompt=True
        )

        print(f"✅ Generated specific condition wallpaper successfully!")
        print(f"   Filename: {result['filename']}")
        print(f"   Path: {result['path']}")

    except Exception as e:
        print(f"❌ Error generating specific condition wallpaper: {e}")


if __name__ == "__main__" and len(sys.argv) == 1:
    # If no command line arguments, show example usage
    example_class_usage()
    print("\n" + "=" * 50)
    print("To use the original batch generation functionality, run with arguments:")
    print("python generate_wallpapers-v3.py --help")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Generate day/time x weather wallpapers with style packs.")
    parser.add_argument(
        "--day-night-json", default=DEFAULT_DAY_NIGHT_JSON, help="Path to conf/day_night.json")
    parser.add_argument("--conditions-json", default=DEFAULT_CONDITIONS_JSON,
                        help="Path to conf/gcp_conditions.json")
    parser.add_argument(
        "--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    parser.add_argument("--style", default=load_config_value("STYLE_PACK",
                        "minimal-gradient"), help="Style pack name (or 'random' for random selection)")
    parser.add_argument("--all-styles", action="store_true",
                        help="Generate every style pack")
    parser.add_argument("--list-styles", action="store_true",
                        help="List available style packs and exit")
    parser.add_argument("--no-resize", action="store_true",
                        help="Do not downscale/crop to target size")
    parser.add_argument("--size", default=None,
                        help="Target WxH, e.g., 800x600")
    parser.add_argument("--backoff", type=float, default=2.0,
                        help="Seconds between requests")
    parser.add_argument("--force", action="store_true",
                        help="Force regeneration of existing files")
    parser.add_argument("--save-prompts", action="store_true", default=False,
                        help="Save GPT prompts to _prompts directory (default: False)")
    args = parser.parse_args()

    global TRY_RESIZE, TARGET_SIZE
    if args.no_resize:
        TRY_RESIZE = False
    if args.size:
        try:
            w, h = args.size.lower().split("x")
            TARGET_SIZE = (int(w), int(h))
        except Exception:
            print("Invalid --size format; expected WxH like 800x600")

    if args.list_styles:
        print("Available style packs:")
        for k in STYLE_PACKS.keys():
            print(" -", k)
        print(" - random (randomly selects from above styles)")
        return

    output_dir = Path(args.output_dir)
    # Don't create directories here - will create them per style

    day_night_map, conditions_map = load_maps(
        args.day_night_json, args.conditions_json)

    if args.all_styles:
        styles = list(STYLE_PACKS.keys())
    else:
        if args.style == 'random':
            # Randomly select from available styles
            available_styles = list(STYLE_PACKS.keys())
            styles = [random.choice(available_styles)]
            print(f"🎲 Randomly selected style: {styles[0]}")
        elif args.style not in STYLE_PACKS:
            print(
                f"Unknown style '{args.style}'. Use --list-styles to see options.")
            return
        else:
            styles = [args.style]

    plans = make_plans(styles, day_night_map, conditions_map)
    print(f"Total images to generate: {len(plans)}")
    if args.force:
        print("🔄 Force mode enabled - will regenerate existing files")
    else:
        print("⏭️  Skip mode enabled - will skip existing files")
    backoff = max(0.0, args.backoff)

    # Statistics tracking
    stats = {"skipped": 0, "generated": 0, "failed": 0}

    for i, plan in enumerate(plans, start=1):
        # Ensure style and time-specific directories exist
        ensure_dirs(output_dir, plan.style_key, plan.time_key)

        style_text = STYLE_PACKS[plan.style_key]
        prompt = build_prompt(
            plan, style_text, TARGET_SIZE if TRY_RESIZE else (1024, 1024))
        filename = plan.safe_name(OUT_EXT)
        filename_no_ext = filename[:-len(OUT_EXT)]
        time_dir = plan.time_key.lower().replace(" ", "-")
        out_path = output_dir / plan.style_key / time_dir / filename

        # Save prompt only if --save-prompts flag is set
        if args.save_prompts:
            save_prompt(output_dir, prompt, filename_no_ext,
                        plan.style_key, plan.time_key)

        # Check if file already exists and skip if not forcing regeneration
        if out_path.exists() and not args.force:
            file_size = out_path.stat().st_size
            print(
                f"[{i}/{len(plans)}] ⏭️  Skipping existing {filename} ({file_size:,} bytes)")
            print(
                f"    Style: {plan.style_key} | Time: {plan.time_key} | Condition: {plan.cond_key}")
            stats["skipped"] += 1
            continue
        elif out_path.exists() and args.force:
            file_size = out_path.stat().st_size
            print(
                f"[{i}/{len(plans)}] 🔄 Force regenerating {filename} (was {file_size:,} bytes)")
            print(
                f"    Style: {plan.style_key} | Time: {plan.time_key} | Condition: {plan.cond_key}")

        # Enhanced retry loop with detailed reporting
        success = False
        for attempt in range(1, 4):
            try:
                print(
                    f"[{i}/{len(plans)}] 🎨 Generating {filename} (attempt {attempt}/3)")
                print(
                    f"    Style: {plan.style_key} | Time: {plan.time_key} | Condition: {plan.cond_key}")

                # Generate image with timing
                start_time = time.time()
                raw_png = generate_image_b64(prompt)
                generation_time = time.time() - start_time
                print(
                    f"    ✅ Image generated in {generation_time:.2f}s ({len(raw_png)} bytes)")

                # Resize if needed
                if TRY_RESIZE:
                    resize_start = time.time()
                    final_png = maybe_resize(raw_png, TARGET_SIZE)
                    resize_time = time.time() - resize_start
                    print(
                        f"    🔄 Resized to {TARGET_SIZE} in {resize_time:.2f}s ({len(final_png)} bytes)")
                else:
                    final_png = raw_png
                    print(f"    ⏭️  Skipping resize (--no-resize flag)")

                # Write file
                write_start = time.time()
                write_png(out_path, final_png)
                write_time = time.time() - write_start
                print(f"    💾 Saved to {out_path} in {write_time:.2f}s")

                success = True
                stats["generated"] += 1
                print(
                    f"    🎉 Success! Total time: {time.time() - start_time:.2f}s")
                break

            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                print(
                    f"    ❌ Error on attempt {attempt}/3: {error_type}: {error_msg}")

                # More specific error handling
                if "rate_limit" in error_msg.lower() or "quota" in error_msg.lower():
                    print(
                        f"    ⚠️  Rate limit detected - will wait longer before retry")
                    wait_time = backoff * attempt * 2  # Double wait for rate limits
                elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                    print(f"    🌐 Network issue detected - will retry with backoff")
                    wait_time = backoff * attempt
                else:
                    print(f"    🔧 Unknown error - will retry with standard backoff")
                    wait_time = backoff * attempt

                if attempt == 3:
                    print(
                        f"    💀 Giving up on {filename} after 3 failed attempts")
                    print(f"    📝 Last error: {error_type}: {error_msg}")
                else:
                    print(f"    ⏳ Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)

        if not success:
            stats["failed"] += 1
            # Clean up any partially created files
            if out_path.exists():
                try:
                    out_path.unlink()  # Remove the file
                    print(f"    🧹 Cleaned up partial file: {out_path}")
                except Exception as cleanup_error:
                    print(
                        f"    ⚠️  Warning: Could not clean up {out_path}: {cleanup_error}")
            print(
                f"    🚫 Failed to generate {filename} - continuing with next image")

        time.sleep(backoff)

    # Print final statistics
    print("\n" + "="*50)
    print("📊 GENERATION SUMMARY")
    print("="*50)
    print(f"✅ Successfully generated: {stats['generated']} images")
    print(f"⏭️  Skipped existing: {stats['skipped']} images")
    print(f"❌ Failed to generate: {stats['failed']} images")
    print(
        f"📁 Total processed: {stats['generated'] + stats['skipped'] + stats['failed']} images")
    print("="*50)
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
