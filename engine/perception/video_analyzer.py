"""
SpaceAI FC - Video Tactical Analysis
======================================
Phase 4 Module 1: Extract player positions from video clips.

Pipeline: video → frame extraction → person detection → tracking →
          team classification → homography → pitch coordinates

Supports:
    - Local video files (mp4, avi, mov, mkv)
    - YouTube downloads via yt-dlp
    - Synthetic demo data for testing without video
    - Individual player tracking (trajectory, heatmap, speed)

Dependencies (optional — falls back to synthetic demo):
    - ultralytics  (YOLOv8 person detection)
    - opencv-python (video processing)
    - yt-dlp        (YouTube download)

Safety:
    - File format validation (.mp4, .avi, .mov, .mkv only)
    - Max file size 500 MB
    - URL sanitization for yt-dlp
    - Temp directory cleanup after processing
    - No face recognition or personal identification
"""

import os
import sys
import math
import random
import tempfile
import shutil
import re
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap

# ── Optional dependency imports ─────────────────────────────────
# Each is guarded so the module works in synthetic-only mode

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

# Try mplsoccer for nice pitch drawing (already in requirements)
try:
    from mplsoccer import Pitch
    HAS_MPLSOCCER = True
except ImportError:
    HAS_MPLSOCCER = False


# ════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════

ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}
MAX_FILE_SIZE_MB = 500
PITCH_LENGTH = 120
PITCH_WIDTH = 80

ACTION_NAMES = {
    0: 'keep_current', 1: 'press_higher', 2: 'drop_deeper',
    3: 'attacking_formation', 4: 'defensive_formation',
    5: 'exploit_width', 6: 'play_through_center',
    7: 'increase_tempo', 8: 'slow_down',
}


# ════════════════════════════════════════════════════════════════
# Synthetic Data Generator
# ════════════════════════════════════════════════════════════════

