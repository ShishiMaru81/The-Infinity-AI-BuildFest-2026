"""Require N consecutive frames before confirming a hazard detection."""


class HazardFrameTracker:
    def __init__(self, required_frames: int = 5):
        self.required_frames = max(1, required_frames)
        self._counts: dict[str, int] = {}
        self._last_conf: dict[str, float] = {}

    def reset(self, hazard: str | None = None) -> None:
        if hazard is None:
            self._counts.clear()
            self._last_conf.clear()
            return
        self._counts.pop(hazard, None)
        self._last_conf.pop(hazard, None)

    def update(self, hazard: str, confidence: float) -> bool:
        """Increment streak for hazard; return True if confirmed."""
        self._counts[hazard] = self._counts.get(hazard, 0) + 1
        self._last_conf[hazard] = confidence
        for other in list(self._counts.keys()):
            if other != hazard:
                self._counts[other] = 0
        return self._counts[hazard] >= self.required_frames

    def best_confirmed(self) -> tuple[str, float] | None:
        for hazard, count in self._counts.items():
            if count >= self.required_frames:
                return hazard, self._last_conf.get(hazard, 0.0)
        return None

    def tick_miss(self) -> None:
        """Call when no hazard met threshold this frame — decay all streaks."""
        for key in list(self._counts.keys()):
            self._counts[key] = max(0, self._counts[key] - 1)
