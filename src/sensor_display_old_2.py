import numpy as np
import cv2
import serial.tools.list_ports


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

    params.minThreshold = 15
    params.maxThreshold = 255

    params.filterByArea = False

    params.minArea = 10
    params.maxArea = 500

    params.filterByCircularity = False
    params.filterByConvexity = False
    params.filterByInertia = False

    return cv2.SimpleBlobDetector_create(params)


if __name__ == '__main__':
    # Serial port setup
    comport = '/dev/cu.usbmodem126032001'
    baudrate = 115200

    # Initialize OpenCV window and blob detector
    cv2.namedWindow("Sensor Matrix", cv2.WINDOW_NORMAL)
    detector = initialize_blob_detector()

    while True:
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

        # Perform blob detection on the image
        keypoints = detector.detect(img)

        # Draw detected blobs as red circles on the image
        blob_image = cv2.drawKeypoints(
            img, keypoints, np.array([]),
            (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
        )

        # Display the image with blobs in the OpenCV window
        cv2.imshow("Sensor Matrix", blob_image)

        # # Display the image in the OpenCV window
        # cv2.imshow("Sensor Matrix", img)

        # Break the loop if the user presses the 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cv2.destroyAllWindows()
