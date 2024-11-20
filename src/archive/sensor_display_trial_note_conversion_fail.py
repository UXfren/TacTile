import numpy as np
import cv2
import serial.tools.list_ports
import random
from midi_note_grid_complex import MIDINoteGrid
from midi_note_class import MIDINote
import time


class DummyDataGenerator:
    def __init__(self, length=200, delay=0.25):
        self.length = length
        self.current_index = 0
        self.delay = delay  # Delay in seconds between frame updates
        self.last_update_time = time.time()
        # Initialize the first frame
        self.current_frame = [1023] * self.length
        self.current_frame[self.current_index] = 0

    def get_next_frame(self):
        # Check if enough time has passed to update the frame
        current_time = time.time()
        if current_time - self.last_update_time >= self.delay:
            # Update the last update time
            self.last_update_time = current_time

            # Generate a new frame with all values set to 1023
            self.current_frame = [1023] * self.length
            # Set only the current index value to 0
            self.current_frame[self.current_index] = 0
            # Move to the next index, wrapping around
            self.current_index = (self.current_index + 1) % self.length

        # Always return the most recent frame
        return self.current_frame


class BlobToMIDIConverter:
    def __init__(self):
        # Initialize the MIDI note grid
        self.note_grid = MIDINoteGrid()

        # Track active notes by blob ID
        self.active_notes = {}

        # Track active cells (row, col) for each blob ID
        self.active_cells = {}

    def process_blob(self, blob_id, position, size):
        """Processes each blob's position within the note grid and plays MIDI notes accordingly."""
        row, col = self.get_grid_position(position)

        # Check if the blob is within the grid bounds
        if row is not None and col is not None:
            midi_note = self.note_grid.get_note_at_position(row, col)
            if blob_id not in self.active_notes or self.active_notes[blob_id].midi_note != midi_note:
                # If blob is in a new note cell, update the MIDI note for the blob
                self.play_note_for_blob(blob_id, midi_note, size)
                # Update the active cell for visual feedback
                self.active_cells[blob_id] = (row, col)
            else:
                # Apply vibrato if blob stays in the same cell
                self.apply_vibrato_to_blob(blob_id, position)
        else:
            # Remove note if blob is outside grid
            self.remove_blob(blob_id)

    def get_grid_position(self, position):
        """Returns the row and column in the note grid for a given blob position."""
        x, y = position
        rows, cols = 6, 13  # MIDI grid dimensions
        row = int(y / (390 / rows))  # Adjust based on display dimensions
        col = int(x / (780 / cols))  # Adjust based on display dimensions

        if 0 <= row < rows and 0 <= col < cols:
            return row, col
        else:
            return None, None

    def play_note_for_blob(self, blob_id, midi_note, size):
        """Assigns a MIDI note to a blob based on its grid position and size (velocity)."""

        # Cyclically assign MIDI channels
        midi_channel = blob_id % 16

        # Scale blob size to MIDI velocity range
        velocity = min(127, max(0, int(size / 10)))

        # Convert MIDI note number to note name
        note_name = self.note_grid.midi_to_note_name(midi_note)

        midi_note_obj = MIDINote(midi_channel, midi_note, velocity)

        self.active_notes[blob_id] = midi_note_obj

        print(f"Playing note {note_name} on channel {
              midi_channel} with velocity {velocity}")

    def apply_vibrato_to_blob(self, blob_id, position):
        """Applies vibrato effect if the blob is within the same note grid block."""
        if blob_id in self.active_notes:
            midi_note = self.active_notes[blob_id]
            row, col = self.get_grid_position(position)
            vibrato_amount = self.calculate_vibrato(position, row, col)
            midi_note.set_vibrato(vibrato_amount)
            # print(f"Applying vibrato {vibrato_amount} to blob {
            #       blob_id} on note {midi_note.midi_note}")

    def remove_blob(self, blob_id):
        """Stops the MIDI note assigned to a blob when it leaves the grid."""
        if blob_id in self.active_notes:
            print(f"Stopping note for blob {blob_id}")
            del self.active_notes[blob_id]
            # Remove the active cell for visual feedback
            if blob_id in self.active_cells:
                del self.active_cells[blob_id]

    def calculate_vibrato(self, position, row, col):
        """Calculate vibrato amount based on position within a grid cell."""
        cell_width = 780 / 13
        cell_height = 390 / 6
        x, y = position
        dx = abs((col + 0.5) * cell_width - x)  # Distance from center
        dy = abs((row + 0.5) * cell_height - y)
        return min(127, int((dx + dy) / 10))  # Scale vibrato for MIDI CC


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
        np.uint8), (780, 390), interpolation=cv2.INTER_LANCZOS4)

    # Define yellow color for border in BGR format
    padding_color = (255)

    # Add padding to the resized image
    padded_image = cv2.copyMakeBorder(
        # Padded border
        resized_image, padding_offset, padding_offset, padding_offset, padding_offset, cv2.BORDER_CONSTANT, value=padding_color)

    # # Print for debugging
    # print(f"Padding: {padding_offset}, Border Color: {padding_color}")

    return resized_image, padded_image


