import math

class RiskEngine:
    def __init__(self, high_risk_threshold=50, med_risk_threshold=150):
        self.high_risk_threshold = high_risk_threshold
        self.med_risk_threshold = med_risk_threshold

    def calculate_min_distance(self, box_tree, box_line):
        """
        Calculate min pixel distance between two bounding boxes.
        Boxes are [x1, y1, x2, y2]
        """
        tx1, ty1, tx2, ty2 = box_tree
        lx1, ly1, lx2, ly2 = box_line
        
        # Check for overlap
        overlap_x = max(tx1, lx1) < min(tx2, lx2)
        overlap_y = max(ty1, ly1) < min(ty2, ly2)
        if overlap_x and overlap_y:
            return 0.0 # Touching or overlapping
            
        # Distances along X and Y
        dx = max(0, max(tx1, lx1) - min(tx2, lx2))
        dy = max(0, max(ty1, ly1) - min(ty2, ly2))
        
        return math.sqrt(dx*dx + dy*dy)

    def classify_risk(self, distance):
        if distance == 0:
            return "HIGH" # Overlap
        elif distance < self.high_risk_threshold:
            return "HIGH"
        elif distance < self.med_risk_threshold:
            return "MEDIUM"
        else:
            return "LOW"

    def analyze_frame(self, detections):
        """
        Analyzes detected objects and finds the highest risk pairs.
        Returns [{'pair': (tree_idx, line_idx), 'distance': min_dist, 'risk': risk_level}]
        """
        trees = [d for d in detections if d['class'] == 'tree']
        lines = [d for d in detections if d['class'] == 'powerline']
        
        anomalies = []
        for t_idx, tree in enumerate(trees):
            for l_idx, line in enumerate(lines):
                dist = self.calculate_min_distance(tree['bbox'], line['bbox'])
                risk = self.classify_risk(dist)
                
                if risk != "LOW":
                    anomalies.append({
                        'tree_bbox': tree['bbox'],
                        'line_bbox': line['bbox'],
                        'distance': dist,
                        'risk': risk
                    })
                    
        return anomalies
