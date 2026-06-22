"""
Atelier Flow Infinite Canvas API routes.

Endpoints:
  GET  /api/v1/projects/{project_id}/canvas-state   — load canvas state
  PUT  /api/v1/projects/{project_id}/canvas-state   — save canvas state
  GET  /api/v1/projects/{project_id}/timeline        — generation timeline
  GET  /api/v1/projects/{project_id}/canvas-assets   — asset library w/ filters
"""
import json
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.canvas_state import CanvasState
from app.models.visual_asset import VisualAsset

router = APIRouter(prefix="/api/v1", tags=["atelier-canvas"])


# ── Pydantic Schemas ──────────────────────────────────────────

class CanvasElement(BaseModel):
    id: str
    type: str  # key_visual, video, texture, text, graphic
    label: str = ""
    x: float = 0
    y: float = 0
    width: float = 400
    height: float = 400
    rotation: Optional[float] = None
    zIndex: Optional[int] = None
    hidden: Optional[bool] = None
    locked: Optional[bool] = None
    editableLayers: Optional[List[dict]] = None
    thumbnail_url: Optional[str] = None
    asset_ref: Optional[dict] = None
    metadata: Optional[dict] = None


class CanvasConnection(BaseModel):
    id: str
    source_id: str
    target_id: str
    label: str = ""
    relation_type: Optional[str] = None


class ViewportState(BaseModel):
    x: float = 0
    y: float = 0
    scale: float = 1


class CanvasStatePayload(BaseModel):
    elements: List[CanvasElement] = []
    connections: List[CanvasConnection] = []
    viewport: ViewportState = ViewportState()


class CanvasStateResponse(BaseModel):
    project_id: int
    elements: list
    connections: list
    viewport: dict
    updated_at: Optional[str] = None


class TimelineEntry(BaseModel):
    id: int
    prompt: str
    timestamp: str
    asset_type: str
    thumbnail_url: Optional[str] = None
    model_used: Optional[str] = None
    generation_seconds: Optional[int] = None


class TimelineResponse(BaseModel):
    project_id: int
    entries: List[TimelineEntry]


class AssetLibraryItem(BaseModel):
    id: str
    type: str  # image, video, graphic, doc
    label: str
    url: Optional[str] = None
    preview_url: Optional[str] = None
    text_preview: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Optional[dict] = None


class AssetLibraryResponse(BaseModel):
    project_id: int
    items: List[AssetLibraryItem]
    total: int


# ── DB helper ─────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Canvas State ──────────────────────────────────────────────

@router.get("/projects/{project_id}/canvas-state", response_model=CanvasStateResponse)
def get_canvas_state(project_id: int, db: Session = Depends(get_db)):
    """Load the full canvas state for a project."""
    state = (
        db.query(CanvasState)
        .filter(CanvasState.project_id == project_id)
        .first()
    )

    if not state:
        return CanvasStateResponse(
            project_id=project_id,
            elements=[],
            connections=[],
            viewport={"x": 0, "y": 0, "scale": 1},
        )

    return CanvasStateResponse(
        project_id=project_id,
        elements=json.loads(state.elements_json),
        connections=json.loads(state.connections_json),
        viewport=json.loads(state.viewport_json),
        updated_at=state.updated_at.isoformat() if state.updated_at else None,
    )


@router.put("/projects/{project_id}/canvas-state", response_model=CanvasStateResponse)
def put_canvas_state(
    project_id: int,
    payload: CanvasStatePayload,
    db: Session = Depends(get_db),
):
    """Save (create or update) the canvas state for a project."""
    state = (
        db.query(CanvasState)
        .filter(CanvasState.project_id == project_id)
        .first()
    )

    elements_json = json.dumps(
        [e.model_dump(exclude_none=True) for e in payload.elements], ensure_ascii=False
    )
    connections_json = json.dumps(
        [c.model_dump(exclude_none=True) for c in payload.connections], ensure_ascii=False
    )
    viewport_json = json.dumps(payload.viewport.model_dump(exclude_none=True))

    if state:
        state.elements_json = elements_json
        state.connections_json = connections_json
        state.viewport_json = viewport_json
        state.updated_at = datetime.utcnow()
    else:
        state = CanvasState(
            project_id=project_id,
            elements_json=elements_json,
            connections_json=connections_json,
            viewport_json=viewport_json,
        )
        db.add(state)

    db.commit()
    db.refresh(state)

    return CanvasStateResponse(
        project_id=project_id,
        elements=json.loads(state.elements_json),
        connections=json.loads(state.connections_json),
        viewport=json.loads(state.viewport_json),
        updated_at=state.updated_at.isoformat() if state.updated_at else None,
    )