class SyntheticDataGenerator:
    """
    Generate realistic fake tracking data for demo/testing.
    
    Creates N frames of 22 players (11 per team) with movement
    patterns that mimic real football: defenders hold line,
    midfielders oscillate, attackers push forward.
    """
    
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)
    
    def generate(self, n_frames=100, n_players_per_team=11):
        """
        Generate synthetic tracking data.
        
        Returns:
            dict with keys:
                'frames': list of frame dicts, each containing:
                    'frame_idx': int
                    'team_a': list of player dicts {id, x, y, team}
                    'team_b': list of player dicts {id, x, y, team}
                    'ball': {x, y}
                'metadata': dict with generation params
        """
        # Initial positions — Barcelona-style 4-2-3-1
        team_a_init = self._get_formation_positions(
            'left', n_players_per_team)
        # Real Madrid-style 4-3-3
        team_b_init = self._get_formation_positions(
            'right', n_players_per_team)
        
        frames = []
        team_a_pos = [dict(p) for p in team_a_init]
        team_b_pos = [dict(p) for p in team_b_init]
        ball_x, ball_y = 60.0, 40.0
        
        for frame_idx in range(n_frames):
            # Update player positions with role-based movement
            team_a_pos = self._update_positions(
                team_a_pos, ball_x, ball_y, 'left', frame_idx)
            team_b_pos = self._update_positions(
                team_b_pos, ball_x, ball_y, 'right', frame_idx)
            
            # Update ball — biased random walk toward attacking players
            ball_x += self.np_rng.normal(0.3 * math.sin(frame_idx * 0.1), 1.5)
            ball_y += self.np_rng.normal(0, 1.0)
            ball_x = max(5, min(115, ball_x))
            ball_y = max(5, min(75, ball_y))
            
            frame = {
                'frame_idx': frame_idx,
                'team_a': [{'id': p['id'], 'x': round(p['x'], 1),
                            'y': round(p['y'], 1), 'team': 'A'}
                           for p in team_a_pos],
                'team_b': [{'id': p['id'], 'x': round(p['x'], 1),
                            'y': round(p['y'], 1), 'team': 'B'}
                           for p in team_b_pos],
                'ball': {'x': round(ball_x, 1), 'y': round(ball_y, 1)},
            }
            frames.append(frame)
        
        return {
            'frames': frames,
            'metadata': {
                'source': 'synthetic',
                'n_frames': n_frames,
                'n_players_per_team': n_players_per_team,
                'fps': 25,
            }
        }
    
    def _get_formation_positions(self, side, n_players):
        """Get initial formation positions for a team."""
        if n_players >= 11:
            if side == 'left':
                # 4-2-3-1 on left side
                positions = [
                    {'id': 0, 'x': 5,  'y': 40, 'role': 'GK'},
                    {'id': 1, 'x': 25, 'y': 70, 'role': 'DEF'},
                    {'id': 2, 'x': 22, 'y': 52, 'role': 'DEF'},
                    {'id': 3, 'x': 22, 'y': 28, 'role': 'DEF'},
                    {'id': 4, 'x': 25, 'y': 10, 'role': 'DEF'},
                    {'id': 5, 'x': 42, 'y': 48, 'role': 'MID'},
                    {'id': 6, 'x': 42, 'y': 32, 'role': 'MID'},
                    {'id': 7, 'x': 60, 'y': 68, 'role': 'ATT'},
                    {'id': 8, 'x': 58, 'y': 40, 'role': 'MID'},
                    {'id': 9, 'x': 60, 'y': 12, 'role': 'ATT'},
                    {'id': 10, 'x': 75, 'y': 40, 'role': 'ATT'},
                ]
            else:
                # 4-3-3 on right side
                positions = [
                    {'id': 11, 'x': 115, 'y': 40, 'role': 'GK'},
                    {'id': 12, 'x': 95,  'y': 70, 'role': 'DEF'},
                    {'id': 13, 'x': 98,  'y': 52, 'role': 'DEF'},
                    {'id': 14, 'x': 98,  'y': 28, 'role': 'DEF'},
                    {'id': 15, 'x': 95,  'y': 10, 'role': 'DEF'},
                    {'id': 16, 'x': 78,  'y': 55, 'role': 'MID'},
                    {'id': 17, 'x': 75,  'y': 40, 'role': 'MID'},
                    {'id': 18, 'x': 78,  'y': 25, 'role': 'MID'},
                    {'id': 19, 'x': 55,  'y': 65, 'role': 'ATT'},
                    {'id': 20, 'x': 50,  'y': 40, 'role': 'ATT'},
                    {'id': 21, 'x': 55,  'y': 15, 'role': 'ATT'},
                ]
        else:
            # Simplified positions for smaller team sizes
            positions = []
            for i in range(n_players):
                if side == 'left':
                    x = 10 + (i / max(n_players - 1, 1)) * 60
                    y = 20 + (i % 3) * 20
                    pid = i
                else:
                    x = 110 - (i / max(n_players - 1, 1)) * 60
                    y = 20 + (i % 3) * 20
                    pid = n_players + i
                role = 'GK' if i == 0 else ('DEF' if i < 3 else
                       ('MID' if i < 6 else 'ATT'))
                positions.append({'id': pid, 'x': x, 'y': y, 'role': role})
        
        return positions[:n_players]
    
    def _update_positions(self, players, ball_x, ball_y, side, frame_idx):
        """Update player positions with role-based movement patterns."""
        updated = []
        for p in players:
            dx = self.np_rng.normal(0, 0.8)
            dy = self.np_rng.normal(0, 0.8)
            
            role = p.get('role', 'MID')
            
            if role == 'GK':
                # Goalkeeper — small movements around starting position
                dx *= 0.2
                dy *= 0.3
                # Stay near goal
                if side == 'left':
                    p['x'] = max(2, min(12, p['x'] + dx))
                else:
                    p['x'] = max(108, min(118, p['x'] + dx))
                p['y'] = max(30, min(50, p['y'] + dy))
            
            elif role == 'DEF':
                # Defenders — hold line, shift toward ball
                ball_pull = 0.02 * (ball_y - p['y'])
                dy += ball_pull
                # Slight x movement tracking ball
                if side == 'left':
                    target_x = max(15, min(40, ball_x * 0.3 + 10))
                else:
                    target_x = max(80, min(105, ball_x * 0.3 + 70))
                dx += 0.05 * (target_x - p['x'])
                p['x'] = max(5, min(115, p['x'] + dx))
                p['y'] = max(3, min(77, p['y'] + dy))
            
            elif role == 'MID':
                # Midfielders — oscillate between attack and defense
                osc = 3.0 * math.sin(frame_idx * 0.08 + p['id'] * 0.5)
                dx += osc * 0.3
                ball_pull_y = 0.03 * (ball_y - p['y'])
                dy += ball_pull_y
                p['x'] = max(10, min(110, p['x'] + dx))
                p['y'] = max(5, min(75, p['y'] + dy))
            
            elif role == 'ATT':
                # Attackers — push forward, seek space
                if side == 'left':
                    dx += 0.15  # bias forward
                else:
                    dx -= 0.15  # bias forward (other direction)
                # Move toward ball laterally
                ball_pull_y = 0.04 * (ball_y - p['y'])
                dy += ball_pull_y
                p['x'] = max(20, min(115, p['x'] + dx))
                p['y'] = max(5, min(75, p['y'] + dy))
            
            updated.append(p)
        
        return updated


# ════════════════════════════════════════════════════════════════
# Video Analyzer
# ════════════════════════════════════════════════════════════════

