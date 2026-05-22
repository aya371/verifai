"""
Patches routes.py to add media verification endpoints.
Run from: C:\\Users\\User\\Documents\\verifai
"""
import re

content = open("backend/api/routes.py", encoding="utf-8").read()

# Check if already patched
if "analyze-audio" in content:
    print("Already patched.")
    exit()

# New imports to add
new_imports = """from fastapi import UploadFile, File, Form
from backend.agents.audio_deepfake_detector import AudioDeepfakeDetector
from backend.agents.video_deepfake_detector import VideoDeepfakeDetector
from backend.agents.media_cross_verifier import MediaCrossVerifier
"""

# New routes to append before the last line
new_routes = '''

# ── Media Verification Routes ─────────────────────────────────────────────

@router.post("/media/analyze-audio")
async def analyze_audio(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        detector    = AudioDeepfakeDetector()
        result      = detector.detect(audio_bytes, filename=audio.filename or "audio.wav")
        return result
    except Exception as e:
        logger.error(f"Audio analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media/analyze-video")
async def analyze_video(video: UploadFile = File(...)):
    try:
        video_bytes = await video.read()
        detector    = VideoDeepfakeDetector()
        result      = detector.detect(video_bytes, filename=video.filename or "video.mp4")
        return result
    except Exception as e:
        logger.error(f"Video analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media/cross-verify")
async def cross_verify(
    name:  str        = Form(None),
    image: UploadFile = File(None),
    audio: UploadFile = File(None),
    video: UploadFile = File(None),
):
    try:
        identity_result = None
        image_result    = None
        audio_result    = None
        video_result    = None

        if name and name.strip():
            from backend.agents.identity_verifier import IdentityVerifier
            identity_result = IdentityVerifier().verify_by_name(name.strip())

        if image and image.filename:
            from backend.agents.image_verifier import ImageVerifier
            img_bytes    = await image.read()
            image_result = ImageVerifier().verify(img_bytes, image.filename)

        if audio and audio.filename:
            aud_bytes    = await audio.read()
            audio_result = AudioDeepfakeDetector().detect(aud_bytes, audio.filename)

        if video and video.filename:
            vid_bytes    = await video.read()
            video_result = VideoDeepfakeDetector().detect(vid_bytes, video.filename)

        result = MediaCrossVerifier().verify(
            identity_result=identity_result,
            image_result=image_result,
            audio_result=audio_result,
            video_result=video_result,
        )
        return result

    except Exception as e:
        logger.error(f"Cross-verify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
'''

# Inject imports after existing imports block
if "from fastapi import" in content:
    content = content.replace(
        "from fastapi import",
        new_imports + "from fastapi import",
        1
    )
else:
    content = new_imports + content

# Append new routes at end
content = content.rstrip() + "\n" + new_routes + "\n"

open("backend/api/routes.py", "w", encoding="utf-8").write(content)
print("OK routes.py patched with media endpoints")
