import numpy as np
import cv2
import serial_reader

# Function to map the 0-1023 values to a grayscale range


def map_value(value, in_min=0, in_max=1023, out_min=0, out_max=255):
    return int(value/4)

# Function to convert the sensor data into a 20x10 image


def generate_image(data):
    # Reshape the flat list into a 20x10 numpy array
    # WTF, I can't believe there's actually a tool to do this!
    matrix = np.array(data).reshape((10, 20))

    # Map the 0-1023 range to 0-255 for grayscale
    mapped_matrix = np.vectorize(map_value)(matrix)

    # Resize the 20x10 image to make it larger for visualization
    resized_image = cv2.resize(mapped_matrix.astype(
        np.uint8), (600, 300), interpolation=cv2.INTER_NEAREST)
    return resized_image

    # # Convert to a 3-channel grayscale image for OpenCV display
    # color_image = cv2.cvtColor(resized_image, cv2.COLOR_GRAY2BGR)
    # return color_image


if __name__ == '__main__':
    # Read the serial data
    comport = '/dev/cu.usbmodem126032001'
    baudrate = 115200

    # Create a window for OpenCV display
    cv2.namedWindow("Sensor Matrix", cv2.WINDOW_NORMAL)

    # this is the problem (purge the buffer or if serial_reader.available: )
    for sensor_data in serial_reader.read_serial(comport, baudrate):
        # Generate the image from the sensor data
        img = generate_image(sensor_data)

        # Save the image as a NumPy array for blob detection
        # np.save("sensor_matrix.npy", img) # DONT DO THIS

        # Display the image in the OpenCV window
        cv2.imshow("Sensor Matrix", img)

        # Break the loop if the user presses the 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cv2.destroyAllWindows()