# ── Timeline ──────────────────────────────────────────────────

@router.get("/projects/{project_id}/timeline", response_model=TimelineResponse)
def get_timeline(project_id: int, db: Session = Depends(get_db)):
    """Return generation history for a project (newest first).

    Extracts prompts and thumbnails from VisualAsset records.
    """
    generations = (
        db.query(VisualAsset)
        .filter(VisualAsset.project_id == project_id)
        .order_by(VisualAsset.created_at.desc())
        .all()
    )

    entries: List[TimelineEntry] = []
    for gen in generations:
        try:
            plan = gen.asset_plan if gen.asset_plan else {}
        except Exception:
            plan = {}

        created = gen.created_at.isoformat() if gen.created_at else None

        # Extract main_image as primary timeline entry
        main = plan.get("main_image")
        if isinstance(main, dict) and main.get("prompt"):
            entries.append(TimelineEntry(
                id=gen.id,
                prompt=main["prompt"],
                timestamp=created,
                asset_type="key_visual",
                thumbnail_url=main.get("url"),
                model_used=gen.model_used,
                generation_seconds=gen.generation_seconds,
            ))

        # Extract scene_images as separate entries
        scenes = plan.get("scene_images", [])
        if isinstance(scenes, list):
            for scene in scenes:
                if isinstance(scene, dict) and scene.get("prompt"):
                    entries.append(TimelineEntry(
                        id=gen.id,
                        prompt=scene["prompt"],
                        timestamp=created,
                        asset_type="scene_image",
                        thumbnail_url=scene.get("url"),
                        model_used=gen.model_used,
                        generation_seconds=gen.generation_seconds,
                    ))

    return TimelineResponse(project_id=project_id, entries=entries)


# ── Asset Library ─────────────────────────────────────────────

