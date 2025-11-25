"""
Data Cleaning Engine

Advanced data cleaning, validation, and quality assurance.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore


class DataCleaningEngine:
    """
    Advanced data cleaning engine.
    
    Features:
    - Outlier detection
    - Missing value handling
    - Data normalization
    - Type conversion
    - Range validation
    - Pattern matching
    - Statistical cleaning
    """
    
    def __init__(self):
        """Initialize data cleaning engine."""
        self.cleaning_rules: Dict[str, List[Callable]] = {}
        self.statistics: Dict[str, Dict[str, Any]] = {}
    
    def clean_record(
        self,
        record: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Clean a data record.
        
        Args:
            record: Data record to clean
            schema: Optional schema definition
        
        Returns:
            Tuple of (cleaned_record, warnings)
        """
        cleaned = {}
        warnings = []
        
        for key, value in record.items():
            try:
                # Get cleaning rules for this field
                rules = self.cleaning_rules.get(key, [])
                
                # Apply cleaning
                cleaned_value = value
                for rule in rules:
                    cleaned_value, warning = rule(cleaned_value)
                    if warning:
                        warnings.append(f"{key}: {warning}")
                
                # Schema validation
                if schema and key in schema:
                    cleaned_value, schema_warnings = self._validate_schema(
                        key, cleaned_value, schema[key]
                    )
                    warnings.extend(schema_warnings)
                
                cleaned[key] = cleaned_value
                
            except Exception as e:
                LOGGER.warning("Error cleaning field %s: %s", key, e)
                warnings.append(f"{key}: Cleaning error - {e}")
                cleaned[key] = value  # Keep original on error
        
        return cleaned, warnings
    
    def add_cleaning_rule(self, field: str, rule: Callable) -> None:
        """
        Add cleaning rule for field.
        
        Args:
            field: Field name
            rule: Cleaning function (takes value, returns (cleaned_value, warning))
        """
        if field not in self.cleaning_rules:
            self.cleaning_rules[field] = []
        self.cleaning_rules[field].append(rule)
    
    def detect_outliers(
        self,
        values: List[float],
        method: str = "iqr"  # "iqr", "zscore", "isolation"
    ) -> List[int]:
        """
        Detect outliers in data.
        
        Args:
            values: List of numeric values
            method: Detection method
        
        Returns:
            List of outlier indices
        """
        if not NUMPY_AVAILABLE or not values:
            return []
        
        values_array = np.array(values)
        outliers = []
        
        if method == "iqr":
            # Interquartile Range method
            q1 = np.percentile(values_array, 25)
            q3 = np.percentile(values_array, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for i, val in enumerate(values):
                if val < lower_bound or val > upper_bound:
                    outliers.append(i)
        
        elif method == "zscore":
            # Z-score method
            mean = np.mean(values_array)
            std = np.std(values_array)
            if std > 0:
                z_scores = np.abs((values_array - mean) / std)
                outliers = [i for i, z in enumerate(z_scores) if z > 3]
        
        return outliers
    
    def handle_missing_values(
        self,
        data: List[Dict[str, Any]],
        strategy: str = "mean"  # "mean", "median", "mode", "forward_fill", "drop"
    ) -> List[Dict[str, Any]]:
        """
        Handle missing values in dataset.
        
        Args:
            data: List of records
            strategy: Imputation strategy
        
        Returns:
            List of records with missing values handled
        """
        if not data:
            return data
        
        # Identify numeric fields
        numeric_fields = {}
        for record in data:
            for key, value in record.items():
                if isinstance(value, (int, float)) and not np.isnan(value) if NUMPY_AVAILABLE else True:
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(value)
        
        # Apply strategy
        for field, values in numeric_fields.items():
            if strategy == "mean" and values:
                fill_value = sum(values) / len(values)
            elif strategy == "median" and values:
                sorted_values = sorted(values)
                fill_value = sorted_values[len(sorted_values) // 2]
            elif strategy == "mode" and values:
                fill_value = max(set(values), key=values.count)
            else:
                fill_value = 0.0
            
            # Fill missing values
            for record in data:
                if field not in record or record[field] is None:
                    record[field] = fill_value
        
        return data
    
    def normalize_data(
        self,
        data: List[Dict[str, Any]],
        method: str = "min_max"  # "min_max", "z_score", "decimal"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Tuple[float, float]]]:
        """
        Normalize numeric data.
        
        Args:
            data: List of records
            method: Normalization method
        
        Returns:
            Tuple of (normalized_data, normalization_params)
        """
        if not data or not NUMPY_AVAILABLE:
            return data, {}
        
        # Find numeric fields
        numeric_fields = {}
        for record in data:
            for key, value in record.items():
                if isinstance(value, (int, float)):
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(value)
        
        normalization_params = {}
        normalized_data = [dict(r) for r in data]  # Copy
        
        for field, values in numeric_fields.items():
            if not values:
                continue
            
            values_array = np.array(values)
            
            if method == "min_max":
                min_val = np.min(values_array)
                max_val = np.max(values_array)
                if max_val > min_val:
                    normalized = (values_array - min_val) / (max_val - min_val)
                    normalization_params[field] = (min_val, max_val)
                else:
                    normalized = values_array
                    normalization_params[field] = (0, 1)
            
            elif method == "z_score":
                mean = np.mean(values_array)
                std = np.std(values_array)
                if std > 0:
                    normalized = (values_array - mean) / std
                    normalization_params[field] = (mean, std)
                else:
                    normalized = values_array
                    normalization_params[field] = (0, 1)
            
            else:
                normalized = values_array
                normalization_params[field] = (0, 1)
            
            # Apply normalization
            for i, record in enumerate(normalized_data):
                if field in record:
                    record[field] = float(normalized[i])
        
        return normalized_data, normalization_params
    
    def _validate_schema(
        self,
        field: str,
        value: Any,
        schema: Dict[str, Any]
    ) -> Tuple[Any, List[str]]:
        """Validate value against schema."""
        warnings = []
        
        # Type validation
        expected_type = schema.get("type")
        if expected_type:
            if expected_type == "int" and not isinstance(value, int):
                try:
                    value = int(value)
                except:
                    warnings.append(f"{field}: Type mismatch, expected int")
            elif expected_type == "float" and not isinstance(value, float):
                try:
                    value = float(value)
                except:
                    warnings.append(f"{field}: Type mismatch, expected float")
        
        # Range validation
        if "min" in schema and value < schema["min"]:
            warnings.append(f"{field}: Value below minimum ({schema['min']})")
            value = schema["min"]
        if "max" in schema and value > schema["max"]:
            warnings.append(f"{field}: Value above maximum ({schema['max']})")
            value = schema["max"]
        
        # Pattern validation
        if "pattern" in schema:
            pattern = schema["pattern"]
            if isinstance(value, str) and not re.match(pattern, value):
                warnings.append(f"{field}: Pattern mismatch")
        
        return value, warnings


__all__ = ["DataCleaningEngine"]









