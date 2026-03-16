"""Motor de segurança de plataforma para pacing, cooldown e risco."""

from app.safety.cooldown import clear_expired_cooldown, is_cooldown_active, start_cooldown
from app.safety.events import emit_safety_event
from app.safety.models import (
    AccountMode,
    AccountSafetyState,
    RiskLevel,
    RiskSignal,
    SafetyDecision,
    SafetyDecisionType,
)
from app.safety.pacing import evaluate_pacing
from app.safety.risk_detector import detect_risk
from app.safety.safety_gate import evaluate_publish_safety
from app.safety.service import SafetyService

__all__ = [
    "AccountMode",
    "AccountSafetyState",
    "RiskLevel",
    "RiskSignal",
    "SafetyDecision",
    "SafetyDecisionType",
    "clear_expired_cooldown",
    "detect_risk",
    "emit_safety_event",
    "evaluate_pacing",
    "evaluate_publish_safety",
    "is_cooldown_active",
    "SafetyService",
    "start_cooldown",
]