@router.get("/projects/{project_id}/canvas-assets", response_model=AssetLibraryResponse)
def get_canvas_assets(
    project_id: int,
    type: Optional[str] = Query(None, description="Filter: images, videos, graphics, docs"),
    mood: Optional[str] = Query(None, description="Filter by mood tag"),
    color: Optional[str] = Query(None, description="Filter by dominant color"),
    search: Optional[str] = Query(None, description="Keyword search in prompts/labels"),
    approved: Optional[bool] = Query(None, description="Show only approved assets"),
    db: Session = Depends(get_db),
):
    """Search and filter assets for the canvas asset library panel.

    Scans all VisualAsset generations for a project and extracts
    individual assets (images, scenes, videos, graphics) with metadata.
    """
    generations = (
        db.query(VisualAsset)
        .filter(VisualAsset.project_id == project_id)
        .order_by(VisualAsset.created_at.desc())
        .all()
    )

    items: List[AssetLibraryItem] = []
    item_idx = 0

    for gen in generations:
        try:
            plan = gen.asset_plan if gen.asset_plan else {}
        except Exception:
            plan = {}

        created = gen.created_at.isoformat() if gen.created_at else None

        def _matches_filters(label: str, prompt: str, meta: dict) -> bool:
            """Check if an item matches all provided filters."""
            # Type filter
            if type and type not in ("all", "All"):
                # Normalize type matching
                type_map = {
                    "images": ["image", "images", "main_image", "scene_image", "white_bg"],
                    "videos": ["video", "videos", "video_script"],
                    "graphics": ["graphic", "graphics", "selling_point", "ad_material"],
                    "docs": ["doc", "docs", "brief", "layout_plan"],
                }
                allowed = type_map.get(type, [type])
                if label not in allowed:
                    return False

            # Mood filter — check metadata
            if mood and meta.get("mood", "").lower() != mood.lower():
                return False

            # Color filter — check metadata
            if color and meta.get("color", "").lower() != color.lower():
                return False

            # Search filter — grep prompt + label
            if search:
                search_lower = search.lower()
                if search_lower not in label.lower() and search_lower not in prompt.lower():
                    return False

            # Approved filter
            if approved is not None:
                is_approved = meta.get("approved", False)
                if is_approved != approved:
                    return False

            return True

        # Extract main_image
        main = plan.get("main_image")
        if isinstance(main, dict) and main.get("url"):
            if _matches_filters("main_image", main.get("prompt", ""), main):
                item_idx += 1
                items.append(AssetLibraryItem(
                    id=f"asset_{gen.id}_{item_idx}",
                    type="image",
                    label=main.get("goal", "Main Image"),
                    url=main.get("url"),
                    created_at=created,
                    metadata={"generation_id": gen.id, "prompt": main.get("prompt", "")},
                ))

        # Extract white_bg
        white_bg = plan.get("white_bg")
        if isinstance(white_bg, dict) and white_bg.get("url"):
            if _matches_filters("white_bg", white_bg.get("prompt", ""), white_bg):
                item_idx += 1
                items.append(AssetLibraryItem(
                    id=f"asset_{gen.id}_{item_idx}",
                    type="image",
                    label="White Background",
                    url=white_bg.get("url"),
                    created_at=created,
                    metadata={"generation_id": gen.id},
                ))

        # Extract scene_images
        scenes = plan.get("scene_images", [])
        if isinstance(scenes, list):
            for scene in scenes:
                if isinstance(scene, dict) and scene.get("url"):
                    if _matches_filters("scene_image", scene.get("prompt", ""), scene):
                        item_idx += 1
                        items.append(AssetLibraryItem(
                            id=f"asset_{gen.id}_{item_idx}",
                            type="image",
                            label=scene.get("scene_name", "Scene"),
                            url=scene.get("url"),
                            created_at=created,
                            metadata={
                                "generation_id": gen.id,
                                "prompt": scene.get("prompt", ""),
                                "mood": scene.get("mood", ""),
                            },
                        ))

        # Extract selling_points as graphics
        selling = plan.get("selling_points", [])
        if isinstance(selling, list):
            for sp in selling:
                if isinstance(sp, dict):
                    if _matches_filters("selling_point", sp.get("title", ""), sp):
                        item_idx += 1
                        items.append(AssetLibraryItem(
                            id=f"asset_{gen.id}_{item_idx}",
                            type="graphic",
                            label=sp.get("title", "Selling Point"),
                            text_preview=sp.get("description", "")[:200],
                            created_at=created,
                            metadata={"generation_id": gen.id},
                        ))

        # Extract video_scripts
        videos = plan.get("video_scripts", [])
        if isinstance(videos, list):
            for vid in videos:
                if isinstance(vid, dict):
                    if _matches_filters("video_script", vid.get("video_goal", ""), vid):
                        item_idx += 1
                        items.append(AssetLibraryItem(
                            id=f"asset_{gen.id}_{item_idx}",
                            type="video",
                            label=vid.get("video_goal", "Video Script"),
                            preview_url=vid.get("preview_url"),
                            text_preview=vid.get("script", "")[:200],
                            created_at=created,
                            metadata={
                                "generation_id": gen.id,
                                "duration": vid.get("duration_seconds"),
                            },
                        ))

        # Extract ad_material
        ad = plan.get("ad_material")
        if isinstance(ad, dict) and ad:
            if _matches_filters("ad_material", ad.get("ad_goal", ""), ad):
                item_idx += 1
                items.append(AssetLibraryItem(
                    id=f"asset_{gen.id}_{item_idx}",
                    type="graphic",
                    label=ad.get("ad_goal", "Ad Material"),
                    text_preview=ad.get("hook", "")[:200],
                    created_at=created,
                    metadata={"generation_id": gen.id},
                ))

        # Extract layout_plan
        layout = plan.get("layout_plan")
        if isinstance(layout, dict) and layout:
            item_idx += 1
            items.append(AssetLibraryItem(
                id=f"asset_{gen.id}_{item_idx}",
                type="doc",
                label="Layout Plan",
                text_preview=json.dumps(layout, ensure_ascii=False)[:200],
                created_at=created,
                metadata={"generation_id": gen.id},
            ))

    return AssetLibraryResponse(
        project_id=project_id,
        items=items,
        total=len(items),
    )
