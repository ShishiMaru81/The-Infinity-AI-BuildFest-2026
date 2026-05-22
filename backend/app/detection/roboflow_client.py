"""Optional Roboflow hosted inference for weapon/fire models."""

import base64
from typing import Any

import httpx

from app.config import settings
from app.detection.class_map import normalize_label


async def infer_roboflow(frame_b64: str, model_slug: str) -> list[dict]:
    """
    model_slug format: workspace/project/version e.g. weapons-detection/1
    """
    if not settings.roboflow_api_key or not model_slug:
        return []

    parts = model_slug.strip("/").split("/")
    if len(parts) < 2:
        return []
    project = "/".join(parts[:-1])
    version = parts[-1]
    url = f"https://detect.roboflow.com/{project}/{version}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                params={"api_key": settings.roboflow_api_key},
                content=base64.b64decode(frame_b64),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    out: list[dict] = []
    for pred in data.get("predictions", []):
        label = pred.get("class") or pred.get("label") or ""
        conf = float(pred.get("confidence", 0))
        hazard = normalize_label(str(label))
        if not hazard:
            continue
        w = float(pred.get("width", 0))
        h = float(pred.get("height", 0))
        cx = float(pred.get("x", 0))
        cy = float(pred.get("y", 0))
        x1 = int(cx - w / 2)
        y1 = int(cy - h / 2)
        x2 = int(cx + w / 2)
        y2 = int(cy + h / 2)
        out.append(
            {
                "label": hazard,
                "raw_label": label,
                "confidence": conf,
                "bbox": [x1, y1, x2, y2],
                "source": "roboflow",
            }
        )
    return out
