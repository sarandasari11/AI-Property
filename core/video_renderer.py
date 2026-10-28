"""
Video Compositing & Rendering Engine for Real Estate Property Videos.

Features:
1. Smooth Ken Burns motion effect (subtle cinematic pan & zoom) on static property photos.
2. Television-quality branded lower-third cards & badges with semi-transparent glassmorphic styling.
3. Crossfade transitions and synchronization with neural audio soundtrack.
4. Fast MP4 rendering with libx264 and AAC audio.
"""
import os
import math
from pathlib import Path
from typing import List, Tuple, Optional, Callable
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import (
    VideoClip,
    AudioFileClip,
    concatenate_videoclips,
)
from moviepy.video.fx import FadeIn, FadeOut

from config import (
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    DEFAULT_FPS,
    OUTPUT_DIR,
    TEMP_DIR,
    COLOR_PRIMARY,
    COLOR_ACCENT,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
)
from core.validator import PropertyInput
from core.script_generator import SceneScript, PropertyScript


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Loads system modern font with graceful fallback to PIL default font."""
    font_candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for font_path in font_candidates:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_overlay_card(
    width: int,
    height: int,
    scene: SceneScript,
    property_name: str,
) -> Image.Image:
    """
    Generates a premium glassmorphic overlay card on an RGBA canvas.
    Includes accent badge, drop shadows, and high-contrast readable typography.
    """
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Subtle cinematic bottom gradient vignette for guaranteed contrast
    vignette_height = int(height * 0.45)
    vignette = Image.new("RGBA", (width, vignette_height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    for y in range(vignette_height):
        alpha = int(190 * (y / vignette_height) ** 1.3)
        v_draw.line([(0, y), (width, y)], fill=(8, 12, 20, alpha))
    overlay.paste(vignette, (0, height - vignette_height), vignette)

    # Fonts
    badge_font = get_font(max(13, int(height * 0.022)), bold=True)
    title_font = get_font(max(20, int(height * 0.042)), bold=True)
    subtitle_font = get_font(max(15, int(height * 0.026)), bold=False)

    card_margin_x = int(width * 0.06)
    card_margin_bottom = int(height * 0.06)

    if scene.scene_type in ("intro", "outro"):
        # Centered prominent card for Hook and CTA Outro
        card_w = int(width * 0.88)
        card_h = int(height * 0.26)
        card_x = (width - card_w) // 2
        card_y = height - card_h - card_margin_bottom
    else:
        # Sleek lower-third card for feature scenes
        card_w = int(width * 0.82)
        card_h = int(height * 0.23)
        card_x = card_margin_x
        card_y = height - card_h - card_margin_bottom

    # 2. Glassmorphic Card Background (Rounded Rectangle with semi-transparent slate)
    card_rect = [card_x, card_y, card_x + card_w, card_y + card_h]
    radius = int(height * 0.018)
    draw.rounded_rectangle(card_rect, radius=radius, fill=(12, 18, 30, 215))

    # 3. Top Accent Border Line (Champagne Gold / Warm Luxury)
    accent_bar_height = max(3, int(height * 0.005))
    accent_rect = [card_x + radius, card_y, card_x + card_w - radius, card_y + accent_bar_height]
    draw.rectangle(accent_rect, fill=(218, 165, 32, 255))

    # 4. Badge Pill (e.g. 'EXCLUSIVE LISTING', 'FEATURE 1', 'BOOK VIEWING')
    badge_label = (scene.badge_text or "PROPERTY TOUR").upper()
    badge_bbox = draw.textbbox((0, 0), badge_label, font=badge_font)
    badge_text_w = badge_bbox[2] - badge_bbox[0]
    badge_text_h = badge_bbox[3] - badge_bbox[1]
    
    badge_pad_x = int(height * 0.016)
    badge_pad_y = int(height * 0.006)
    badge_x = card_x + int(height * 0.028)
    badge_y = card_y + int(height * 0.024)
    
    badge_bg = [
        badge_x,
        badge_y,
        badge_x + badge_text_w + badge_pad_x * 2,
        badge_y + badge_text_h + badge_pad_y * 2,
    ]
    draw.rounded_rectangle(badge_bg, radius=int(height * 0.008), fill=(218, 165, 32, 230))
    draw.text((badge_x + badge_pad_x, badge_y + badge_pad_y - 1), badge_label, font=badge_font, fill=(10, 15, 25, 255))

    # 5. Primary Title Text (Bold with subtle drop shadow)
    title_text = scene.caption_title
    title_x = card_x + int(height * 0.028)
    title_y = badge_y + badge_text_h + badge_pad_y * 2 + int(height * 0.016)

    # Shadow
    draw.text((title_x + 1, title_y + 1), title_text, font=title_font, fill=(0, 0, 0, 180))
    # Main Title
    draw.text((title_x, title_y), title_text, font=title_font, fill=COLOR_TEXT_LIGHT)

    # 6. Secondary Subtitle / Description Text
    subtitle_text = scene.caption_subtitle
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_h = title_bbox[3] - title_bbox[1]
    
    subtitle_x = title_x
    subtitle_y = title_y + title_h + int(height * 0.012)
    
    # Shadow & Main Subtitle
    draw.text((subtitle_x + 1, subtitle_y + 1), subtitle_text, font=subtitle_font, fill=(0, 0, 0, 160))
    draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=(210, 225, 240, 240))

    return overlay


def build_ken_burns_scene_clip(
    scene: SceneScript,
    duration: float,
    width: int = 1280,
    height: int = 720,
    zoom_in: bool = True,
    property_name: str = "Property",
) -> VideoClip:
    """
    Creates a VideoClip for a single scene applying Ken Burns motion
    and composite overlay card.
    """
    # 1. Load source photo
    img_path = Path(scene.image_path)
    if not img_path.exists():
        # Fallback colored canvas if image missing
        base_img = Image.new("RGB", (width, height), color=(30, 45, 65))
    else:
        try:
            base_img = Image.open(img_path).convert("RGB")
        except Exception:
            base_img = Image.new("RGB", (width, height), color=(30, 45, 65))

    # Pre-scale image to maintain aspect ratio covering the target box with 15% zoom buffer
    buffer_scale = 1.15
    target_w = int(width * buffer_scale)
    target_h = int(height * buffer_scale)
    
    # Resize preserving aspect ratio (crop to fill target_w x target_h)
    img_w, img_h = base_img.size
    aspect = img_w / img_h
    target_aspect = target_w / target_h
    
    if aspect > target_aspect:
        # Image is wider: fit height and crop width
        new_h = target_h
        new_w = int(target_h * aspect)
    else:
        # Image is taller: fit width and crop height
        new_w = target_w
        new_h = int(target_w / aspect)
    
    scaled_img = base_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    # Crop to exact target_w x target_h
    crop_x = (new_w - target_w) // 2
    crop_y = (new_h - target_h) // 2
    buffer_img = scaled_img.crop((crop_x, crop_y, crop_x + target_w, crop_y + target_h))

    # 2. Render static overlay graphic
    overlay_img = create_overlay_card(width, height, scene, property_name)

    # 3. Ken Burns Frame Generator
    max_dx = target_w - width
    max_dy = target_h - height

    def make_frame(t: float) -> np.ndarray:
        progress = min(1.0, max(0.0, t / max(0.1, duration)))
        
        if zoom_in:
            # Zoom from 1.0 (larger crop) to tighter crop
            cur_scale = 1.08 - 0.08 * progress
        else:
            # Zoom from tight crop to wider crop
            cur_scale = 1.0 + 0.08 * progress

        cur_crop_w = int(width * cur_scale)
        cur_crop_h = int(height * cur_scale)
        
        # Center crop with slight subtle pan
        offset_x = int((target_w - cur_crop_w) * (0.5 + 0.1 * (progress - 0.5)))
        offset_y = int((target_h - cur_crop_h) * (0.5 + 0.1 * (progress - 0.5)))
        
        offset_x = max(0, min(max_dx, offset_x))
        offset_y = max(0, min(max_dy, offset_y))

        cropped = buffer_img.crop((offset_x, offset_y, offset_x + cur_crop_w, offset_y + cur_crop_h))
        frame_img = cropped.resize((width, height), Image.Resampling.BILINEAR).convert("RGBA")
        
        # Composite text overlay on top
        frame_img.alpha_composite(overlay_img)
        
        return np.array(frame_img.convert("RGB"))

    scene_clip = VideoClip(make_frame, duration=duration)
    
    # Apply subtle fade in & fade out for smooth scene transitions
    fade_dur = min(0.4, duration * 0.1)
    scene_clip = scene_clip.with_effects([FadeIn(fade_dur), FadeOut(fade_dur)])
    
    return scene_clip


def render_property_video(
    prop: PropertyInput,
    script: PropertyScript,
    scene_audio_data: List[Tuple[SceneScript, str, float]],
    master_audio_path: str,
    output_filename: str = "property_tour.mp4",
    width: int = 1280,
    height: int = 720,
    fps: int = DEFAULT_FPS,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> str:
    """
    Renders the complete property tour MP4 video.
    
    Args:
        prop: Validated PropertyInput.
        script: PropertyScript with scene details.
        scene_audio_data: List of (SceneScript, audio_path, duration).
        master_audio_path: Master mixed soundtrack path.
        output_filename: Output video file name.
        width: Video width (default: 1280).
        height: Video height (default: 720).
        fps: Frames per second (default: 24).
        progress_callback: Optional function (progress_fraction, message) -> None.
        
    Returns:
        Absolute path to the exported MP4 video file.
    """
    out_path = OUTPUT_DIR / output_filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback(0.05, "Building cinematic scene transitions...")

    clips = []
    num_scenes = len(scene_audio_data)

    for idx, (scene, audio_path, duration) in enumerate(scene_audio_data):
        zoom_in_direction = (idx % 2 == 0)
        
        scene_clip = build_ken_burns_scene_clip(
            scene=scene,
            duration=duration,
            width=width,
            height=height,
            zoom_in=zoom_in_direction,
            property_name=prop.name,
        )
        clips.append(scene_clip)
        
        if progress_callback:
            pct = 0.05 + 0.35 * ((idx + 1) / num_scenes)
            progress_callback(pct, f"Assembled scene {idx + 1} of {num_scenes}...")

    # 1. Concatenate all scenes sequentially
    if progress_callback:
        progress_callback(0.45, "Compositing video timeline...")

    final_video = concatenate_videoclips(clips, method="compose")

    # 2. Attach master soundtrack
    if progress_callback:
        progress_callback(0.55, "Attaching mixed neural soundtrack...")

    soundtrack_clip = AudioFileClip(master_audio_path)
    final_video = final_video.with_audio(soundtrack_clip)

    # 3. Export to MP4
    if progress_callback:
        progress_callback(0.65, "Encoding H.264 MP4 video...")

    final_video.write_videofile(
        str(out_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        threads=4,
        logger=None,  # Clean console
    )

    # 4. Clean up resources
    soundtrack_clip.close()
    final_video.close()
    for c in clips:
        try:
            c.close()
        except Exception:
            pass

    if progress_callback:
        progress_callback(1.0, "Video rendering complete!")

    return str(out_path.resolve())
