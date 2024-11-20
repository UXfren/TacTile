# blob_detection.py
import numpy as np
import cv2
import time


def load_image():
    # Load the saved sensor matrix image as a NumPy array
    try:
        return np.load("sensor_matrix.npy")
    except FileNotFoundError:
        print("Image file not found.")
        return None

# Blob detection function


def detect_blobs(image):
    # Convert to grayscale if needed
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Set up the blob detector with default parameters
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 50
    params.maxArea = 5000
    detector = cv2.SimpleBlobDetector_create(params)

    # Detect blobs
    keypoints = detector.detect(gray_image)

    # Draw detected blobs as red circles
    output_image = cv2.drawKeypoints(image, keypoints, np.array([]), (0, 0, 255),
                                     cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    return output_image, keypoints


if __name__ == '__main__':
    cv2.namedWindow("Blob Detection", cv2.WINDOW_NORMAL)

    while True:
        # Load the latest sensor matrix image
        image = load_image()

        if image is not None:
            # Run blob detection on the loaded image
            blob_image, keypoints = detect_blobs(image)

            # Display the blob detection results
            cv2.imshow("Blob Detection", blob_image)

            # Optional: Print blob coordinates
            for keypoint in keypoints:
                print(f"Blob at (x: {keypoint.pt[0]}, y: {
                      keypoint.pt[1]}), size: {keypoint.size}")

        # Refresh every 100ms to check for new data
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
