import os
import cv2
import numpy as np
from ultralytics import YOLO

class UtilityDetector:
    def __init__(self, model_path='yolov8n.pt'):
        self.model = YOLO(model_path)
        # Class mapping for COCO (yolov8n) vs Specialized (what we want)
        # In a real scenario, these would be the direct indices of the fine-tuned model
        self.class_names = {
            'tree': 'potted plant', # Proxy class or custom
            'powerline': 'powerline', # Only in custom models
            'pole': 'pole'  # Only in custom models
        }
        
    def detect(self, frame):
        """
        Detect objects in a frame.
        Returns a list of dicts: [{'class': 'tree', 'bbox': [x1, y1, x2, y2], 'conf': 0.8}]
        """
        results = self.model.predict(frame, verbose=False)[0]
        detections = []
        
        # Mapping COCO indices to our target classes for demo purposes
        # COCO 58: potted plant -> Tree
        # COCO 72: traffic light/pole -> Pole (approximation)
        
        for result in results.boxes:
            cls_id = int(result.cls[0])
            conf = float(result.conf[0])
            bbox = result.xyxy[0].tolist() # [x1, y1, x2, y2]
            
            label = self.model.names[cls_id]
            
            # Map detected label to our target classes
            target_class = None
            if label == 'potted plant':
                target_class = 'tree'
            elif label == 'traffic light' or label == 'bench': # Heuristics for demo
                target_class = 'pole'
            
            if target_class and conf > 0.3:
                detections.append({
                    'class': target_class,
                    'bbox': bbox,
                    'conf': conf
                })
        
        # DEMO FALLBACK: If no powerlines detected (as yolov8n doesn't have them),
        # we simulate one across the middle if in simulation mode
        # In production, this section would be removed or integrated into the model.
        return detections

    def simulate_powerlines(self, frame_shape):
        """Helper for demo: creates a mock powerline across the frame."""
        h, w = frame_shape[:2]
        # Simulate a powerline from left to right at 1/3 height
        return [{
            'class': 'powerline',
            'bbox': [0, h//3, w, h//3 + 10],
            'conf': 1.0
        }]
