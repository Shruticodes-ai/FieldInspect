import math
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="SIH26095 Field Inspection API", version="1.0.0")

# Setup HTML Template folder
templates = Jinja2Templates(directory="templates")

class InspectionPayload(BaseModel):
    inspector_id: str
    facility_id: str
    user_lat: float
    user_lng: float
    target_lat: float
    target_lng: float
    is_mock_location: bool
    photo_hash: str
    checklist_data: dict

def calculate_distance(lat1, lon1, lat2, lon2):
    # Haversine formula to compute ground distance in meters
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Mock database of existing photo hashes to prevent duplicate submissions
KNOWN_PHOTO_HASHES = {"hash_fake_sample_123", "recycled_photo_456"}

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

@app.post("/api/v1/inspections/submit")
async def submit_inspection(payload: InspectionPayload):
    # 1. Mock location detection check
    if payload.is_mock_location:
        raise HTTPException(status_code=400, detail="FRAUD_ALERT: Mock location / GPS spoofing app detected on mobile device.")

    # 2. Geo-fencing verification (Must be within 100 meters of facility)
    distance = calculate_distance(payload.user_lat, payload.user_lng, payload.target_lat, payload.target_lng)
    if distance > 100.0:
        raise HTTPException(
            status_code=403, 
            detail=f"GEO_FENCE_VIOLATION: Inspector is {round(distance, 1)}m away from facility. Maximum allowed radius is 100m."
        )

    # 3. Image anti-duplication / Anti-spoofing check
    if payload.photo_hash in KNOWN_PHOTO_HASHES:
        raise HTTPException(status_code=409, detail="DUPLICATE_IMAGE_REJECTED: Image hash matches a previously submitted audit photo.")

    # Record valid submission
    KNOWN_PHOTO_HASHES.add(payload.photo_hash)
    
    return {
        "status": "SUCCESS",
        "message": "Inspection audit logged & verified.",
        "distance_verified_meters": round(distance, 2),
        "timestamp": datetime.utcnow().isoformat()
    }