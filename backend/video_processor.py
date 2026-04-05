import cv2
import os
import json
from datetime import datetime
from detector import UtilityDetector
from risk_engine import RiskEngine

class VideoProcessor:
    def __init__(self, output_dir='output', snapshot_dir='snapshots'):
        self.output_dir = output_dir
        self.snapshot_dir = snapshot_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        self.detector = UtilityDetector()
        self.risk_engine = RiskEngine()
        
    def process_video(self, video_path, skip_frames=30):
        """
        Process video and return results log and output path.
        skip_frames: analyze every Nth frame (default approx 1 frame/sec for 30fps).
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        output_filename = f"processed_{os.path.basename(video_path)}"
        output_path = os.path.join(self.output_dir, output_filename)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_idx = 0
        logs = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract and analyze every X frames
            if frame_idx % skip_frames == 0:
                # Detect and Analyze
                detections = self.detector.detect(frame)
                
                # Demo simulation of powerline across middle
                detections.extend(self.detector.simulate_powerlines(frame.shape))
                
                anomalies = self.risk_engine.analyze_frame(detections)
                
                results_entry = {
                    'frame': frame_idx,
                    'timestamp': str(datetime.now()),
                    'detections': detections,
                    'anomalies': anomalies
                }
                logs.append(results_entry)
                
                # Annotate and save high risk snapshots
                for anomaly in anomalies:
                    # Draw boxes
                    self.annotate_frame(frame, detections, anomaly)
                    
                    if anomaly['risk'] == "HIGH":
                        # Save high risk snapshot
                        snapshot_name = f"risk_{frame_idx}_{datetime.now().strftime('%H%M%S')}.jpg"
                        snapshot_path = os.path.join(self.snapshot_dir, snapshot_name)
                        cv2.imwrite(snapshot_path, frame)
                        results_entry['snapshot'] = snapshot_path

                # Overlay general info
                cv2.putText(frame, f"Frame: {frame_idx} | FPS: {fps}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            out.write(frame)
            frame_idx += 1
            if frame_idx > 500: # Limit for demo to prevent huge processing time
                break
                
        cap.release()
        out.release()
        
        # Save logs to JSON
        log_path = os.path.join(self.output_dir, f"logs_{os.path.basename(video_path)}.json")
        with open(log_path, 'w') as f:
            json.dump(logs, f, indent=4)
            
        return output_path, log_path, logs

    def annotate_frame(self, frame, detections, anomaly):
        """Draw bounding boxes and risk labels on the frame."""
        # Draw detections
        for d in detections:
            x1, y1, x2, y2 = map(int, d['bbox'])
            color = (0, 255, 0) # Green for general
            if d['class'] == 'powerline':
                color = (255, 100, 100) # Light blue
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{d['class']} ({d['conf']:.2f})"
            cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Highlight anomalies
        risk_color = {
            "HIGH": (0, 0, 255),    # Red
            "MEDIUM": (0, 165, 255), # Orange
            "LOW": (0, 255, 0)      # Green
        }
        
        risk = anomaly['risk']
        color = risk_color.get(risk, (255, 255, 255))
        
        # Draw connection line distance
        # Placeholder for simplified center-to-center or nearest-edge
        # Actually risk_engine has the logic
        dist_meta = f"Risk: {risk} | Dist: {int(anomaly['distance'])} px"
        cv2.putText(frame, dist_meta, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 3)