def initialize_blob_detector():

    # Initialize blob detector with parameters
    params = cv2.SimpleBlobDetector_Params()

    '''Thresholding'''

    params.minThreshold = cv2.getTrackbarPos("Thresh Min", "Sensor Matrix")
    params.maxThreshold = cv2.getTrackbarPos("Thresh Max", "Sensor Matrix")

    '''------------------------------------------------------------------------'''

    '''Filter by Area'''

    params.filterByArea = False

    params.minArea = cv2.getTrackbarPos("Area Min", "Sensor Matrix")
    params.maxArea = cv2.getTrackbarPos("Area Max", "Sensor Matrix")

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
    # cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("Thresh Min", "Sensor Matrix", 10, 20, nothing)
    cv2.createTrackbar("Thresh Max", "Sensor Matrix", 255, 255, nothing)
    cv2.createTrackbar("Area Min", "Sensor Matrix", 15, 1000, nothing)
    cv2.createTrackbar("Area Max", "Sensor Matrix", 500, 5000, nothing)


def overlay_note_grid(display_img, note_grid, padding_offet, active_cells):
    # Calculate effective dimensions of the note grid
    effective_width = display_img.shape[1] - (2 * padding_offset)
    effective_height = display_img.shape[0] - (2 * padding_offset)

    # Determine the number of rows and columns in the note grid
    rows, cols = len(note_grid.grid), len(note_grid.grid[0])

    # Calculate cell width and height based on the effective grid size
    cell_width = effective_width // cols
    cell_height = effective_height // rows

    # Loop through each cell in the grid and add note text
    for row in range(rows):
        for col in range(cols):

            # Check if the current cell is active
            is_active = any(cell == (row, col)
                            for cell in active_cells.values())

            # Define color based on whether cell is active
            cell_color = (0, 255, 0) if is_active else (200, 200, 200)

            # Get the MIDI note number at the position
            note_number = note_grid.get_note_at_position(row, col)
            # Convert the MIDI note number to the note name
            note_name = note_grid.midi_to_note_name(
                note_number, include_octave=True)

            x = padding_offset + (col * cell_width)
            y = padding_offset + (row * cell_height)

            # Draw a rectangle for each cell, filled if active
            cv2.rectangle(display_img, (x, y), (x + cell_width,
                          y + cell_height), cell_color, -1 if is_active else 1)

            # Put the note name at the center of each cell
            cv2.putText(display_img, note_name, (x + cell_width // 4, y + cell_height // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    return display_img


# Define a set of predefined colors
colors = [
    (95, 89, 255),      # Coral Red (FF595F)
    (57, 202, 255),     # Golden Yellow (FFCA39)
    (39, 201, 138),     # Lime Green (8AC927)
    (196, 130, 26),     # Azure Blue (1A82C4)
    (147, 76, 106),     # Royal Purple (6A4C93)
    (77, 146, 255),     # Peach Orange (FF924D)
    (117, 166, 83),     # Forest Green (53A675)
    (220, 218, 168),    # Pale Aqua (A8DADC)
    (49, 202, 197),     # Chartreuse (C5CA31)
    (172, 103, 66),     # Steel Blue (4267AC)
    (121, 83, 181),     # Magenta Pink (B55379)
    (145, 110, 140),    # Mauve (8C6E91)
    (103, 139, 182),    # Taupe (B68B67)
    (249, 237, 250),    # Blush Pink (FAEDF9)
    (87, 53, 30),       # Deep Navy (1E3557)
    (167, 184, 219)     # Sand Beige (DBB8A7)
]


if __name__ == '__main__':
    # Serial port setup
    comport = '/dev/cu.usbmodem126032001'
    baudrate = 115200
    ports = serial.tools.list_ports.comports()
    available_ports = [port.device for port in ports]

    # Check if the desired port is available
    if comport in available_ports:
        ser = serial.Serial(comport, baudrate, timeout=0.1)
        use_dummy_data = False
        print(f"Connected to {comport}")
    else:
        use_dummy_data = True
        dummy_generator = DummyDataGenerator()
        print("Device not connected. Using dummy data.")

    # Initialize OpenCV window and blob detector
    cv2.namedWindow("Sensor Matrix", cv2.WINDOW_NORMAL)
    create_trackbars()  # Create trackbars for on-screen controls
    detector = initialize_blob_detector()

    # Toggle view states

    # Toggle for displaying blobs
    show_blobs = True

    # Toggle for displaying the black-and-white thresholded image
    show_threshold = 0
    # 0: thresholded view, 1: raw view, 2: white canvas

    # Toggle for displaying the note grid
    show_note_grid = True

    # Padding offset for edge blobs
    padding_offset = 30  # This hack works for now, but make it 30 or higher for border padding; but incorporate scaling into the program

    # Original display dimensions
    original_width, original_height = 600, 300
    # Effective dimensions after padding
    effective_width = original_width - (2 * padding_offset)
    effective_height = original_height - (2 * padding_offset)

    # Create the note grid
    note_grid = MIDINoteGrid()
    print(note_grid)

    # Initialize blob detector and MIDI note grid converter
    converter = BlobToMIDIConverter()

    while True:

        # Read current trackbar positions for threshold and area parameters
        threshold_min = cv2.getTrackbarPos("Thresh Min", "Sensor Matrix")
        threshold_max = cv2.getTrackbarPos("Thresh Max", "Sensor Matrix")
        area_min = cv2.getTrackbarPos("Area Min", "Sensor Matrix")
        area_max = cv2.getTrackbarPos("Area Max", "Sensor Matrix")

        # Update blob detector parameters
        detector = initialize_blob_detector()

        # If the port isn't connected, generate sensor data
        if use_dummy_data:
            # Get the next frame from the dummy data generator
            sensor_data = dummy_generator.get_next_frame()
        else:
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
        original_img, padded_img = generate_image(sensor_data)

        # Apply inverted thresholding to keep darker areas as blobs
        thresholded_img = apply_threshold_and_invert(
            padded_img, min_val=threshold_min, max_val=threshold_max)

        # Initialize the display base as a white background
        display_img = np.full_like(thresholded_img, 255)
        display_img = cv2.cvtColor(original_img, cv2.COLOR_GRAY2BGR)

        # Perform blob detection on the image
        keypoints = detector.detect(
            thresholded_img if show_threshold == 0 else padded_img)

        # Show thresholded image if enabled
        if show_threshold == 0:
            display_img = np.full_like(padded_img, 255)
            display_img = cv2.cvtColor(display_img, cv2.COLOR_GRAY2BGR)
        if show_threshold == 1:
            display_img = cv2.cvtColor(
                thresholded_img.copy(), cv2.COLOR_GRAY2BGR)
        if show_threshold == 2:
            # Use the original padded image directly
            display_img = cv2.cvtColor(padded_img, cv2.COLOR_GRAY2BGR)

        # Show blobs if enabled
        if show_blobs:
            # Convert to color to draw in color
            blob_image = cv2.cvtColor(thresholded_img, cv2.COLOR_GRAY2BGR)

            for i, keypoint in enumerate(keypoints):
                x = int((keypoint.pt[0]))
                # Scaling: int((keypoint.pt[1] - padding_offset) * effective_width / original_width)
                y = int((keypoint.pt[1]))
                size = int(keypoint.size)  # Scale size as well

                # Process the blob for MIDI playback
                converter.process_blob(i, (x, y), size)

                # Assign a unique color to each blob based on its index
                color = colors[i % len(colors)]

                # Draw the blob as a filled circle
                # Fill the blob with a solid color
                cv2.circle(display_img, (x, y), size // 2, color, -1)

                # Draw a crosshair at the center of the blob
                crosshair_size = 7
                cv2.line(display_img, (x - crosshair_size, y), (x + crosshair_size, y),
                         (0, 0, 0), 1)  # Horizontal line
                cv2.line(display_img, (x, y - crosshair_size), (x, y + crosshair_size),
                         (0, 0, 0), 1)  # Vertical line

                # Blob info text
                blob_info = f"ID: {i}, X: {x}, Y: {y}, Size: {size}"
                cv2.putText(display_img, blob_info, (x + 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        # Show note grid if enabled
        if show_note_grid:
            display_img = overlay_note_grid(
                display_img, converter.note_grid, padding_offset, converter.active_cells)

        # Display the image with blobs in the OpenCV window
        cv2.imshow("Sensor Matrix", display_img)

        # Wait for a key press and handle 'q', 't', and 'b'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break  # Quit the program
        elif key == ord('t'):
            show_threshold = (show_threshold + 1) % 3  # Toggle show_threshold
        elif key == ord('b'):
            show_blobs = not show_blobs  # Toggle show_blobs
        elif key == ord('n'):  # Toggle note grid display
            show_note_grid = not show_note_grid

    # Release resources
    cv2.destroyAllWindows()
