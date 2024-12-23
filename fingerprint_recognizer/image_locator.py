import pyautogui
import cv2
import numpy as np
import os
from skimage.metrics import structural_similarity as ssim

from concurrent.futures import ThreadPoolExecutor, as_completed


class ImageLocator:
    def __init__(self, scale_range=(0.2, 2.1), scale_step=0.5, threshold=0.75):
        """Initialize the ImageLocator with template paths, scale range, step, and threshold."""
        
        self.template_paths : list
        self.scale_range = scale_range
        self.scale_step = scale_step
        self.threshold = threshold
        self.templates = []

    def load_templates(self, template_paths):
        """Load and process templates from file paths."""
        self.templates = []
        for path in template_paths:
            if not os.path.exists(path):
                print(f"Template file not found: {path}")
                continue
            
            template = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if template is None:
                print(f"Failed to load image: {path}")
                continue
            
            self.templates.append({
                'path': path,
                'image': template,
                'grayscale': cv2.cvtColor(template, cv2.COLOR_BGRA2GRAY) if template.shape[-1] == 4 else cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            })

    def take_screenshot(self):
        """Capture a screenshot of the current screen."""
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        return cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    def preprocess_image(self, image):
        """Preprocess the image by reducing noise and enhancing details."""
        # Apply Gaussian blur for denoising
        blurred_image = cv2.GaussianBlur(image, (5, 5), 0)
        return blurred_image

    def locate_images_on_screen(self, screenshot, only_once=False):
        """Locate images on the screen using template matching with multithreading."""
        matches = []
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        screenshot_gray = self.preprocess_image(screenshot_gray)
        
        # Create a set to track which templates have already been processed if 'only_once' is set
        did_append = set()

        # This will hold the futures for asynchronous tasks
        future_to_template = {}

        # Function to process each template
        def process_template(template_data, index):
            nonlocal matches  # Access the matches list
            if only_once and index in did_append:
                return []  # No need to process this template if it was already processed

            template_gray = template_data['grayscale']
            template_gray = self.preprocess_image(template_gray)

            local_matches = []  # Local matches for this template

            for scale in np.arange(self.scale_range[0], self.scale_range[1], self.scale_step):
                scaled_template = cv2.resize(template_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                if scaled_template.shape[0] > screenshot_gray.shape[0] or scaled_template.shape[1] > screenshot_gray.shape[1]:
                    continue  # Skip if the scaled template is larger

                result = cv2.matchTemplate(screenshot_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= self.threshold)
                h, w = scaled_template.shape[:2]

                for pt in zip(*locations[::-1]):
                    new_match = {
                        'index': index,
                        'path': template_data['path'],
                        'x': int(pt[0]),
                        'y': int(pt[1]),
                        'width': int(w),
                        'height': int(h)
                    }

                    if not self.is_overlapping(matches, new_match):
                        local_matches.append(new_match)

            return local_matches

        # Use ThreadPoolExecutor to process templates in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:  # Adjust max_workers for your hardware
            for index, template_data in enumerate(self.templates):
                future = executor.submit(process_template, template_data, index)
                future_to_template[future] = template_data

            # Collect results as they are completed
            for future in as_completed(future_to_template):
                result = future.result()
                matches.extend(result)  # Add the matches found by this future

                # If 'only_once' is True, mark this template as processed
                template_data = future_to_template[future]
                if only_once:
                    did_append.add(self.templates.index(template_data))

        return matches


    def is_overlapping(self, matches, new_match, overlap_threshold=0.2):
        """Check if the new match overlaps significantly with any existing match."""
        for match in matches:
            x1, y1, w1, h1 = match['x'], match['y'], match['width'], match['height']
            x2, y2, w2, h2 = new_match['x'], new_match['y'], new_match['width'], new_match['height']

            x_intersection = max(x1, x2)
            y_intersection = max(y1, y2)
            w_intersection = min(x1 + w1, x2 + w2) - x_intersection
            h_intersection = min(y1 + h1, y2 + h2) - y_intersection

            if w_intersection > 0 and h_intersection > 0:
                intersection_area = w_intersection * h_intersection
                area1 = w1 * h1
                area2 = w2 * h2
                overlap = intersection_area / float(area1 + area2 - intersection_area)

                if overlap > overlap_threshold:
                    return True

        return False

    def orb_matching(self, screenshot):
        """ORB (Oriented FAST and Rotated BRIEF) feature matching with adjusted sensitivity."""
        matches = []
        orb = cv2.ORB_create(nfeatures=5000, scaleFactor=1.2, nlevels=10)

        for template_data in self.templates:
            template = template_data['image']
            keypoints1, descriptors1 = orb.detectAndCompute(template, None)
            keypoints2, descriptors2 = orb.detectAndCompute(screenshot, None)
            
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            raw_matches = bf.match(descriptors1, descriptors2)
            raw_matches = sorted(raw_matches, key=lambda x: x.distance)
            
            distance_threshold = 75
            filtered_matches = [match for match in raw_matches if match.distance < distance_threshold]
            
            for match in filtered_matches[:20]:
                kp = keypoints2[match.trainIdx].pt
                matches.append({'x': int(kp[0]), 'y': int(kp[1]), 'width': 50, 'height': 50, 'score': match.distance})
        
        return matches

    def ssim_matching(self, screenshot):
        """SSIM (Structural Similarity Index) matching."""
        matches = []
        for template_data in self.templates:
            template_gray = template_data['grayscale']
            h, w = template_gray.shape
            for y in range(0, screenshot.shape[0] - h + 1, 10):
                for x in range(0, screenshot.shape[1] - w + 1, 10):
                    patch = screenshot[y:y + h, x:x + w]
                    patch_resized = cv2.resize(patch, (w, h))
                    score = ssim(template_gray, patch_resized, multichannel=False)

                    if score >= self.threshold:
                        matches.append({'x': x, 'y': y, 'width': w, 'height': h, 'score': score})

        return matches

    def locate_objects(self, screenshot):
        """Combine different matching techniques to improve object detection."""
        template_matches = self.locate_images_on_screen(screenshot)
        orb_matches = self.orb_matching(screenshot)
        ssim_matches = self.ssim_matching(screenshot)

        all_matches = template_matches + orb_matches + ssim_matches
        unique_matches = []
        for match in all_matches:
            if not self.is_overlapping(unique_matches, match):
                unique_matches.append(match)

        return unique_matches
