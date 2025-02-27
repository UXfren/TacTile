import serial
import cv2
import numpy as np
from collections import deque
import pygame
import time

# Constants
SKIN_COLS = 20
SKIN_ROWS = 10
SKIN_CELLS = SKIN_COLS * SKIN_ROWS
PHYSICAL_W = 70
PHYSICAL_H = 94
SERIAL_PORT = '/dev/cu.usbmodem126032001'  # Change as per your port
SERIAL_RATE = 115200
THRESHOLD_MIN = 0
THRESHOLD_MAX = 800
GAIN_VALUE = 10

# Visualization settings
RESIZE_FACTOR = 30
TRANSLATE = 30
DISPLAY_W = (SKIN_COLS * RESIZE_FACTOR) + TRANSLATE + 140
DISPLAY_H = (SKIN_ROWS * RESIZE_FACTOR) + TRANSLATE + 140


class SensorMatrix:
    def __init__(self, port, baud_rate):
        self.serial_port = serial.Serial(port, baud_rate)
        self.skin_buffer = np.zeros(SKIN_CELLS)
        self.skin_data_valid = False

    def read_skin_buffer(self):
        if self.serial_port.in_waiting > 0:
            skin_data = self.serial_port.readline().decode('utf-8').strip()
            # Debugging line to check raw input
            print("Raw skin_data:\n", skin_data)
            skin_buffer = list(map(int, skin_data.split('\t')))
            self.skin_data_valid = len(skin_buffer) == SKIN_CELLS
            if self.skin_data_valid:
                self.skin_buffer = np.array(skin_buffer)
        return self.skin_data_valid


class ImageProcessor:
    def __init__(self):
        self.skin_image = np.zeros((SKIN_ROWS, SKIN_COLS), dtype=np.uint8)
        self.dest_img = np.zeros((DISPLAY_H, DISPLAY_W), dtype=np.uint8)
        self.threshold_blob_min = 15
        self.threshold_blob_max = 255

    def process_image(self, skin_buffer):
        # Ensure skin_buffer has correct number of elements
        if len(skin_buffer) != SKIN_CELLS:
            print("Error: skin_buffer size is incorrect. Expected:",
                  SKIN_CELLS, "Got:", len(skin_buffer))
            return self.dest_img

        # Reshape skin buffer to expected dimensions
        try:
            self.skin_image = skin_buffer.reshape(SKIN_ROWS, SKIN_COLS)
            print("Debug: Reshaped skin_buffer to skin_image with shape:",
                  self.skin_image.shape)
        except ValueError as e:
            print("Error reshaping skin_buffer:", e)
            return self.dest_img

        # Check if the skin image is empty
        if self.skin_image.size == 0:
            print("Warning: skin_image is empty.")
            return self.dest_img

        # Resize and threshold
        try:
            self.dest_img = cv2.resize(
                self.skin_image, (DISPLAY_W, DISPLAY_H), interpolation=cv2.INTER_LANCZOS4)
            _, self.dest_img = cv2.threshold(
                self.dest_img, self.threshold_blob_min, self.threshold_blob_max, cv2.THRESH_BINARY)
        except cv2.error as e:
            print("OpenCV error in resizing or thresholding:", e)
            return self.dest_img

        return self.dest_img


class BlobDetector:
    def __init__(self):
        self.params = cv2.SimpleBlobDetector_Params()
        self.params.minThreshold = 10
        self.params.maxThreshold = 200
        self.params.filterByArea = True
        self.params.minArea = 30
        self.params.maxArea = 2000
        self.detector = cv2.SimpleBlobDetector_create(self.params)

    def detect_blobs(self, image):
        keypoints = self.detector.detect(image)
        # Returns position and size
        return [(kp.pt[0], kp.pt[1], kp.size) for kp in keypoints]


class TouchVisualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
        self.clock = pygame.time.Clock()

    def draw_skin_image(self, image):
        surface = pygame.surfarray.make_surface(
            cv2.cvtColor(image, cv2.COLOR_GRAY2RGB).swapaxes(0, 1))
        self.screen.blit(surface, (TRANSLATE, TRANSLATE))

    def draw_blobs(self, blobs):
        for blob in blobs:
            pygame.draw.circle(self.screen, (0, 255, 0), (int(
                blob[0]), int(blob[1])), int(blob[2] * 0.75), 2)

    def update(self):
        pygame.display.flip()
        self.clock.tick(30)

    def quit(self):
        pygame.quit()


def main():
    sensor_matrix = SensorMatrix(SERIAL_PORT, SERIAL_RATE)
    image_processor = ImageProcessor()
    blob_detector = BlobDetector()
    visualizer = TouchVisualizer()

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    visualizer.quit()
                    return

            # Read sensor matrix data
            if sensor_matrix.read_skin_buffer():
                skin_image = image_processor.process_image(
                    sensor_matrix.skin_buffer)
                blobs = blob_detector.detect_blobs(skin_image)

                # Display
                visualizer.screen.fill((200, 200, 200))
                visualizer.draw_skin_image(skin_image)
                visualizer.draw_blobs(blobs)
                visualizer.update()
    except KeyboardInterrupt:
        visualizer.quit()


if __name__ == "__main__":
    main()
