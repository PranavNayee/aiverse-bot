"""Code-based animation generation for educational content (No AI images needed)"""
import os, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from util import log

# Canvas size for Instagram Reels (9:16)
W, H = 1080, 1920
FPS = 30

# Colors (modern, clean palette)
COLOR_BG = (26, 26, 46)          # Dark blue background
COLOR_PRIMARY = (99, 102, 241)    # Indigo (main accent)
COLOR_SECONDARY = (251, 191, 36)  # Amber (highlights)
COLOR_TEXT = (255, 255, 255)      # White text
COLOR_ACCENT = (34, 197, 94)      # Green (success/emphasis)
COLOR_MUTED = (156, 163, 175)     # Gray (secondary text)

def get_font(size, bold=False):
    """Get font for text rendering"""
    try:
        # Try to load Noto Sans (supports Hindi + English)
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", size)
    except:
        try:
            # Fallback to Devanagari font for Hinglish
            return ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf", size)
        except:
            # Last resort: default font
            return ImageFont.load_default()

def create_title_card(text, subtitle="", duration=3.0):
    """Create animated title card with text
    
    Args:
        text: Main title (Hinglish)
        subtitle: Optional subtitle
        duration: Duration in seconds
    
    Returns:
        Path to generated video
    """
    nframes = int(duration * FPS)
    output = "work/title_card.mp4"
    
    frames = []
    for f in range(nframes):
        # Create frame
        img = Image.new('RGB', (W, H), COLOR_BG)
        draw = ImageDraw.Draw(img)
        
        # Fade in animation
        alpha = min(1.0, f / (FPS * 0.5))  # 0.5s fade in
        
        # Draw title
        font_title = get_font(90, bold=True)
        
        # Text centering (approximate)
        bbox = draw.textbbox((0, 0), text, font=font_title)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (W - text_w) // 2
        y = (H - text_h) // 2 - 100
        
        # Add glow effect
        if alpha > 0.5:
            glow_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_img)
            glow_color = (*COLOR_PRIMARY, int(100 * alpha))
            for offset in [4, 8, 12]:
                glow_draw.text((x, y), text, font=font_title, fill=glow_color)
            glow_img = glow_img.filter(ImageFilter.GaussianBlur(10))
            img.paste(glow_img, (0, 0), glow_img)
        
        # Draw main text
        text_color = (*COLOR_TEXT, int(255 * alpha))
        draw.text((x, y), text, font=font_title, fill=text_color)
        
        # Draw subtitle if provided
        if subtitle:
            font_sub = get_font(50)
            sub_bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
            sub_w = sub_bbox[2] - sub_bbox[0]
            sub_x = (W - sub_w) // 2
            sub_y = y + text_h + 40
            sub_color = (*COLOR_MUTED, int(255 * alpha))
            draw.text((sub_x, sub_y), subtitle, font=font_sub, fill=sub_color)
        
        # Convert to cv2 format
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        frames.append(frame)
    
    # Write video
    write_video(frames, output, duration)
    log(f"Title card created: {duration}s")
    return output

def create_text_animation(text_lines, duration=5.0, animation_type="fade"):
    """Create animated text display
    
    Args:
        text_lines: List of text lines to animate
        duration: Duration in seconds
        animation_type: "fade", "slide", "typewriter"
    
    Returns:
        Path to generated video
    """
    nframes = int(duration * FPS)
    output = f"work/text_{animation_type}.mp4"
    
    frames = []
    font = get_font(70)
    line_height = 100
    
    for f in range(nframes):
        img = Image.new('RGB', (W, H), COLOR_BG)
        draw = ImageDraw.Draw(img)
        
        progress = f / nframes
        
        # Draw each line with animation
        for i, line in enumerate(text_lines):
            y_pos = 400 + i * line_height
            
            if animation_type == "fade":
                # Stagger fade in
                line_progress = max(0, min(1, (progress - i * 0.15) * 2))
                alpha = int(255 * line_progress)
            elif animation_type == "slide":
                # Slide from right
                line_progress = max(0, min(1, (progress - i * 0.1) * 1.5))
                x_offset = int((1 - line_progress) * 300)
                alpha = int(255 * line_progress)
            else:  # typewriter
                chars_to_show = int(len(line) * progress)
                line = line[:chars_to_show]
                alpha = 255
                x_offset = 0
            
            # Center text
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x = (W - text_w) // 2 + (x_offset if animation_type == "slide" else 0)
            
            color = (*COLOR_TEXT, alpha)
            draw.text((x, y_pos), line, font=font, fill=color)
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        frames.append(frame)
    
    write_video(frames, output, duration)
    log(f"Text animation created: {animation_type}, {duration}s")
    return output