class VideoAnalyzer:
    """
    Extract player positions from video using YOLOv8 + tracking.
    
    Full pipeline:
        1. Load video (local file or YouTube URL)
        2. Extract frames at configurable sample rate
        3. Detect persons using YOLOv8
        4. Track players across frames (centroid tracking)
        5. Classify into teams using jersey color (HSV)
        6. Transform pixel coordinates to pitch coordinates (homography)
        7. Output: list of frames with player positions
    
    Falls back to synthetic data if dependencies are missing.
    """
    
    def __init__(self, max_file_size_mb=MAX_FILE_SIZE_MB):
        self.max_file_size_mb = max_file_size_mb
        self.video_path = None
        self.frames = []
        self.detections = []  # per-frame detection results
        self.tracking_data = None  # final tracked + classified data
        self.homography_matrix = None
        self.reference_pixel_pts = None
        self.reference_pitch_pts = None
        self._temp_dir = None
        self._model = None
        
        # Team colors for classification (HSV ranges)
        self.team_a_hsv = None  # (lower, upper) HSV bounds
        self.team_b_hsv = None
        self.team_a_name = "Team A"
        self.team_b_name = "Team B"
        self.team_a_color = "#a50044"
        self.team_b_color = "#ffffff"
    
    # ── Video Loading ───────────────────────────────────────────
    
    def validate_video_path(self, path):
        """Validate video file path for format and size."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Video file not found: {path}")
        
        ext = os.path.splitext(path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid video format '{ext}'. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            raise ValueError(
                f"Video file too large ({size_mb:.0f} MB). "
                f"Maximum: {self.max_file_size_mb} MB"
            )
        
        return True
    
    def load_video(self, path):
        """
        Load a local video file.
        
        Args:
            path: Path to video file (.mp4, .avi, .mov, .mkv)
        """
        if not HAS_CV2:
            raise ImportError(
                "opencv-python required for video loading. "
                "Run: pip install opencv-python"
            )
        
        self.validate_video_path(path)
        self.video_path = path
        print(f"  Loaded video: {os.path.basename(path)}")
        
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        print(f"  Resolution: {w}x{h}  FPS: {fps:.1f}  Frames: {total}")
        return {'fps': fps, 'total_frames': total, 'width': w, 'height': h}
    
    def download_youtube(self, url, output_dir=None):
        """
        Download a YouTube video using yt-dlp.
        
        Args:
            url: YouTube URL (sanitized before use)
            output_dir: Directory to save to (uses temp dir if None)
        
        Returns:
            Path to downloaded video file
        """
        if not HAS_YTDLP:
            raise ImportError(
                "yt-dlp required for YouTube downloads. "
                "Run: pip install yt-dlp"
            )
        
        # Sanitize URL — only allow youtube.com and youtu.be domains
        url = url.strip()
        if not re.match(
            r'^https?://(www\.)?(youtube\.com|youtu\.be)/', url
        ):
            raise ValueError(
                "Invalid YouTube URL. Only youtube.com and youtu.be are allowed."
            )
        
        if output_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix='spaceai_video_')
            output_dir = self._temp_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        print(f"  Downloading from YouTube...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        self.video_path = filename
        print(f"  Downloaded: {os.path.basename(filename)}")
        return filename
    
    # ── Homography ──────────────────────────────────────────────
    
    def set_reference_points(self, pixel_points, pitch_points):
        """
        Define reference point pairs for homography transformation.
        
        Args:
            pixel_points: list of (px, py) in video frame coordinates
            pitch_points: list of (x, y) in pitch coordinates (0-120, 0-80)
        
        At least 4 point pairs are required.
        """
        if len(pixel_points) < 4 or len(pitch_points) < 4:
            raise ValueError("At least 4 reference point pairs required.")
        if len(pixel_points) != len(pitch_points):
            raise ValueError("pixel_points and pitch_points must have same length.")
        
        self.reference_pixel_pts = np.array(pixel_points, dtype=np.float32)
        self.reference_pitch_pts = np.array(pitch_points, dtype=np.float32)
        print(f"  Set {len(pixel_points)} reference points for homography")
    
    def compute_homography(self):
        """Compute homography matrix from reference points."""
        if not HAS_CV2:
            raise ImportError("opencv-python required for homography.")
        
        if self.reference_pixel_pts is None:
            raise ValueError("Set reference points first with set_reference_points()")
        
        H, mask = cv2.findHomography(
            self.reference_pixel_pts,
            self.reference_pitch_pts,
            cv2.RANSAC, 5.0
        )
        self.homography_matrix = H
        inliers = mask.sum() if mask is not None else len(self.reference_pixel_pts)
        print(f"  Homography computed ({inliers}/{len(self.reference_pixel_pts)} inliers)")
        return H
    
    def pixel_to_pitch(self, pixel_coords):
        """
        Transform pixel coordinates to pitch coordinates using homography.
        
        Args:
            pixel_coords: numpy array of shape (N, 2) or (2,)
        
        Returns:
            numpy array of pitch coordinates
        """
        if self.homography_matrix is None:
            # Default: simple linear mapping assuming full-pitch view
            # This is a rough approximation for demo purposes
            coords = np.atleast_2d(pixel_coords).astype(np.float32)
            # Assume video is 1920x1080 showing full pitch
            pitch_x = coords[:, 0] / 1920.0 * PITCH_LENGTH
            pitch_y = coords[:, 1] / 1080.0 * PITCH_WIDTH
            return np.column_stack([pitch_x, pitch_y])
        
        coords = np.atleast_2d(pixel_coords).astype(np.float32)
        # Reshape for perspectiveTransform: (1, N, 2)
        reshaped = coords.reshape(1, -1, 2)
        transformed = cv2.perspectiveTransform(reshaped, self.homography_matrix)
        return transformed.reshape(-1, 2)
    
    # ── Detection & Tracking ───────────────────────────────────
    
    def detect_players(self, frame):
        """
        Detect persons in a single frame using YOLOv8.
        
        Args:
            frame: numpy array (H, W, 3) BGR image
        
        Returns:
            list of dicts with keys: bbox (x1,y1,x2,y2), center (cx,cy),
            confidence, crop (BGR sub-image for color classification)
        """
        if not HAS_YOLO:
            raise ImportError(
                "ultralytics required for detection. "
                "Run: pip install ultralytics"
            )
        
        if self._model is None:
            self._model = YOLO('yolov8n.pt')  # nano model for speed
        
        results = self._model(frame, verbose=False, classes=[0])  # class 0 = person
        
        detections = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                
                if conf < 0.3:
                    continue
                
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                
                # Extract crop for color classification
                x1i, y1i = int(max(0, x1)), int(max(0, y1))
                x2i, y2i = int(min(frame.shape[1], x2)), int(min(frame.shape[0], y2))
                crop = frame[y1i:y2i, x1i:x2i].copy() if y2i > y1i and x2i > x1i else None
                
                detections.append({
                    'bbox': (float(x1), float(y1), float(x2), float(y2)),
                    'center': (float(cx), float(cy)),
                    'confidence': conf,
                    'crop': crop,
                })
        
        return detections
    
    def _centroid_distance(self, c1, c2):
        """Euclidean distance between two centroids."""
        return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
    
    def track_players(self, frame_detections, max_distance=80):
        """
        Simple centroid-based tracking across frames.
        
        Assigns consistent IDs to detections by matching closest
        centroids between consecutive frames.
        
        Args:
            frame_detections: list of per-frame detection lists
            max_distance: max pixel distance to consider same player
        
        Returns:
            list of per-frame tracked detection lists with 'track_id'
        """
        tracked_frames = []
        next_id = 0
        prev_tracks = {}  # track_id -> last centroid
        
        for frame_dets in frame_detections:
            current_tracks = {}
            used_dets = set()
            assignments = {}
            
            # Match existing tracks to new detections
            for tid, prev_center in prev_tracks.items():
                best_dist = max_distance
                best_idx = -1
                for i, det in enumerate(frame_dets):
                    if i in used_dets:
                        continue
                    dist = self._centroid_distance(prev_center, det['center'])
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = i
                
                if best_idx >= 0:
                    assignments[best_idx] = tid
                    used_dets.add(best_idx)
                    current_tracks[tid] = frame_dets[best_idx]['center']
            
            # Create new tracks for unmatched detections
            tracked_dets = []
            for i, det in enumerate(frame_dets):
                d = dict(det)
                if i in assignments:
                    d['track_id'] = assignments[i]
                else:
                    d['track_id'] = next_id
                    current_tracks[next_id] = det['center']
                    next_id += 1
                tracked_dets.append(d)
            
            tracked_frames.append(tracked_dets)
            prev_tracks = current_tracks
        
        return tracked_frames
    
    # ── Team Classification ────────────────────────────────────
    
    def set_team_colors(self, team_a_color_bgr, team_b_color_bgr,
                        team_a_name="Team A", team_b_name="Team B",
                        team_a_display="#a50044", team_b_display="#ffffff",
                        tolerance=30):
        """
        Set approximate jersey colors for team classification.
        
        Args:
            team_a_color_bgr: (B, G, R) approximate jersey color
            team_b_color_bgr: (B, G, R) approximate jersey color
            tolerance: HSV hue tolerance for matching
        """
        self.team_a_name = team_a_name
        self.team_b_name = team_b_name
        self.team_a_color = team_a_display
        self.team_b_color = team_b_display
        
        if HAS_CV2:
            # Convert BGR to HSV
            a_hsv = cv2.cvtColor(
                np.uint8([[team_a_color_bgr]]), cv2.COLOR_BGR2HSV)[0, 0]
            b_hsv = cv2.cvtColor(
                np.uint8([[team_b_color_bgr]]), cv2.COLOR_BGR2HSV)[0, 0]
            
            self.team_a_hsv = (
                np.array([max(0, a_hsv[0] - tolerance), 40, 40]),
                np.array([min(180, a_hsv[0] + tolerance), 255, 255])
            )
            self.team_b_hsv = (
                np.array([max(0, b_hsv[0] - tolerance), 40, 40]),
                np.array([min(180, b_hsv[0] + tolerance), 255, 255])
            )
    
    def classify_team(self, crop):
        """
        Classify a detected person's team using jersey color.
        
        Args:
            crop: BGR sub-image of detected person
        
        Returns:
            'A', 'B', or 'other'
        """
        if crop is None or not HAS_CV2 or self.team_a_hsv is None:
            return 'other'
        
        # Use upper body (top 40%) for jersey color
        h = crop.shape[0]
        jersey = crop[:int(h * 0.4), :]
        
        if jersey.size == 0:
            return 'other'
        
        hsv = cv2.cvtColor(jersey, cv2.COLOR_BGR2HSV)
        
        mask_a = cv2.inRange(hsv, self.team_a_hsv[0], self.team_a_hsv[1])
        mask_b = cv2.inRange(hsv, self.team_b_hsv[0], self.team_b_hsv[1])
        
        ratio_a = np.sum(mask_a > 0) / max(mask_a.size, 1)
        ratio_b = np.sum(mask_b > 0) / max(mask_b.size, 1)
        
        if ratio_a > 0.15 and ratio_a > ratio_b:
            return 'A'
        elif ratio_b > 0.15 and ratio_b > ratio_a:
            return 'B'
        return 'other'
    
    def classify_teams(self, tracked_frames):
        """
        Classify all tracked detections into teams.
        
        Args:
            tracked_frames: output from track_players()
        
        Returns:
            Same structure with 'team' field added to each detection
        """
        for frame_dets in tracked_frames:
            for det in frame_dets:
                det['team'] = self.classify_team(det.get('crop'))
        return tracked_frames
    
    # ── Full Pipeline ──────────────────────────────────────────
    
    def analyze_video(self, sample_rate=5, max_frames=200):
        """
        Run the full video analysis pipeline.
        
        Args:
            sample_rate: process every Nth frame
            max_frames: maximum frames to process
        
        Returns:
            dict with tracking data in pitch coordinates
        """
        if not HAS_CV2 or not HAS_YOLO:
            print("  ⚠ Video dependencies not available. Using synthetic data.")
            return self.run_synthetic_demo()
        
        if self.video_path is None:
            raise ValueError("No video loaded. Call load_video() or download_youtube() first.")
        
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"  Analyzing video: {total} frames, sampling every {sample_rate}th...")
        
        # Step 1: Extract frames and detect
        frame_detections = []
        frame_indices = []
        processed = 0
        
        for i in range(total):
            ret, frame = cap.read()
            if not ret:
                break
            
            if i % sample_rate != 0:
                continue
            
            if processed >= max_frames:
                break
            
            dets = self.detect_players(frame)
            frame_detections.append(dets)
            frame_indices.append(i)
            processed += 1
            
            if processed % 20 == 0:
                print(f"    Processed {processed} frames, "
                      f"{len(dets)} players detected in latest")
        
        cap.release()
        print(f"  Detection complete: {processed} frames processed")
        
        # Step 2: Track
        tracked = self.track_players(frame_detections)
        
        # Step 3: Classify teams
        tracked = self.classify_teams(tracked)
        
        # Step 4: Convert to pitch coordinates
        frames = []
        for idx, (frame_idx, dets) in enumerate(zip(frame_indices, tracked)):
            team_a = []
            team_b = []
            
            for det in dets:
                center = np.array(det['center'])
                pitch_pos = self.pixel_to_pitch(center)[0]
                
                player = {
                    'id': det['track_id'],
                    'x': float(np.clip(pitch_pos[0], 0, PITCH_LENGTH)),
                    'y': float(np.clip(pitch_pos[1], 0, PITCH_WIDTH)),
                    'team': det['team'],
                    'confidence': det['confidence'],
                }
                
                if det['team'] == 'A':
                    team_a.append(player)
                elif det['team'] == 'B':
                    team_b.append(player)
            
            frames.append({
                'frame_idx': frame_idx,
                'team_a': team_a,
                'team_b': team_b,
            })
        
        self.tracking_data = {
            'frames': frames,
            'metadata': {
                'source': 'video',
                'video_path': self.video_path,
                'sample_rate': sample_rate,
                'fps': fps,
                'n_frames': len(frames),
            }
        }
        
        return self.tracking_data
    
    def run_synthetic_demo(self, n_frames=100):
        """Run with synthetic data (no video dependencies needed)."""
        gen = SyntheticDataGenerator(seed=42)
        self.tracking_data = gen.generate(n_frames=n_frames)
        return self.tracking_data
    
    # ── Individual Player Tracking ─────────────────────────────
    
    def track_individual(self, player_id, team='A'):
        """
        Extract detailed tracking data for a single player.
        
        Args:
            player_id: player ID to track
            team: 'A' or 'B'
        
        Returns:
            dict with trajectory, heatmap data, distance, speed, etc.
        """
        if self.tracking_data is None:
            raise ValueError("No tracking data. Run analyze_video() or run_synthetic_demo() first.")
        
        trajectory = []
        team_key = 'team_a' if team == 'A' else 'team_b'
        fps = self.tracking_data['metadata'].get('fps', 25)
        sample_rate = self.tracking_data['metadata'].get('sample_rate', 1)
        time_per_frame = sample_rate / fps if fps > 0 else 0.04
        
        for frame in self.tracking_data['frames']:
            for player in frame[team_key]:
                if player['id'] == player_id:
                    trajectory.append({
                        'frame': frame['frame_idx'],
                        'x': player['x'],
                        'y': player['y'],
                    })
                    break
        
        if not trajectory:
            return {'error': f'Player {player_id} not found in team {team}'}
        
        # Compute distance and speed
        total_distance = 0.0
        speeds = []
        
        for i in range(1, len(trajectory)):
            dx = trajectory[i]['x'] - trajectory[i-1]['x']
            dy = trajectory[i]['y'] - trajectory[i-1]['y']
            dist = math.sqrt(dx**2 + dy**2)
            total_distance += dist
            
            speed = dist / time_per_frame if time_per_frame > 0 else 0
            speeds.append(speed)
        
        # Heatmap grid
        heatmap = np.zeros((16, 24))  # 16 rows × 24 cols (5m × 5m cells)
        for pt in trajectory:
            row = min(15, int(pt['y'] / PITCH_WIDTH * 16))
            col = min(23, int(pt['x'] / PITCH_LENGTH * 24))
            heatmap[row, col] += 1
        
        return {
            'player_id': player_id,
            'team': team,
            'trajectory': trajectory,
            'total_distance_m': round(total_distance, 1),
            'avg_speed': round(np.mean(speeds), 2) if speeds else 0,
            'max_speed': round(max(speeds), 2) if speeds else 0,
            'n_frames_tracked': len(trajectory),
            'heatmap': heatmap,
            'positions_x': [pt['x'] for pt in trajectory],
            'positions_y': [pt['y'] for pt in trajectory],
        }
    
    # ── Visualization ──────────────────────────────────────────
    
    def draw_frame(self, frame_idx=0, figsize=(12, 8)):
        """
        Draw detected players on the pitch model for a given frame.
        
        Args:
            frame_idx: index into tracking_data frames list
        
        Returns:
            fig, ax
        """
        if self.tracking_data is None:
            raise ValueError("No tracking data available.")
        
        if frame_idx >= len(self.tracking_data['frames']):
            frame_idx = len(self.tracking_data['frames']) - 1
        
        frame = self.tracking_data['frames'][frame_idx]
        
        fig = plt.figure(figsize=figsize, facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        
        if HAS_MPLSOCCER:
            pitch = Pitch(pitch_type='statsbomb', pitch_color='#1a1a2e',
                          line_color='#e0e0e0', linewidth=1, goal_type='box')
            pitch.draw(ax=ax)
        else:
            ax.set_facecolor('#1a1a2e')
            ax.set_xlim(-2, 122)
            ax.set_ylim(-2, 82)
            ax.add_patch(plt.Rectangle((0, 0), 120, 80, fill=False,
                                        edgecolor='#e0e0e0', linewidth=1))
            ax.plot([60, 60], [0, 80], color='#e0e0e0', linewidth=0.5)
        
        # Plot team A
        for p in frame['team_a']:
            ax.scatter(p['x'], p['y'], c=self.team_a_color, s=250,
                       edgecolors='white', linewidths=1.5, zorder=6, alpha=0.9)
            ax.annotate(str(p['id']), xy=(p['x'], p['y']),
                        ha='center', va='center', fontsize=7,
                        fontweight='bold', color='white', zorder=7)
        
        # Plot team B
        for p in frame['team_b']:
            ax.scatter(p['x'], p['y'], c=self.team_b_color, s=250,
                       edgecolors='#333333', linewidths=1.5, zorder=6, alpha=0.9)
            ax.annotate(str(p['id']), xy=(p['x'], p['y']),
                        ha='center', va='center', fontsize=7,
                        fontweight='bold', color='#333333', zorder=7)
        
        # Plot ball
        if 'ball' in frame:
            ax.scatter(frame['ball']['x'], frame['ball']['y'],
                       c='#f1c40f', s=80, edgecolors='white',
                       linewidths=1.5, zorder=8, marker='o')
        
        source = self.tracking_data['metadata']['source']
        real_frame = frame.get('frame_idx', frame_idx)
        fig.suptitle(
            f"SpaceAI FC - Video Analysis (Frame {real_frame}) [{source}]",
            color='white', fontsize=14, fontweight='bold', y=0.98
        )
        
        # Legend
        ax.scatter([], [], c=self.team_a_color, s=80, edgecolors='white',
                   linewidths=1.5, label=self.team_a_name)
        ax.scatter([], [], c=self.team_b_color, s=80, edgecolors='#333333',
                   linewidths=1.5, label=self.team_b_name)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.02),
                  ncol=2, fontsize=9, facecolor='#1a1a2e',
                  edgecolor='#444444', labelcolor='white')
        
        return fig, ax
    
    def draw_player_tracking(self, player_data, figsize=(16, 6)):
        """
        Draw individual player tracking visualization.
        
        Args:
            player_data: output from track_individual()
        
        Returns:
            fig
        """
        fig, axes = plt.subplots(1, 3, figsize=figsize, facecolor='#1a1a2e')
        
        pid = player_data['player_id']
        team = player_data['team']
        color = self.team_a_color if team == 'A' else self.team_b_color
        
        fig.suptitle(
            f"SpaceAI FC - Player {pid} Tracking Analysis",
            color='white', fontsize=14, fontweight='bold', y=0.98
        )
        
        # Panel 1: Trajectory on pitch
        ax1 = axes[0]
        ax1.set_facecolor('#1a1a2e')
        ax1.set_xlim(-2, 122)
        ax1.set_ylim(-2, 82)
        ax1.add_patch(plt.Rectangle((0, 0), 120, 80, fill=False,
                                     edgecolor='#e0e0e0', linewidth=0.8))
        ax1.plot([60, 60], [0, 80], color='#e0e0e0', linewidth=0.3)
        
        xs = player_data['positions_x']
        ys = player_data['positions_y']
        
        # Color trajectory by time
        for i in range(1, len(xs)):
            alpha = 0.3 + 0.7 * (i / len(xs))
            ax1.plot([xs[i-1], xs[i]], [ys[i-1], ys[i]],
                     color=color, alpha=alpha, linewidth=1.5)
        
        ax1.scatter(xs[0], ys[0], c='#2ecc71', s=100, zorder=8,
                    edgecolors='white', linewidths=1.5, label='Start')
        ax1.scatter(xs[-1], ys[-1], c='#e74c3c', s=100, zorder=8,
                    edgecolors='white', linewidths=1.5, label='End')
        
        ax1.set_title("Movement Trajectory", color='white', fontsize=10, pad=8)
        ax1.legend(fontsize=7, facecolor='#1a1a2e', edgecolor='#444444',
                   labelcolor='white', loc='lower right')
        ax1.tick_params(colors='#666666', labelsize=6)
        
        # Panel 2: Heatmap
        ax2 = axes[1]
        ax2.set_facecolor('#1a1a2e')
        cmap = LinearSegmentedColormap.from_list(
            'heat', ['#1a1a2e', '#2c3e50', '#e74c3c', '#f1c40f'], N=256)
        
        heatmap = player_data['heatmap']
        ax2.imshow(heatmap, extent=[0, 120, 0, 80], origin='lower',
                   cmap=cmap, aspect='auto', interpolation='bilinear')
        ax2.set_title("Position Heatmap", color='white', fontsize=10, pad=8)
        ax2.tick_params(colors='#666666', labelsize=6)
        
        # Panel 3: Stats
        ax3 = axes[2]
        ax3.set_facecolor('#1a1a2e')
        ax3.axis('off')
        
        stats_text = [
            f"Player ID: {pid}",
            f"Team: {'A' if team == 'A' else 'B'}",
            f"",
            f"Distance: {player_data['total_distance_m']:.1f} m",
            f"Avg Speed: {player_data['avg_speed']:.1f} m/s",
            f"Max Speed: {player_data['max_speed']:.1f} m/s",
            f"",
            f"Frames Tracked: {player_data['n_frames_tracked']}",
            f"Coverage: {np.sum(heatmap > 0)} / {heatmap.size} zones",
        ]
        
        y = 0.9
        for line in stats_text:
            if line == "":
                y -= 0.05
                continue
            weight = 'bold' if ':' not in line or 'Player' in line else 'normal'
            col = '#f1c40f' if 'Player' in line or 'Team' in line else 'white'
            ax3.text(0.1, y, line, transform=ax3.transAxes,
                     fontsize=10, color=col, fontweight=weight,
                     verticalalignment='top')
            y -= 0.09
        
        ax3.set_title("Tracking Stats", color='white', fontsize=10, pad=8)
        
        plt.tight_layout()
        return fig
    
    def save_animation(self, filename="video_analysis.gif", max_frames=50,
                       interval=200):
        """
        Save tracking data as an animated GIF.
        
        Args:
            filename: output filename
            max_frames: maximum frames in animation
            interval: ms between frames
        """
        if self.tracking_data is None:
            raise ValueError("No tracking data available.")
        
        frames = self.tracking_data['frames'][:max_frames]
        
        fig = plt.figure(figsize=(10, 7), facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        
        def animate(i):
            ax.clear()
            ax.set_facecolor('#1a1a2e')
            ax.set_xlim(-2, 122)
            ax.set_ylim(-2, 82)
            ax.add_patch(plt.Rectangle((0, 0), 120, 80, fill=False,
                                        edgecolor='#e0e0e0', linewidth=0.8))
            ax.plot([60, 60], [0, 80], color='#e0e0e0', linewidth=0.3)
            
            # Penalty areas
            ax.add_patch(plt.Rectangle((0, 18), 18, 44, fill=False,
                                        edgecolor='#e0e0e0', linewidth=0.5))
            ax.add_patch(plt.Rectangle((102, 18), 18, 44, fill=False,
                                        edgecolor='#e0e0e0', linewidth=0.5))
            
            frame = frames[i]
            
            for p in frame['team_a']:
                ax.scatter(p['x'], p['y'], c=self.team_a_color, s=200,
                           edgecolors='white', linewidths=1.2, zorder=6)
            
            for p in frame['team_b']:
                ax.scatter(p['x'], p['y'], c=self.team_b_color, s=200,
                           edgecolors='#333333', linewidths=1.2, zorder=6)
            
            if 'ball' in frame:
                ax.scatter(frame['ball']['x'], frame['ball']['y'],
                           c='#f1c40f', s=60, edgecolors='white',
                           linewidths=1, zorder=8)
            
            ax.set_title(
                f"SpaceAI FC - Video Analysis  |  Frame {frame.get('frame_idx', i)}",
                color='white', fontsize=11, fontweight='bold', pad=10
            )
            ax.tick_params(colors='#666666', labelsize=6)
        
        anim = animation.FuncAnimation(fig, animate, frames=len(frames),
                                        interval=interval, blit=False)
        
        filepath = f"outputs/{filename}"
        anim.save(filepath, writer='pillow', fps=5)
        plt.close(fig)
        print(f"  Saved animation: {filepath}")
    
    # ── Text Output ────────────────────────────────────────────
    
    def print_summary(self):
        """Print a text summary of video analysis results."""
        if self.tracking_data is None:
            print("  No tracking data available.")
            return
        
        meta = self.tracking_data['metadata']
        frames = self.tracking_data['frames']
        
        print(f"\n  ╔══════════════════════════════════════════╗")
        print(f"  ║   VIDEO TACTICAL ANALYSIS SUMMARY        ║")
        print(f"  ╚══════════════════════════════════════════╝")
        print(f"  Source: {meta['source']}")
        print(f"  Total frames analyzed: {meta['n_frames']}")
        print(f"  FPS: {meta.get('fps', 'N/A')}")
        
        if frames:
            # Average players per frame
            avg_a = np.mean([len(f['team_a']) for f in frames])
            avg_b = np.mean([len(f['team_b']) for f in frames])
            
            print(f"\n  --- Player Detection ---")
            print(f"  Avg {self.team_a_name} players/frame: {avg_a:.1f}")
            print(f"  Avg {self.team_b_name} players/frame: {avg_b:.1f}")
            
            # Unique player IDs
            ids_a = set()
            ids_b = set()
            for f in frames:
                for p in f['team_a']:
                    ids_a.add(p['id'])
                for p in f['team_b']:
                    ids_b.add(p['id'])
            
            print(f"  Unique {self.team_a_name} IDs tracked: {len(ids_a)}")
            print(f"  Unique {self.team_b_name} IDs tracked: {len(ids_b)}")
            
            # Average positions
            if frames[-1]['team_a']:
                avg_x_a = np.mean([p['x'] for p in frames[-1]['team_a']])
                print(f"  {self.team_a_name} avg x (last frame): {avg_x_a:.1f}")
            if frames[-1]['team_b']:
                avg_x_b = np.mean([p['x'] for p in frames[-1]['team_b']])
                print(f"  {self.team_b_name} avg x (last frame): {avg_x_b:.1f}")
            
            # Tracking quality
            tracked_pct = sum(1 for f in frames if len(f['team_a']) >= 8) / len(frames) * 100
            print(f"\n  --- Tracking Quality ---")
            print(f"  Frames with 8+ {self.team_a_name} players: {tracked_pct:.0f}%")
        
        print()
    
    def get_summary_data(self):
        """
        Get a summary dict suitable for integration with MatchReport.
        
        Returns:
            dict with key metrics, or None if no data
        """
        if self.tracking_data is None:
            return None
        
        meta = self.tracking_data['metadata']
        frames = self.tracking_data['frames']
        
        if not frames:
            return None
        
        avg_a = np.mean([len(f['team_a']) for f in frames])
        avg_b = np.mean([len(f['team_b']) for f in frames])
        
        ids_a = set()
        ids_b = set()
        for f in frames:
            for p in f['team_a']:
                ids_a.add(p['id'])
            for p in f['team_b']:
                ids_b.add(p['id'])
        
        return {
            'source': meta['source'],
            'n_frames': meta['n_frames'],
            'fps': meta.get('fps', 0),
            'avg_team_a_detected': round(avg_a, 1),
            'avg_team_b_detected': round(avg_b, 1),
            'unique_ids_team_a': len(ids_a),
            'unique_ids_team_b': len(ids_b),
            'team_a_name': self.team_a_name,
            'team_b_name': self.team_b_name,
        }
    
    # ── Cleanup ────────────────────────────────────────────────
    
    def cleanup(self):
        """Remove temporary files (downloaded videos, etc.)."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
            print("  Cleaned up temporary files.")
    
    def __del__(self):
        """Ensure cleanup on garbage collection."""
        try:
            self.cleanup()
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════
# Standalone Demo
# ════════════════════════════════════════════════════════════════

