import cv2
from ultralytics import YOLO

# Load the YOLOv8 model (you can use different versions such as 'yolov8l.pt', 'yolov8s.pt', etc.)
model = YOLO('yolov8n.pt')

# Open the input video file
video_path = 'Video.mp4'  # Change this to your video file path
cap = cv2.VideoCapture(video_path)

# Check if video opened successfully
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# Get video properties
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Define the codec and create a VideoWriter object to save the output
output_path = 'output_video.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for mp4 format
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# Loop through each frame of the video
while cap.isOpened():
    ret, frame = cap.read()
    
    if not ret:
        print("Finished processing video or an error occurred.")
        break

    # Run YOLOv8 model on the frame
    results = model(frame)

    # Draw bounding boxes on detected humans (class ID 0 corresponds to 'person')
    for result in results:
        for box in result.boxes:
            if int(box.cls[0]) == 0:  # '0' is the class index for 'person' in the COCO dataset
                # Get bounding box coordinates and confidence score
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0]
                
                # Draw the bounding box and label on the frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green box
                cv2.putText(frame, f'Person {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Write the processed frame to the output video
    out.write(frame)

# Release the video capture and writer objects
cap.release()
out.release()

print(f"Processed video saved as {output_path}")
