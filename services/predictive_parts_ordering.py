"""
Predictive Parts Ordering Service
AI predicts part failures and automatically orders replacements.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class PartStatus(Enum):
    """Part status."""
    HEALTHY = "healthy"
    MONITORING = "monitoring"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class Part:
    """Vehicle part."""
    part_id: str
    name: str
    category: str  # engine, transmission, suspension, etc.
    current_status: PartStatus
    health_score: float  # 0.0 - 100.0
    predicted_failure_date: Optional[float] = None
    confidence: float = 0.0  # 0.0 - 1.0
    last_inspection: float = field(default_factory=time.time)
    mileage_at_install: float = 0.0
    current_mileage: float = 0.0


@dataclass
class PartOrder:
    """Parts order."""
    order_id: str
    part_id: str
    part_name: str
    supplier: str
    price: float
    estimated_delivery: float  # Timestamp
    status: OrderStatus
    created_at: float
    approved_at: Optional[float] = None
    ordered_at: Optional[float] = None
    tracking_number: Optional[str] = None
    user_notes: str = ""


@dataclass
class FailurePrediction:
    """Part failure prediction."""
    part_id: str
    part_name: str
    predicted_failure_date: float
    confidence: float
    severity: str  # low, medium, high, critical
    reasoning: str
    recommended_action: str
    estimated_cost: Optional[float] = None


class PredictivePartsOrdering:
    """
    Predictive parts ordering service.
    
    Features:
    - Monitor part health
    - Predict failures using ML
    - Automatic ordering
    - Supplier integration
    - Price tracking
    """
    
    def __init__(
        self,
        supplier_api_url: Optional[str] = None,
        auto_order_enabled: bool = False,
        approval_required: bool = True,
    ):
        """
        Initialize predictive parts ordering.
        
        Args:
            supplier_api_url: Supplier API URL
            auto_order_enabled: Enable automatic ordering
            approval_required: Require user approval before ordering
        """
        self.supplier_api_url = supplier_api_url
        self.auto_order_enabled = auto_order_enabled
        self.approval_required = approval_required
        
        self.parts: Dict[str, Part] = {}
        self.orders: List[PartOrder] = []
        self.predictions: List[FailurePrediction] = []
        
        # Data storage
        self.data_dir = Path("data/parts_ordering")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_data()
    
    def monitor_part(
        self,
        part_id: str,
        telemetry_data: Dict[str, Any],
        current_mileage: float,
    ) -> Optional[FailurePrediction]:
        """
        Monitor part health and predict failure.
        
        Args:
            part_id: Part ID
            telemetry_data: Current telemetry data
            current_mileage: Current vehicle mileage
        
        Returns:
            FailurePrediction if failure predicted
        """
        if part_id not in self.parts:
            # Create new part entry
            self.parts[part_id] = Part(
                part_id=part_id,
                name=telemetry_data.get("part_name", part_id),
                category=telemetry_data.get("category", "unknown"),
                current_status=PartStatus.HEALTHY,
                health_score=100.0,
                current_mileage=current_mileage,
            )
        
        part = self.parts[part_id]
        part.current_mileage = current_mileage
        
        # Analyze telemetry for part health
        health_score = self._calculate_health_score(part, telemetry_data)
        part.health_score = health_score
        
        # Update status
        if health_score >= 80:
            part.current_status = PartStatus.HEALTHY
        elif health_score >= 60:
            part.current_status = PartStatus.MONITORING
        elif health_score >= 40:
            part.current_status = PartStatus.WARNING
        elif health_score >= 20:
            part.current_status = PartStatus.CRITICAL
        else:
            part.current_status = PartStatus.FAILED
        
        # Predict failure if status is warning or critical
        if part.current_status in [PartStatus.WARNING, PartStatus.CRITICAL]:
            prediction = self._predict_failure(part, telemetry_data)
            if prediction:
                part.predicted_failure_date = prediction.predicted_failure_date
                part.confidence = prediction.confidence
                
                # Add to predictions
                self.predictions.append(prediction)
                
                # Auto-order if enabled and critical
                if self.auto_order_enabled and prediction.severity == "critical":
                    if not self.approval_required:
                        self._create_order(part_id, prediction)
                
                return prediction
        
        return None
    
    def _calculate_health_score(
        self,
        part: Part,
        telemetry_data: Dict[str, Any],
    ) -> float:
        """Calculate part health score."""
        base_score = part.health_score
        
        # Degrade based on mileage
        mileage_since_install = part.current_mileage - part.mileage_at_install
        if mileage_since_install > 0:
            # Typical part lifespan (varies by part)
            typical_lifespan = self._get_typical_lifespan(part.category)
            if typical_lifespan > 0:
                age_factor = min(1.0, mileage_since_install / typical_lifespan)
                base_score = 100.0 * (1.0 - age_factor * 0.5)  # Degrade up to 50%
        
        # Adjust based on telemetry
        if "temperature" in telemetry_data:
            temp = telemetry_data["temperature"]
            if temp > 250:  # Overheating
                base_score -= 10
            elif temp > 200:
                base_score -= 5
        
        if "vibration" in telemetry_data:
            vibration = telemetry_data["vibration"]
            if vibration > 0.5:  # High vibration
                base_score -= 15
        
        if "pressure" in telemetry_data:
            pressure = telemetry_data["pressure"]
            expected_pressure = telemetry_data.get("expected_pressure", 0)
            if expected_pressure > 0:
                deviation = abs(pressure - expected_pressure) / expected_pressure
                if deviation > 0.2:  # 20% deviation
                    base_score -= 10
        
        return max(0.0, min(100.0, base_score))
    
    def _get_typical_lifespan(self, category: str) -> float:
        """Get typical part lifespan in miles."""
        lifespans = {
            "engine": 150000,
            "transmission": 120000,
            "turbo": 100000,
            "suspension": 80000,
            "brakes": 50000,
            "tires": 40000,
            "battery": 50000,
            "alternator": 100000,
            "starter": 100000,
            "fuel_pump": 100000,
            "water_pump": 80000,
            "timing_belt": 60000,
            "spark_plugs": 30000,
            "air_filter": 15000,
            "oil_filter": 5000,
        }
        return lifespans.get(category, 50000)
    
    def _predict_failure(
        self,
        part: Part,
        telemetry_data: Dict[str, Any],
    ) -> Optional[FailurePrediction]:
        """Predict part failure."""
        if part.health_score <= 20:
            # Critical - failure imminent
            days_until_failure = 1.0
            confidence = 0.9
            severity = "critical"
        elif part.health_score <= 40:
            # Warning - failure soon
            days_until_failure = 7.0
            confidence = 0.7
            severity = "high"
        elif part.health_score <= 60:
            # Monitoring - failure possible
            days_until_failure = 30.0
            confidence = 0.5
            severity = "medium"
        else:
            return None  # No prediction needed
        
        predicted_date = time.time() + (days_until_failure * 24 * 3600)
        
        # Estimate cost
        estimated_cost = self._estimate_replacement_cost(part.category)
        
        reasoning = f"Part health score: {part.health_score:.1f}%. "
        reasoning += f"Current status: {part.current_status.value}. "
        reasoning += f"Predicted failure in {days_until_failure:.0f} days."
        
        recommended_action = f"Order replacement {part.name} immediately" if severity == "critical" else \
                           f"Monitor closely and order replacement soon"
        
        return FailurePrediction(
            part_id=part.part_id,
            part_name=part.name,
            predicted_failure_date=predicted_date,
            confidence=confidence,
            severity=severity,
            reasoning=reasoning,
            recommended_action=recommended_action,
            estimated_cost=estimated_cost,
        )
    
    def _estimate_replacement_cost(self, category: str) -> float:
        """Estimate replacement cost."""
        costs = {
            "engine": 5000.0,
            "transmission": 3000.0,
            "turbo": 1500.0,
            "suspension": 800.0,
            "brakes": 400.0,
            "tires": 600.0,
            "battery": 150.0,
            "alternator": 300.0,
            "starter": 250.0,
            "fuel_pump": 200.0,
            "water_pump": 150.0,
            "timing_belt": 500.0,
            "spark_plugs": 50.0,
            "air_filter": 30.0,
            "oil_filter": 15.0,
        }
        return costs.get(category, 200.0)
    
    def _create_order(
        self,
        part_id: str,
        prediction: FailurePrediction,
    ) -> Optional[PartOrder]:
        """Create parts order."""
        if part_id not in self.parts:
            return None
        
        part = self.parts[part_id]
        
        # Find supplier and price
        supplier, price = self._find_supplier(part.name, part.category)
        if not supplier:
            LOGGER.warning("No supplier found for part: %s", part.name)
            return None
        
        # Estimate delivery (7 days default)
        estimated_delivery = time.time() + (7 * 24 * 3600)
        
        order = PartOrder(
            order_id=f"order_{int(time.time())}",
            part_id=part_id,
            part_name=part.name,
            supplier=supplier,
            price=price,
            estimated_delivery=estimated_delivery,
            status=OrderStatus.PENDING,
            created_at=time.time(),
        )
        
        self.orders.append(order)
        self._save_data()
        
        LOGGER.info("Order created: %s - $%.2f", part.name, price)
        return order
    
    def _find_supplier(self, part_name: str, category: str) -> tuple[Optional[str], float]:
        """Find supplier and price for part."""
        # Try API if available
        if self.supplier_api_url and REQUESTS_AVAILABLE:
            try:
                response = requests.get(
                    f"{self.supplier_api_url}/api/parts/search",
                    params={"name": part_name, "category": category},
                    timeout=10,
                )
                response.raise_for_status()
                
                data = response.json()
                if data.get("available"):
                    return data["supplier"], data["price"]
            except requests.RequestException as e:
                LOGGER.warning("Failed to query supplier API: %s", e)
        
        # Fallback: estimate price
        estimated_cost = self._estimate_replacement_cost(category)
        return "Local Supplier", estimated_cost
    
    def approve_order(self, order_id: str) -> bool:
        """Approve parts order."""
        order = next((o for o in self.orders if o.order_id == order_id), None)
        if not order:
            return False
        
        if order.status != OrderStatus.PENDING:
            return False
        
        order.status = OrderStatus.APPROVED
        order.approved_at = time.time()
        
        # Place order with supplier
        if self.supplier_api_url and REQUESTS_AVAILABLE:
            try:
                response = requests.post(
                    f"{self.supplier_api_url}/api/orders",
                    json={
                        "part_name": order.part_name,
                        "supplier": order.supplier,
                        "price": order.price,
                    },
                    timeout=10,
                )
                response.raise_for_status()
                
                data = response.json()
                order.status = OrderStatus.ORDERED
                order.ordered_at = time.time()
                order.tracking_number = data.get("tracking_number")
            except requests.RequestException as e:
                LOGGER.warning("Failed to place order: %s", e)
        
        self._save_data()
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel parts order."""
        order = next((o for o in self.orders if o.order_id == order_id), None)
        if not order:
            return False
        
        if order.status in [OrderStatus.ORDERED, OrderStatus.SHIPPED]:
            LOGGER.warning("Cannot cancel order that is already ordered/shipped")
            return False
        
        order.status = OrderStatus.CANCELLED
        self._save_data()
        return True
    
    def get_pending_orders(self) -> List[PartOrder]:
        """Get pending orders requiring approval."""
        return [o for o in self.orders if o.status == OrderStatus.PENDING]
    
    def get_active_predictions(self) -> List[FailurePrediction]:
        """Get active failure predictions."""
        current_time = time.time()
        return [p for p in self.predictions 
                if p.predicted_failure_date > current_time]
    
    def _save_data(self) -> None:
        """Save data to disk."""
        try:
            # Save parts
            parts_file = self.data_dir / "parts.json"
            with open(parts_file, 'w') as f:
                json.dump({
                    part_id: {
                        "part_id": part.part_id,
                        "name": part.name,
                        "category": part.category,
                        "current_status": part.current_status.value,
                        "health_score": part.health_score,
                        "predicted_failure_date": part.predicted_failure_date,
                        "confidence": part.confidence,
                        "last_inspection": part.last_inspection,
                        "mileage_at_install": part.mileage_at_install,
                        "current_mileage": part.current_mileage,
                    }
                    for part_id, part in self.parts.items()
                }, f, indent=2)
            
            # Save orders
            orders_file = self.data_dir / "orders.json"
            with open(orders_file, 'w') as f:
                json.dump([
                    {
                        "order_id": o.order_id,
                        "part_id": o.part_id,
                        "part_name": o.part_name,
                        "supplier": o.supplier,
                        "price": o.price,
                        "estimated_delivery": o.estimated_delivery,
                        "status": o.status.value,
                        "created_at": o.created_at,
                        "approved_at": o.approved_at,
                        "ordered_at": o.ordered_at,
                        "tracking_number": o.tracking_number,
                    }
                    for o in self.orders
                ], f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save data: %s", e)
    
    def _load_data(self) -> None:
        """Load data from disk."""
        try:
            # Load parts
            parts_file = self.data_dir / "parts.json"
            if parts_file.exists():
                with open(parts_file, 'r') as f:
                    data = json.load(f)
                    for part_id, part_data in data.items():
                        self.parts[part_id] = Part(
                            part_id=part_data["part_id"],
                            name=part_data["name"],
                            category=part_data["category"],
                            current_status=PartStatus(part_data["current_status"]),
                            health_score=part_data["health_score"],
                            predicted_failure_date=part_data.get("predicted_failure_date"),
                            confidence=part_data.get("confidence", 0.0),
                            last_inspection=part_data.get("last_inspection", time.time()),
                            mileage_at_install=part_data.get("mileage_at_install", 0.0),
                            current_mileage=part_data.get("current_mileage", 0.0),
                        )
            
            # Load orders
            orders_file = self.data_dir / "orders.json"
            if orders_file.exists():
                with open(orders_file, 'r') as f:
                    data = json.load(f)
                    for order_data in data:
                        self.orders.append(PartOrder(
                            order_id=order_data["order_id"],
                            part_id=order_data["part_id"],
                            part_name=order_data["part_name"],
                            supplier=order_data["supplier"],
                            price=order_data["price"],
                            estimated_delivery=order_data["estimated_delivery"],
                            status=OrderStatus(order_data["status"]),
                            created_at=order_data["created_at"],
                            approved_at=order_data.get("approved_at"),
                            ordered_at=order_data.get("ordered_at"),
                            tracking_number=order_data.get("tracking_number"),
                        ))
        except Exception as e:
            LOGGER.error("Failed to load data: %s", e)
