import numpy as np
import cv2
import serial.tools.list_ports
import random


def map_value(value, in_min=0, in_max=1023, out_min=0, out_max=255):
    # Function to map the 0-1023 values to a grayscale range
    # could also bit shift it from 10 to 8 (computationally faster)
    return int(value/4)


def generate_image(data):
    # Function to convert the sensor data into a 20x10 image
    # Reshape the flat list into a 20x10 numpy array
    matrix = np.array(data).reshape((10, 20))

    # Map the 0-1023 range to 0-255 for grayscale
    mapped_matrix = np.vectorize(map_value)(matrix)

    # Resize the 20x10 image to make it larger for visualization
    resized_image = cv2.resize(mapped_matrix.astype(
        np.uint8), (600, 300), interpolation=cv2.INTER_LANCZOS4)
    return resized_image


def initialize_blob_detector():

    # Initialize blob detector with parameters
    params = cv2.SimpleBlobDetector_Params()

    '''Thresholding'''

    # params.minThreshold = 100
    # params.maxThreshold = 900

    params.minThreshold = cv2.getTrackbarPos("Thresh Min", "Controls")
    params.maxThreshold = cv2.getTrackbarPos("Thresh Max", "Controls")

    '''------------------------------------------------------------------------'''

    '''Filter by Area'''

    params.filterByArea = False

    # params.minArea = 15
    # params.maxArea = 500

    params.minArea = cv2.getTrackbarPos("Area Min", "Controls")
    params.maxArea = cv2.getTrackbarPos("Area Max", "Controls")

    '''------------------------------------------------------------------------'''

    '''Other Control Toggles'''

    params.filterByCircularity = False
    params.filterByConvexity = False
    params.filterByInertia = False

    return cv2.SimpleBlobDetector_create(params)


def apply_threshold_and_invert(img, min_val=250, max_val=255):
    # Apply a threshold and ensure background is white where there are no blobs
    # Invert binary threshold to keep darker blobs
    _, thresholded_img = cv2.threshold(
        img, min_val, max_val, cv2.THRESH_BINARY)
    return thresholded_img


def nothing(x):
    # Callback function for trackbars (required but not used)
    pass


def create_trackbars():
    # Create trackbars for parameter adjustment
    cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("Thresh Min", "Controls", 10, 255, nothing)
    cv2.createTrackbar("Thresh Max", "Controls", 255, 255, nothing)
    cv2.createTrackbar("Area Min", "Controls", 15, 1000, nothing)
    cv2.createTrackbar("Area Max", "Controls", 500, 5000, nothing)


if __name__ == '__main__':
    # Serial port setup
    comport = '/dev/cu.usbmodem126032001'
    baudrate = 115200

    # Initialize OpenCV window and blob detector
    cv2.namedWindow("Sensor Matrix", cv2.WINDOW_NORMAL)
    create_trackbars()  # Create trackbars for on-screen controls
    detector = initialize_blob_detector()

    # CAN THESE BE REMOVED NOW THAT SLIDERS EXIST?
    # DOES THE THRESHOLDING STILL WORK AS EXPECTED?
    # Set threshold values
    # threshold_min = 10  # Adjust to detect only specific dark blobs
    # threshold_max = 255  # Keep background white

    # Toggle states
    show_blobs = True       # Toggle for displaying blobs
    show_threshold = True   # Toggle for displaying the black-and-white thresholded image

    while True:

        # Read current trackbar positions for threshold and area parameters
        threshold_min = cv2.getTrackbarPos("Thresh Min", "Controls")
        threshold_max = cv2.getTrackbarPos("Thresh Max", "Controls")
        min_area = cv2.getTrackbarPos("Area Min", "Controls")
        max_area = cv2.getTrackbarPos("Area Max", "Controls")

        # Update blob detector parameters
        detector = initialize_blob_detector()

        data = serial.Serial(
            comport, baudrate, timeout=0.1).readline().decode()
        if data:
            values = list(map(int, data.split()))
            if len(values) == 200:
                sensor_data = values
            else:
                continue
        else:
            continue

        # Generate the image from the sensor data
        img = generate_image(sensor_data)

        # Apply inverted thresholding to keep darker areas as blobs
        thresholded_img = apply_threshold_and_invert(
            img, min_val=threshold_min, max_val=threshold_max)

        # Initialize the display base as a white background
        display_img = np.full_like(thresholded_img, 255)
        display_img = cv2.cvtColor(display_img, cv2.COLOR_GRAY2BGR)

        # Show thresholded image if enabled
        if show_threshold:
            display_img = cv2.cvtColor(
                thresholded_img.copy(), cv2.COLOR_GRAY2BGR)

        # CHECK IF THIS NEEDS TO BE CALLED HERE *AND* IN THE IF STATEMENT BELOW
        # Perform blob detection on the image
        keypoints = detector.detect(thresholded_img)

        # Show blobs if enabled
        if show_blobs:
            # Convert to color to draw in color
            blob_image = cv2.cvtColor(thresholded_img, cv2.COLOR_GRAY2BGR)
            keypoints = detector.detect(thresholded_img)
            for i, keypoint in enumerate(keypoints):
                x, y = int(keypoint.pt[0]), int(keypoint.pt[1])
                size = int(keypoint.size)

                # Blob circle
                cv2.circle(display_img, (x, y), int(
                    keypoint.size / 2), (0, 0, 255), 2)  # Red contour
                cv2.circle(display_img, (x, y), 6,
                           (255, 0, 0), -1)  # Blue center

                # Blob info text
                blob_info = f"ID: {i}, X: {x}, Y: {y}, Size: {size}"
                cv2.putText(display_img, blob_info, (x + 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        # Display the image with blobs in the OpenCV window
        cv2.imshow("Sensor Matrix", display_img)

        # # Display the image in the OpenCV window
        # cv2.imshow("Sensor Matrix", img)

        # Wait for a key press and handle 'q', 't', and 'b'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break  # Quit the program
        elif key == ord('t'):
            show_threshold = not show_threshold  # Toggle show_threshold
        elif key == ord('b'):
            show_blobs = not show_blobs  # Toggle show_blobs

    # Release resources
    cv2.destroyAllWindows()
