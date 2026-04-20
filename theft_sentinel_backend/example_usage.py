"""
Example Usage of AI Engine API
Demonstrates common integration patterns
"""
import requests
import base64
import cv2
import time
import json
from pathlib import Path

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "http://localhost:8000"
USERNAME = "admin"  # Change to your username
PASSWORD = "admin"  # Change to your password


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_jwt_token(username, password):
    """Get JWT token for authentication"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json()['access']
        print(f"✅ Authenticated as {username}")
        return token
    else:
        print(f"❌ Authentication failed: {response.text}")
        return None


def encode_frame(frame):
    """Encode OpenCV frame to base64"""
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')


def create_test_frame():
    """Create a simple test frame"""
    frame = cv2.imread("test_image.jpg") if Path("test_image.jpg").exists() else None
    
    if frame is None:
        # Create blank frame with text
        import numpy as np
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "Test Frame", (50, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
    
    return frame


# ============================================
# EXAMPLE 1: Simple Frame Analysis
# ============================================

def example_1_simple_analysis(token):
    """Simple frame analysis without saving to database"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Simple Frame Analysis")
    print("="*60)
    
    # Create test frame
    frame = create_test_frame()
    frame_b64 = encode_frame(frame)
    
    # Analyze frame
    response = requests.post(
        f"{BASE_URL}/api/ai/analyze-frame/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "frame": frame_b64,
            "save_to_db": False,
            "create_alert_on_theft": False
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Analysis complete")
        print(f"   Classification: {result['classification']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Detections: {len(result['detections'])}")
        print(f"   Tracks: {len(result['tracks'])}")
        print(f"   Processing Time: {result['processing_time_ms']:.1f} ms")
        
        if result['suspicious_tracks']:
            print(f"\n🚨 Suspicious Tracks:")
            for track in result['suspicious_tracks']:
                print(f"   Track #{track['track_id']}: Score {track['ml_score']:.2%}")
    else:
        print(f"❌ Error: {response.text}")


# ============================================
# EXAMPLE 2: Camera Stream Processing
# ============================================

def example_2_camera_processing(token, camera_id):
    """Process frame from camera and create alert if theft detected"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Camera Stream Processing")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/ai/process-camera/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "camera_id": camera_id,
            "save_to_db": True,
            "create_alert_on_theft": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Camera processed: {result.get('camera_name', 'Unknown')}")
        print(f"   Classification: {result['classification']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        
        if result.get('alert_created'):
            print(f"🚨 Alert created: {result['alert_id']}")
        
        if result.get('inference_id'):
            print(f"💾 Saved to database: {result['inference_id']}")
    else:
        print(f"❌ Error: {response.text}")


# ============================================
# EXAMPLE 3: Continuous Monitoring
# ============================================

def example_3_continuous_monitoring(token, camera_id, duration=30):
    """Monitor camera continuously for specified duration"""
    print("\n" + "="*60)
    print(f"EXAMPLE 3: Continuous Monitoring ({duration}s)")
    print("="*60)
    
    start_time = time.time()
    frame_count = 0
    theft_count = 0
    
    print("Monitoring started... (Press Ctrl+C to stop)")
    
    try:
        while time.time() - start_time < duration:
            response = requests.post(
                f"{BASE_URL}/api/ai/process-camera/",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "camera_id": camera_id,
                    "save_to_db": True,
                    "create_alert_on_theft": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                frame_count += 1
                
                status = "🟢 NORMAL"
                if result['classification'] == 'theft':
                    theft_count += 1
                    status = f"🔴 THEFT ({result['confidence']:.2%})"
                
                print(f"Frame {frame_count}: {status} | "
                      f"Detections: {len(result['detections'])} | "
                      f"Time: {result['processing_time_ms']:.1f}ms")
                
                if result.get('alert_created'):
                    print(f"   ⚠️  Alert created: {result['alert_id']}")
            
            time.sleep(1)  # Process 1 frame per second
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    
    print(f"\nSummary:")
    print(f"   Total frames: {frame_count}")
    print(f"   Theft detections: {theft_count}")
    print(f"   Average FPS: {frame_count / (time.time() - start_time):.1f}")


# ============================================
# EXAMPLE 4: Batch Frame Processing
# ============================================

def example_4_batch_processing(token, image_folder="test_images"):
    """Process multiple images from a folder"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Batch Frame Processing")
    print("="*60)
    
    image_path = Path(image_folder)
    if not image_path.exists():
        print(f"⚠️  Folder not found: {image_folder}")
        print("Creating test images...")
        image_path.mkdir(exist_ok=True)
        for i in range(3):
            test_frame = create_test_frame()
            cv2.imwrite(str(image_path / f"test_{i}.jpg"), test_frame)
    
    image_files = list(image_path.glob("*.jpg")) + list(image_path.glob("*.png"))
    
    if not image_files:
        print("No images found")
        return
    
    print(f"Processing {len(image_files)} images...")
    
    results = []
    for img_file in image_files:
        frame = cv2.imread(str(img_file))
        if frame is None:
            continue
        
        frame_b64 = encode_frame(frame)
        
        response = requests.post(
            f"{BASE_URL}/api/ai/analyze-frame/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "frame": frame_b64,
                "save_to_db": False,
                "create_alert_on_theft": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            results.append({
                "file": img_file.name,
                "classification": result['classification'],
                "confidence": result['confidence']
            })
            
            status = "✅" if result['classification'] == 'normal' else "🚨"
            print(f"{status} {img_file.name}: {result['classification']} ({result['confidence']:.2%})")
    
    # Summary
    theft_count = sum(1 for r in results if r['classification'] == 'theft')
    print(f"\nSummary: {theft_count}/{len(results)} potential thefts detected")


# ============================================
# EXAMPLE 5: Query Inference History
# ============================================

def example_5_query_history(token):
    """Query recent inference history"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Query Inference History")
    print("="*60)
    
    # Get recent theft detections
    response = requests.get(
        f"{BASE_URL}/api/ai/inference-history/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "classification": "theft",
            "min_confidence": 0.5,
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} theft detections")
        
        for inference in data['results'][:5]:
            print(f"\n📊 Inference {inference['id']}")
            print(f"   Camera: {inference.get('camera_name', 'Unknown')}")
            print(f"   Classification: {inference['classification']}")
            print(f"   Confidence: {inference['confidence']:.2%}")
            print(f"   Time: {inference['timestamp']}")
            if inference.get('alert_id'):
                print(f"   Alert: {inference['alert_id']}")
    else:
        print(f"❌ Error: {response.text}")


# ============================================
# EXAMPLE 6: Model Information
# ============================================

def example_6_model_info(token):
    """Get AI model information"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Model Information")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/api/ai/model-info/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        info = response.json()
        print(f"Detection Model: {info['detection_model']}")
        print(f"Pose Model: {info['pose_model']}")
        print(f"ML Classifier: {info['ml_classifier']}")
        print(f"Device: {info['device']}")
        print(f"CUDA Available: {info['cuda_available']}")
        print(f"Models Loaded: {info['models_loaded']}")
        print(f"ML Classifier Loaded: {info['ml_classifier_loaded']}")
    else:
        print(f"❌ Error: {response.text}")