def create_neural_network_viz(duration=8.0):
    """Create animated neural network diagram
    
    Shows:
    - Input layer (3 nodes)
    - Hidden layer (5 nodes)
    - Output layer (2 nodes)
    - Animated connections with data flow
    """
    nframes = int(duration * FPS)
    output = "work/neural_net.mp4"
    
    # Network structure
    layers = [3, 5, 2]  # nodes per layer
    layer_x = [300, W//2, W-300]  # x positions
    
    frames = []
    for f in range(nframes):
        img = Image.new('RGB', (W, H), COLOR_BG)
        draw = ImageDraw.Draw(img)
        
        progress = f / nframes
        
        # Draw title
        font_title = get_font(60, bold=True)
        draw.text((100, 200), "Neural Network", font=font_title, fill=COLOR_TEXT)
        
        # Draw connections first (so nodes are on top)
        for layer_idx in range(len(layers) - 1):
            for i in range(layers[layer_idx]):
                for j in range(layers[layer_idx + 1]):
                    # Node positions
                    x1 = layer_x[layer_idx]
                    y1 = H//2 + (i - layers[layer_idx]/2) * 150
                    x2 = layer_x[layer_idx + 1]
                    y2 = H//2 + (j - layers[layer_idx + 1]/2) * 150
                    
                    # Animated connection strength
                    strength = 0.3 + 0.7 * abs(np.sin(progress * np.pi * 2 + i + j))
                    alpha = int(100 * strength)
                    color = (*COLOR_PRIMARY, alpha)
                    
                    # Draw line
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
        
        # Draw nodes
        for layer_idx, num_nodes in enumerate(layers):
            x = layer_x[layer_idx]
            for i in range(num_nodes):
                y = H//2 + (i - num_nodes/2) * 150
                
                # Animated activation
                activation = 0.5 + 0.5 * np.sin(progress * np.pi * 4 + layer_idx + i)
                
                # Outer glow
                for r in [50, 45, 40]:
                    alpha = int(30 * activation)
                    glow_color = (*COLOR_ACCENT, alpha)
                    draw.ellipse([x-r, y-r, x+r, y+r], fill=glow_color)
                
                # Node circle
                radius = 35
                node_color = COLOR_PRIMARY if activation > 0.6 else COLOR_MUTED
                draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=node_color)
        
        # Labels
        font_label = get_font(40)
        draw.text((layer_x[0]-50, H//2 + 200), "Input", font=font_label, fill=COLOR_MUTED, anchor="mm")
        draw.text((layer_x[1], H//2 + 250), "Hidden", font=font_label, fill=COLOR_MUTED, anchor="mm")
        draw.text((layer_x[2]+50, H//2 + 200), "Output", font=font_label, fill=COLOR_MUTED, anchor="mm")
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        frames.append(frame)
    
    write_video(frames, output, duration)
    log(f"Neural network viz created: {duration}s")
    return output

def create_process_flow(steps, duration=10.0):
    """Create animated process flow diagram
    
    Args:
        steps: List of step names (e.g., ["Data", "Model", "Prediction"])
        duration: Duration in seconds
    """
    nframes = int(duration * FPS)
    output = "work/process_flow.mp4"
    
    frames = []
    font_step = get_font(55, bold=True)
    num_steps = len(steps)
    
    for f in range(nframes):
        img = Image.new('RGB', (W, H), COLOR_BG)
        draw = ImageDraw.Draw(img)
        
        progress = f / nframes
        
        # Draw steps
        step_y = 500
        step_spacing = 300
        
        for i, step in enumerate(steps):
            x = W // 2
            y = step_y + i * step_spacing
            
            # Reveal animation (stagger)
            step_progress = max(0, min(1, (progress - i * 0.2) * 2))
            
            if step_progress > 0:
                # Box
                box_w, box_h = 400, 120
                alpha = int(255 * step_progress)
                box_color = (*COLOR_PRIMARY, alpha)
                draw.rounded_rectangle(
                    [x - box_w//2, y - box_h//2, x + box_w//2, y + box_h//2],
                    radius=20, fill=box_color
                )
                
                # Text
                text_color = (*COLOR_TEXT, alpha)
                draw.text((x, y), step, font=font_step, fill=text_color, anchor="mm")
                
                # Arrow to next step
                if i < num_steps - 1 and step_progress > 0.8:
                    arrow_y = y + box_h//2 + 50
                    arrow_color = (*COLOR_SECONDARY, alpha)
                    draw.polygon([
                        (x, arrow_y),
                        (x - 30, arrow_y + 50),
                        (x + 30, arrow_y + 50)
                    ], fill=arrow_color)
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        frames.append(frame)
    
    write_video(frames, output, duration)
    log(f"Process flow created: {num_steps} steps, {duration}s")
    return output

def create_comparison(left_text, right_text, left_title="Before", right_title="After", duration=6.0):
    """Create before/after or comparison visualization"""
    nframes = int(duration * FPS)
    output = "work/comparison.mp4"
    
    frames = []
    font_title = get_font(50, bold=True)
    font_text = get_font(45)
    
    for f in range(nframes):
        img = Image.new('RGB', (W, H), COLOR_BG)
        draw = ImageDraw.Draw(img)
        
        progress = f / nframes
        
        # Vertical split
        mid_x = W // 2
        
        # Left side
        if progress > 0.2:
            draw.rectangle([50, 400, mid_x - 50, 1500], fill=COLOR_PRIMARY)
            draw.text((mid_x // 2, 500), left_title, font=font_title, fill=COLOR_TEXT, anchor="mm")
            draw.text((mid_x // 2, 700), left_text, font=font_text, fill=COLOR_TEXT, anchor="mm")
        
        # Right side
        if progress > 0.5:
            draw.rectangle([mid_x + 50, 400, W - 50, 1500], fill=COLOR_ACCENT)
            draw.text((mid_x + W // 4, 500), right_title, font=font_title, fill=COLOR_TEXT, anchor="mm")
            draw.text((mid_x + W // 4, 700), right_text, font=font_text, fill=COLOR_TEXT, anchor="mm")
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        frames.append(frame)
    
    write_video(frames, output, duration)
    log(f"Comparison viz created: {duration}s")
    return output

def write_video(frames, output_path, duration):
    """Write frames to video file using ffmpeg"""
    temp_frames = "work/temp_frames_%04d.png"
    
    # Save frames as images
    for i, frame in enumerate(frames):
        cv2.imwrite(f"work/temp_frames_{i:04d}.png", frame)
    
    # Use ffmpeg to create video
    cmd = [
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", temp_frames,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        output_path
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)
    
    # Cleanup temp frames
    import glob
    for f in glob.glob("work/temp_frames_*.png"):
        os.remove(f)

if __name__ == "__main__":
    # Test animations
    print("Testing animation generation...")
    os.makedirs("work", exist_ok=True)
    
    print("1. Title card...")
    create_title_card("Machine Learning", "Lesson #2", 3.0)
    
    print("2. Text animation...")
    create_text_animation([
        "Data collect karo",
        "Pattern dhundho",
        "Prediction karo"
    ], 5.0, "fade")
    
    print("3. Neural network...")
    create_neural_network_viz(8.0)
    
    print("4. Process flow...")
    create_process_flow(["Data", "Training", "Model", "Prediction"], 10.0)
    
    print("✅ All animations generated in work/")
