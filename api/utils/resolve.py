"""
SpaceAI FC - Input Resolver Utilities
======================================
Bridges Phase 4 (Computer Vision) to Phase 1-3.
"""

from pathlib import Path
from fastapi import HTTPException
from api.utils.file_handler import parse_dataset
from engine.perception.video_analyzer import VideoAnalyzer

def resolve_input(req):
    """
    Parses tracking data based on the request's input_type.
    Determines whether the data is from manual entry, a dataset,
    or a YouTube/Video file that needs computer vision tracking.
    
    Returns:
        tuple: (team_a: list, team_b: list, passes: list)
    """
    # 1. Dataset parsing
    if getattr(req, "input_type", "manual") == "dataset" and getattr(req, "dataset_file", None):
        data = parse_dataset(Path(req.dataset_file))
        return data.get("team_a", []), data.get("team_b", []), data.get("passes", [])
        
    # 2. Phase 4 Video CV parsing
    elif getattr(req, "input_type", "manual") == "video" and (getattr(req, "video_file", None) or getattr(req, "youtube_url", None)):
        analyzer = VideoAnalyzer()
        try:
            if getattr(req, "youtube_url", None):
                analyzer.download_youtube(req.youtube_url)
            else:
                analyzer.load_video(req.video_file)
                
            tracking_data = analyzer.analyze_video(sample_rate=5, max_frames=50) # run CV
            
            if "frames" in tracking_data and tracking_data["frames"]:
                # Snag a robust tracking frame to feed the engine's static spatial analysis
                frame = tracking_data["frames"][-1]
                
                # Convert raw cv dicts safely into strict Pydantic model equivalents
                def fmt_p(p, team="A"):
                    return {
                        "name": f"Player {p.get('id', 0)}",
                        "number": p.get('id', 0),
                        "x": p.get('x', 0.0),
                        "y": p.get('y', 0.0),
                        "position": p.get('role', "CM")
                    }
                
                team_a_cv = [fmt_p(p, "A") for p in frame.get("team_a", [])]
                team_b_cv = [fmt_p(p, "B") for p in frame.get("team_b", [])]
                
                return team_a_cv, team_b_cv, []
            else:
                raise HTTPException(status_code=400, detail="No players detected in video.")
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Phase 4 computer vision failed: {str(e)}")
            
    # 3. Manual coordinate object
    team_a = [p.model_dump() for p in req.team_a] if getattr(req, "team_a", None) else []
    team_b = [p.model_dump() for p in req.team_b] if getattr(req, "team_b", None) else []
    passes = [p.model_dump() for p in req.passes] if getattr(req, "passes", None) else []
    
    return team_a, team_b, passes
