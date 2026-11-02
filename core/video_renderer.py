"""
Video Compositing & Rendering Engine for Real Estate Property Videos.

Features:
1. Ultra-Modern Architectural Capsule HUD Labels:
   - Floating dark glass pill card with a glowing electric cyan/gold accent vertical pill.
   - Distinct, glowing uppercase micro-tag.
   - Clean, modern layout (no outdated boxy rectangles).
   - Animated slide-in and scale-in reveal precisely synchronized with image arrival.
2. Synchronized Timeline Timing:
   - Each photo's duration is calculated to match its exact narration duration.
   - Sequential, exact cut transitions ensure speech, label, and photo change together in lockstep.
3. Smooth Ken Burns Camera Motion:
   - Sub-pixel cinematic pan and subtle zoom (zoom_in, pan_right, zoom_out, pan_left) with Sine ease-in-out.
4. Broadcast H.264 MP4 output with synchronized voiceover and ducked background audio.
"""
import math
from pathlib import Path
from typing import List, Tuple, Optional, Callable
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoClip,
    AudioFileClip,
    concatenate_videoclips,
)

from config import (
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    DEFAULT_FPS,
    OUTPUT_DIR,
    COLOR_TEXT_LIGHT,
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


def ease_out_expo(x: float) -> float:
    """Ultra-modern snappy exponential ease-out curve."""
    x = max(0.0, min(1.0, x))
    return 1.0 if x == 1.0 else 1.0 - math.pow(2, -10 * x)


def ease_in_out_sine(x: float) -> float:
    """Sine ease-in-out curve for smooth, organic camera motion."""
    x = max(0.0, min(1.0, x))
    return -(math.cos(math.pi * x) - 1.0) / 2.0


def draw_modern_capsule_label(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    scene: SceneScript,
    card_x: int,
    card_y: int,
    card_w: int,
    card_h: int,
    alpha_mult: float = 1.0,
):
    """
    Renders a completely new, ultra-modern luxury architectural HUD label.
    Design elements:
    - Sleek dark obsidian glass capsule with high blur appearance.
    - Vertical glowing accent bar (Emerald Cyan / Champagne Gold) indicating active scene.
    - Floating uppercase micro-pill badge with letterspacing.
    - High-fashion typography: Bold primary feature title with clean secondary specs.
    - 1px luminous edge border for depth.
    """
    if alpha_mult <= 0.005:
        return

    # 1. Main Obsidian Glass Capsule
    bg_alpha = int(225 * alpha_mult)
    radius = int(card_h * 0.28)  # Smooth modern rounded capsule
    rect = [card_x, card_y, card_x + card_w, card_y + card_h]
    
    # Deep obsidian slate fill
    draw.rounded_rectangle(rect, radius=radius, fill=(9, 14, 24, bg_alpha))
    
    # 1px perimeter glow / border highlight
    border_alpha = int(75 * alpha_mult)
    draw.rounded_rectangle(rect, radius=radius, outline=(255, 255, 255, border_alpha), width=1)

    # 2. Dynamic Accent Theme (Gold for Intro/Outro, Electric Teal/Cyan for Features)
    is_special = scene.scene_type in ("intro", "outro")
    if is_special:
        accent_color = (218, 165, 32)   # Champagne Gold
        badge_bg = (218, 165, 32, int(230 * alpha_mult))
        badge_text_color = (12, 18, 28, int(255 * alpha_mult))
    else:
        accent_color = (45, 212, 191)   # Modern Cyan / Emerald Mint
        badge_bg = (45, 212, 191, int(230 * alpha_mult))
        badge_text_color = (8, 20, 24, int(255 * alpha_mult))

    # 3. Vertical Accent Indicator (Left margin)
    bar_w = max(4, int(height * 0.006))
    bar_margin = int(card_h * 0.18)
    bar_rect = [
        card_x + int(card_h * 0.22),
        card_y + bar_margin,
        card_x + int(card_h * 0.22) + bar_w,
        card_y + card_h - bar_margin,
    ]
    draw.rounded_rectangle(
        bar_rect,
        radius=bar_w // 2,
        fill=(accent_color[0], accent_color[1], accent_color[2], int(255 * alpha_mult)),
    )

    # Content X offset
    content_x = bar_rect[2] + int(height * 0.022)

    # 4. Modern Uppercase Micro Badge Pill
    badge_font = get_font(max(11, int(height * 0.018)), bold=True)
    raw_badge = (scene.badge_text or "EXCLUSIVE").upper()
    badge_label = f" {raw_badge} "
    badge_bbox = draw.textbbox((0, 0), badge_label, font=badge_font)
    bw = badge_bbox[2] - badge_bbox[0]
    bh = badge_bbox[3] - badge_bbox[1]

    badge_pad_x = int(height * 0.010)
    badge_pad_y = int(height * 0.003)
    badge_y = card_y + int(card_h * 0.15)

    pill_rect = [
        content_x,
        badge_y,
        content_x + bw + badge_pad_x * 2,
        badge_y + bh + badge_pad_y * 2,
    ]
    draw.rounded_rectangle(pill_rect, radius=int((bh + badge_pad_y * 2) / 2), fill=badge_bg)
    draw.text(
        (content_x + badge_pad_x, badge_y + badge_pad_y - 1),
        badge_label,
        font=badge_font,
        fill=badge_text_color,
    )

    # 5. Primary Feature Title (Crisp, High Fashion)
    title_font = get_font(max(18, int(height * 0.036)), bold=True)
    title_y = pill_rect[3] + int(height * 0.010)
    title_text = scene.caption_title

    # Shadow
    draw.text((content_x + 1, title_y + 2), title_text, font=title_font, fill=(0, 0, 0, int(190 * alpha_mult)))
    # Main Title
    draw.text(
        (content_x, title_y),
        title_text,
        font=title_font,
        fill=(COLOR_TEXT_LIGHT[0], COLOR_TEXT_LIGHT[1], COLOR_TEXT_LIGHT[2], int(255 * alpha_mult)),
    )

    # 6. Secondary Spec Subtitle
    subtitle_font = get_font(max(13, int(height * 0.022)), bold=False)
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_h = title_bbox[3] - title_bbox[1]
    sub_y = title_y + title_h + int(height * 0.008)
    sub_text = scene.caption_subtitle

    # Shadow & Text
    draw.text((content_x + 1, sub_y + 1), sub_text, font=subtitle_font, fill=(0, 0, 0, int(160 * alpha_mult)))
    draw.text((content_x, sub_y), sub_text, font=subtitle_font, fill=(200, 220, 240, int(230 * alpha_mult)))


def create_overlay_card(
    width: int,
    height: int,
    scene: SceneScript,
    property_name: str = "Property",
    alpha_mult: float = 1.0,
) -> Image.Image:
    """
    Renders standalone overlay card canvas for preview and testing.
    """
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Clean gradient vignette at the bottom
    vignette_height = int(height * 0.40)
    vignette = Image.new("RGBA", (width, vignette_height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    for y in range(vignette_height):
        alpha = int(180 * (y / vignette_height) ** 1.3)
        v_draw.line([(0, y), (width, y)], fill=(6, 10, 18, alpha))
    overlay.paste(vignette, (0, height - vignette_height), vignette)

    card_margin_x = int(width * 0.05)
    card_margin_bottom = int(height * 0.05)

    card_w = int(width * 0.88)
    card_h = int(height * 0.22)
    card_x = card_margin_x
    card_y = height - card_h - card_margin_bottom

    draw_modern_capsule_label(
        draw=draw,
        width=width,
        height=height,
        scene=scene,
        card_x=card_x,
        card_y=card_y,
        card_w=card_w,
        card_h=card_h,
        alpha_mult=alpha_mult,
    )
    return overlay


def build_ken_burns_scene_clip(
    scene: SceneScript,
    duration: float,
    width: int = 1280,
    height: int = 720,
    motion_type: str = "zoom_in",
    zoom_in: Optional[bool] = None,
    property_name: str = "Property",
) -> VideoClip:
    """
    Creates a VideoClip for a single scene applying:
    1. Smooth cinematic Ken Burns camera movement (pan & zoom with ease-in-out interpolation).
    2. Ultra-modern capsule label with snappy slide-in and scale-in reveal precisely synchronized
       with this photo's arrival.
    """
    if zoom_in is not None:
        motion_type = "zoom_in" if zoom_in else "zoom_out"

    # 1. Load and prepare source photo
    img_path = Path(scene.image_path)
    if not img_path.exists():
        base_img = Image.new("RGB", (width, height), color=(20, 30, 45))
    else:
        try:
            base_img = Image.open(img_path).convert("RGB")
        except Exception:
            base_img = Image.new("RGB", (width, height), color=(20, 30, 45))

    # Pre-scale buffer image (18% margin for smooth camera motion)
    buffer_scale = 1.18
    target_w = int(width * buffer_scale)
    target_h = int(height * buffer_scale)

    img_w, img_h = base_img.size
    aspect = img_w / img_h
    target_aspect = target_w / target_h

    if aspect > target_aspect:
        new_h = target_h
        new_w = int(target_h * aspect)
    else:
        new_w = target_w
        new_h = int(target_w / aspect)

    scaled_img = base_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    crop_x = (new_w - target_w) // 2
    crop_y = (new_h - target_h) // 2
    buffer_img = scaled_img.crop((crop_x, crop_y, crop_x + target_w, crop_y + target_h))

    # Pre-calculate bottom gradient vignette
    vignette_height = int(height * 0.40)
    vignette = Image.new("RGBA", (width, vignette_height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    for y in range(vignette_height):
        alpha = int(180 * (y / vignette_height) ** 1.3)
        v_draw.line([(0, y), (width, y)], fill=(6, 10, 18, alpha))

    # Capsule card layout
    card_margin_x = int(width * 0.05)
    card_margin_bottom = int(height * 0.05)

    card_w = int(width * 0.88)
    card_h = int(height * 0.22)
    final_card_x = card_margin_x
    final_card_y = height - card_h - card_margin_bottom

    max_dx = target_w - width
    max_dy = target_h - height

    def get_crop_rect(progress_smooth: float) -> Tuple[int, int, int, int]:
        if motion_type == "zoom_in":
            cur_scale = 1.12 - 0.12 * progress_smooth
            crop_w = int(width * cur_scale)
            crop_h = int(height * cur_scale)
            cx = (target_w - crop_w) * 0.5
            cy = (target_h - crop_h) * 0.5
        elif motion_type == "zoom_out":
            cur_scale = 1.00 + 0.12 * progress_smooth
            crop_w = int(width * cur_scale)
            crop_h = int(height * cur_scale)
            cx = (target_w - crop_w) * 0.5
            cy = (target_h - crop_h) * 0.5
        elif motion_type == "pan_left":
            cur_scale = 1.06
            crop_w = int(width * cur_scale)
            crop_h = int(height * cur_scale)
            cx = (target_w - crop_w) * (0.80 - 0.60 * progress_smooth)
            cy = (target_h - crop_h) * 0.5
        else:  # pan_right
            cur_scale = 1.06
            crop_w = int(width * cur_scale)
            crop_h = int(height * cur_scale)
            cx = (target_w - crop_w) * (0.20 + 0.60 * progress_smooth)
            cy = (target_h - crop_h) * 0.5

        cx = int(max(0, min(max_dx, cx)))
        cy = int(max(0, min(max_dy, cy)))
        return cx, cy, crop_w, crop_h

    # Snappy 0.6s reveal for the label right when the photo begins
    anim_in_dur = 0.65
    anim_out_dur = 0.45

    def make_frame(t: float) -> np.ndarray:
        raw_progress = min(1.0, max(0.0, t / max(0.1, duration)))
        smooth_progress = ease_in_out_sine(raw_progress)

        # 1. Ken Burns Crop
        cx, cy, cw, ch = get_crop_rect(smooth_progress)
        cropped = buffer_img.crop((cx, cy, cx + cw, cy + ch))
        frame_img = cropped.resize((width, height), Image.Resampling.BILINEAR).convert("RGBA")

        # 2. Subtle Vignette
        frame_img.paste(vignette, (0, height - vignette_height), vignette)

        # 3. Label Entrance: Slide-up & Fade-in locked to photo arrival
        if t < anim_in_dur:
            in_prog = ease_out_expo(t / anim_in_dur)
            offset_y = int((1.0 - in_prog) * 35)
            card_alpha = in_prog
        elif t > (duration - anim_out_dur):
            out_prog = max(0.0, min(1.0, (duration - t) / anim_out_dur))
            offset_y = 0
            card_alpha = out_prog
        else:
            offset_y = 0
            card_alpha = 1.0

        current_card_y = final_card_y + offset_y

        # Draw Modern Capsule
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw_modern_capsule_label(
            draw=draw,
            width=width,
            height=height,
            scene=scene,
            card_x=final_card_x,
            card_y=current_card_y,
            card_w=card_w,
            card_h=card_h,
            alpha_mult=card_alpha,
        )

        frame_img.alpha_composite(overlay)
        return np.array(frame_img.convert("RGB"))

    return VideoClip(make_frame, duration=duration)


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
    Renders the complete property tour MP4 video with:
    - Precise 1:1 synchronization between narration, feature label, and photo switch timing.
    - Modern capsule HUD labels.
    - Synchronized Ken Burns camera choreography.
    - Mixed neural voiceover and ducked ambient soundtrack.
    
    Returns:
        Absolute path to the exported MP4 video file.
    """
    out_path = OUTPUT_DIR / output_filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback(0.05, "Synchronizing photo durations with feature speech...")

    motion_cycle = ["zoom_in", "pan_right", "zoom_out", "pan_left"]
    num_scenes = len(scene_audio_data)

    scene_clips = []
    for idx, (scene, audio_path, duration) in enumerate(scene_audio_data):
        motion = motion_cycle[idx % len(motion_cycle)]
        
        # Build scene with Ken Burns motion and synchronized capsule label
        clip = build_ken_burns_scene_clip(
            scene=scene,
            duration=duration,
            width=width,
            height=height,
            motion_type=motion,
            property_name=prop.name,
        )
        scene_clips.append(clip)

        if progress_callback:
            pct = 0.05 + 0.45 * ((idx + 1) / num_scenes)
            progress_callback(pct, f"Built Scene {idx + 1}/{num_scenes}: '{scene.caption_title}' ({duration:.1f}s)...")

    # Concatenate clips sequentially so each photo and its feature label change
    # in lockstep with the narration soundtrack
    if progress_callback:
        progress_callback(0.55, "Assembling synchronized multi-scene timeline...")

    final_video = concatenate_videoclips(scene_clips, method="compose")

    # Attach master soundtrack
    if progress_callback:
        progress_callback(0.65, "Attaching synchronized neural soundtrack...")

    soundtrack_clip = AudioFileClip(master_audio_path)
    final_video = final_video.with_audio(soundtrack_clip)

    # Export to MP4 with H.264 & AAC
    if progress_callback:
        progress_callback(0.75, "Encoding synchronized H.264 MP4 video...")

    final_video.write_videofile(
        str(out_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        threads=4,
        logger=None,  # Clean output
    )

    # Clean up resources
    soundtrack_clip.close()
    final_video.close()
    for c in scene_clips:
        try:
            c.close()
        except Exception:
            pass

    if progress_callback:
        progress_callback(1.0, "Video rendering complete!")

    return str(out_path.resolve())