# ============================================
# MAIN
# ============================================

def main():
    print("="*60)
    print("AI ENGINE - EXAMPLE USAGE")
    print("="*60)
    
    # Check health
    print("\nChecking AI Engine health...")
    response = requests.get(f"{BASE_URL}/api/ai/health/")
    if response.status_code == 200:
        health = response.json()
        print(f"✅ AI Engine Status: {health['status']}")
        print(f"   Models Loaded: {health['models_loaded']}")
        print(f"   Device: {health['device']}")
    else:
        print("❌ AI Engine not available")
        return
    
    # Authenticate
    print("\nAuthenticating...")
    token = get_jwt_token(USERNAME, PASSWORD)
    if not token:
        return
    
    # Run examples
    print("\n" + "="*60)
    print("Choose an example to run:")
    print("="*60)
    print("1. Simple Frame Analysis")
    print("2. Camera Stream Processing (requires camera_id)")
    print("3. Continuous Monitoring (requires camera_id)")
    print("4. Batch Frame Processing")
    print("5. Query Inference History")
    print("6. Model Information")
    print("7. Run All Examples")
    print("0. Exit")
    
    choice = input("\nEnter choice (0-7): ").strip()
    
    if choice == "1":
        example_1_simple_analysis(token)
    elif choice == "2":
        camera_id = input("Enter camera_id: ").strip()
        example_2_camera_processing(token, camera_id)
    elif choice == "3":
        camera_id = input("Enter camera_id: ").strip()
        duration = int(input("Enter duration in seconds (default 30): ") or "30")
        example_3_continuous_monitoring(token, camera_id, duration)
    elif choice == "4":
        example_4_batch_processing(token)
    elif choice == "5":
        example_5_query_history(token)
    elif choice == "6":
        example_6_model_info(token)
    elif choice == "7":
        example_1_simple_analysis(token)
        example_4_batch_processing(token)
        example_5_query_history(token)
        example_6_model_info(token)
        print("\n⚠️  Skipping camera examples (require camera_id)")
    elif choice == "0":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()