def demo():
    """
    Run a full demo using synthetic data.
    No video files or heavy dependencies required.
    """
    print("\n" + "=" * 60)
    print("  SpaceAI FC - Video Tactical Analysis Demo")
    print("  Phase 4 Module 1 (Synthetic Data Mode)")
    print("=" * 60)
    
    import os
    os.makedirs("outputs", exist_ok=True)
    
    va = VideoAnalyzer()
    va.team_a_name = "FC Barcelona"
    va.team_b_name = "Real Madrid"
    va.team_a_color = "#a50044"
    va.team_b_color = "#ffffff"
    
    # ── Step 1: Generate synthetic tracking data ────────────────
    print("\n[1/5] Generating synthetic tracking data...")
    data = va.run_synthetic_demo(n_frames=100)
    print(f"  Generated {len(data['frames'])} frames")
    print(f"  Team A players/frame: {len(data['frames'][0]['team_a'])}")
    print(f"  Team B players/frame: {len(data['frames'][0]['team_b'])}")
    
    # ── Step 2: Print summary ──────────────────────────────────
    print("\n[2/5] Analysis Summary:")
    va.print_summary()
    
    # ── Step 3: Visualize a single frame ───────────────────────
    print("[3/5] Visualizing frame snapshots...")
    
    for frame_idx in [0, 25, 50, 75, 99]:
        fig, ax = va.draw_frame(frame_idx)
        filename = f"16_video_frame_{frame_idx:03d}.png"
        fig.savefig(f"outputs/{filename}", dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
    print("  Saved: 5 frame snapshots to outputs/")
    
    # ── Step 4: Individual player tracking ─────────────────────
    print("\n[4/5] Tracking individual player (Player 10 — striker)...")
    player_data = va.track_individual(player_id=10, team='A')
    
    if 'error' not in player_data:
        print(f"  Distance covered: {player_data['total_distance_m']:.1f} m")
        print(f"  Average speed: {player_data['avg_speed']:.2f} m/s")
        print(f"  Max speed: {player_data['max_speed']:.2f} m/s")
        print(f"  Frames tracked: {player_data['n_frames_tracked']}")
        
        fig_track = va.draw_player_tracking(player_data)
        fig_track.savefig("outputs/16_player_tracking.png", dpi=150,
                          bbox_inches='tight',
                          facecolor=fig_track.get_facecolor())
        plt.close(fig_track)
        print("  Saved: outputs/16_player_tracking.png")
    
    # ── Step 5: Save animation ─────────────────────────────────
    print("\n[5/5] Generating animation...")
    try:
        va.save_animation("16_video_analysis.gif", max_frames=50, interval=200)
    except Exception as e:
        print(f"  ⚠ Could not save animation: {e}")
        print("  (This is OK — animation requires pillow writer)")
    
    # ── Summary ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Video Tactical Analysis Demo Complete!")
    print("  Outputs saved to outputs/16_*.png")
    print("=" * 60)
    
    # Get integration data
    summary = va.get_summary_data()
    print(f"\n  Integration data available: {summary is not None}")
    
    plt.close('all')
    return va


if __name__ == "__main__":
    demo()
