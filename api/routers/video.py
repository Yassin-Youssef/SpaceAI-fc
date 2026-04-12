"""
SpaceAI FC - Video Router
  POST /api/video/upload
  POST /api/video/youtube
  POST /api/video/track-player
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from api.models.requests import YouTubeRequest, TrackPlayerRequest
from api.models.responses import VideoResponse, VideoTrackingData, PlayerTrackResponse
from api.services.video_service import (
    process_video_file,
    process_youtube_url,
    track_player,
)
from api.utils.file_handler import save_video_upload, cleanup

router = APIRouter(prefix="/api/video", tags=["Video Analysis"])


@router.post("/upload", response_model=VideoResponse)
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file (mp4, avi, mov, mkv, max 500MB).
    Returns extracted player tracking data.
    Phase 4 dependencies optional — falls back to synthetic demo data.
    """
    saved_path = None
    try:
        saved_path = await save_video_upload(file)
        tracking = process_video_file(str(saved_path))

        return VideoResponse(
            success=True,
            tracking_data=VideoTrackingData(
                team_a=tracking["team_a"],
                team_b=tracking["team_b"],
                frames_processed=tracking["frames_processed"],
                method=tracking["method"],
            ),
            message=f"Processed {tracking['frames_processed']} frames via {tracking['method']}.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        cleanup(saved_path)


@router.post("/youtube", response_model=VideoResponse)
async def youtube_video(req: YouTubeRequest):
    """
    Download and process a YouTube clip.
    Set demo_mode=true to use synthetic data without downloading.
    """
    try:
        tracking = process_youtube_url(req.url, demo_mode=req.demo_mode)

        return VideoResponse(
            success=True,
            tracking_data=VideoTrackingData(
                team_a=tracking["team_a"],
                team_b=tracking["team_b"],
                frames_processed=tracking["frames_processed"],
                method=tracking["method"],
            ),
            message=f"Processed via {tracking['method']}.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/track-player", response_model=PlayerTrackResponse)
async def track_player_endpoint(req: TrackPlayerRequest):
    """
    Extract individual player trajectory from video tracking data.
    """
    try:
        result = track_player(req.video_data, req.player_id)
        return PlayerTrackResponse(
            success=True,
            player_id=result["player_id"],
            trajectory=result["trajectory"],
            heatmap_base64=result["heatmap_base64"],
            total_distance=result["total_distance"],
            avg_speed=result["avg_speed"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
