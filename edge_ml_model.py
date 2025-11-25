"""
Edge ML Model Module
Handles TensorFlow Lite model loading and inference
"""

import os
import numpy as np

try:
    import tensorflow as tf
    from tensorflow.lite.python.interpreter import Interpreter
except ImportError:
    from tflite_runtime.interpreter import Interpreter


class EdgeMLModel:
    """
    TensorFlow Lite model for anomaly detection.
    The model expects a vector of normalized sensor values.
    """
    
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            print(f"[WARN] No model found at {model_path}, skipping ML inference.")
            self.model = None
            return
        
        self.model = Interpreter(model_path=model_path)
        self.model.allocate_tensors()
        self.input_details = self.model.get_input_details()
        self.output_details = self.model.get_output_details()
        print(f"[ML] Loaded TensorFlow Lite model: {model_path}")

    def predict(self, features):
        """Run inference on feature vector"""
        if not self.model:
            return None
        input_data = np.array([features], dtype=np.float32)
        self.model.set_tensor(self.input_details[0]['index'], input_data)
        self.model.invoke()
        output_data = self.model.get_tensor(self.output_details[0]['index'])
        return float(output_data[0])

