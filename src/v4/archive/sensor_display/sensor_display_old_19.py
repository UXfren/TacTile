import numpy as np
import cv2
import serial.tools.list_ports
import random
from midi_note_grid_complex import MIDINoteGrid
from midi_note_class import MIDINote
import time
import mido


class DummyDataGenerator:
    def __init__(self, length=200, delay=0.1):
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


class AdvancedDummyDataGenerator:
    def __init__(self, length=200, delay=0.1):
        self.length = length
        self.delay = delay  # Delay in seconds between frame updates
        self.last_update_time = time.time()
        self.current_frame = [1023] * self.length
        self.constant_index = int(
            self.length * (2 / 3))  # Top-left 1/3rd index
        # Bottom-right 1/3rd index
        self.flashing_index = int(self.length * (1 / 3))
        self.flash_count = 0
        self.flash_limit = 5
        self.flashing_active = True

    def get_next_frame(self):
        current_time = time.time()
        if current_time - self.last_update_time >= self.delay:
            self.last_update_time = current_time

            # Reset all values to 1023
            self.current_frame = [1023] * self.length
            # Set the constant zero value
            self.current_frame[self.constant_index] = 0

            # Handle flashing zero value
            if self.flashing_active:
                self.current_frame[self.flashing_index] = 0
            self.flash_count += 1

            # Switch constant and flashing positions after reaching flash limit
            if self.flash_count >= self.flash_limit:
                # Swap the constant and flashing indices
                self.constant_index, self.flashing_index = self.flashing_index, self.constant_index
                self.flash_count = 0  # Reset flash counter
                self.flashing_active = not self.flashing_active

        return self.current_frame


class PersistentBlobTracker:
    # adjust distance_threshold as needed by testing with interface; maybe use cell_width and cell_height or cell_width/2?
    def __init__(self, distance_threshold=85):
        self.blob_positions = {}  # Store blob positions by ID
        self.distance_threshold = distance_threshold  # Max distance for matching blobs
        self.next_id = 0  # Counter for generating new IDs
        self.freed_ids = []  # Store IDs from disappeared blobs for reuse

    def update_blobs(self, keypoints):
        """Update blob IDs based on proximity matching."""
        new_positions = {}

        for keypoint in keypoints:
            x, y = int(keypoint.pt[0]), int(keypoint.pt[1])
            size = int(keypoint.size)
            position = (x, y)

            # Find closest existing blob within the distance threshold
            closest_id, min_distance = None, float('inf')
            for blob_id, (prev_position, _) in self.blob_positions.items():
                distance = np.linalg.norm(
                    np.array(position) - np.array(prev_position))
                if distance < min_distance and distance < self.distance_threshold:
                    closest_id, min_distance = blob_id, distance

            # If a close match is found, update the position of the existing blob
            if closest_id is not None:
                new_positions[closest_id] = (position, size)
            else:
                # Assign a new or recycled ID to the unmatched blob
                new_id = self._get_new_id()
                new_positions[new_id] = (position, size)

        # Collect IDs of blobs that weren't matched in this frame to free up those IDs
        for blob_id in set(self.blob_positions) - set(new_positions):
            # print(f"Blob {blob_id} disappeared.")
            self.freed_ids.append(blob_id)

        # Update blob positions for the next frame
        self.blob_positions = new_positions

        return self.blob_positions

    def _get_new_id(self):
        """Get a new or recycled ID for a blob."""
        if self.freed_ids:
            # Reuse the lowest available ID from freed IDs
            return self.freed_ids.pop(0)
        else:
            # Assign the next new ID
            self.next_id += 1
            return self.next_id

    def get_blob_color(self, blob_id):
        """Get a persistent color for each blob ID."""
        return colors[blob_id % len(colors)]


class BlobToMIDIConverter:
    def __init__(self, note_grid, midi_port):
        """
        Initialize the BlobToMIDIConverter with a note grid and MIDI output port.
        :param note_grid: Instance of MIDINoteGrid that represents the note grid.
        :param midi_port: MIDI output port for sending MIDI messages.
        """
        self.note_grid = note_grid
        self.midi_port = midi_port
        self.active_notes = {}  # Dictionary to keep track of active notes by blob ID

    def process_blobs(self, blob_positions):
        """
        Process blobs and handle MIDI note triggering based on their presence in the note grid.
        :param blob_positions: Dictionary with blob IDs as keys and positions as values.
        """
        # Iterate over each blob's position and size
        for blob_id, (position, size) in blob_positions.items():

            x, y = position

            # the calculation below is makeshift and SUCKS but works for now; make it better
            grid_x = (x * effective_width //
                      window_width) + (padding_offset * (effective_width // window_width) + (padding_offset//2) - 5)
            grid_y = (y *
                      effective_height // window_height) + (padding_offset * (effective_width // window_width) + (padding_offset//2) - 5)

            row, col = self._get_grid_position(grid_x, grid_y)

            if row is not None and col is not None:
                midi_note = self.note_grid.get_note_at_position(row, col)
                note_name = self.note_grid.midi_to_note_name(
                    midi_note)  # Get note name

                # Calculate velocity as twice the blob size, clamped to 1–127
                velocity = max(1, min(127, int(size * 2)))

                # Check if this blob is already active on this note
                if blob_id not in self.active_notes:
                    # Create and send a MIDI note on message
                    note = MIDINote(midi_channel=blob_id %
                                    16, midi_note=midi_note, velocity=velocity)
                    note.open_midi_port(self.midi_port)
                    note.send_note_on()
                    self.active_notes[blob_id] = {
                        "note": note, "start_col": col}
                    print(f"Blob {blob_id} started note {
                          note_name} with velocity {velocity}")

                else:
                    # Apply pitch bend based on blob position
                    note_data = self.active_notes[blob_id]
                    start_col = note_data["start_col"]
                    pitch_bend = self._calculate_pitch_bend(
                        grid_x, grid_y, row, col, start_col)
                    if note_data["note"].output_port:
                        note_data["note"].output_port.send(
                            mido.Message(
                                'pitchwheel', channel=0, pitch=pitch_bend)
                        )
                        print(f"\nBlob {blob_id}: Applied Pitch Bend {
                              pitch_bend}")

        # Check for any blobs that have disappeared and stop their notes
        self._stop_disappeared_blobs(blob_positions)

    def _calculate_pitch_bend(self, grid_x, grid_y, row, col, start_col, pitch_bend_range=12):
        """Calculate the pitch bend value based on blob position in the grid block."""
        # Determine the cell width and height
        cell_width = effective_width // self.note_grid.columns
        cell_height = effective_height // len(self.note_grid.grid)

        # Calculate the blob's relative position within the block (0 to 1 range)
        # Horizontal position within block
        rel_x = (grid_x % cell_width) / cell_width
        # Vertical position within block
        rel_y = (grid_y % cell_height) / cell_height

        # rel_x = 40-8+1-(grid_x % cell_width)
        # rel_y = (grid_y % cell_height)

        if col == start_col:
            # Manual Vibrato: Map rel_x to ± pitch_bend_range
            pitch_bend_per_semitone = 8192 // pitch_bend_range
            pitch_bend = int((rel_x - 0.5) * 2 * pitch_bend_per_semitone)

            print(f"Manual Vibrato: rel_x={
                  rel_x:.2f}, pitch_bend={pitch_bend}")
        else:
            # Note Bend: Calculate based on horizontal movement to a new block
            note_diff = col - start_col
            pitch_bend_per_semitone = 8192 // pitch_bend_range
            pitch_bend = note_diff * pitch_bend_per_semitone

            print(f"Note Bend: col={col}, start_col={start_col}, note_diff={
                note_diff}, pitch_bend={pitch_bend}")

        # Clamp the pitch bend value to the valid range
        pitch_bend = max(-8192, min(8191, pitch_bend))

        # Debugging output
        print(f"Grid X: {grid_x}, Grid Y: {grid_y}")
        print(f"Relative X: {rel_x:.2f}, Relative Y: {rel_y:.2f}")
        print(f"Calculated Pitch Bend: {pitch_bend}")

        return pitch_bend

    def _get_grid_position(self, grid_x, grid_y):
        """Calculate the row and column in the note grid based on adjusted grid coordinates."""
        cell_width = effective_width // self.note_grid.columns
        cell_height = effective_height // len(self.note_grid.grid)

        col = grid_x // cell_width
        row = grid_y // cell_height

        if 0 <= row < len(self.note_grid.grid) and 0 <= col < self.note_grid.columns:
            return row, col
        return None, None

    def _stop_disappeared_blobs(self, blob_positions):
        """
        Stop and clear notes for blobs that have disappeared.
        :param blob_positions: Current frame's blob positions.
        """
        # Find blob IDs that were active but are no longer present
        disappeared_blobs = set(self.active_notes.keys()) - \
            set(blob_positions.keys())

        for blob_id in disappeared_blobs:
            note_data = self.active_notes.pop(
                blob_id)  # Get the dict for the blob
            note = note_data["note"]  # Extract the MIDINote object
            note_name = self.note_grid.midi_to_note_name(
                note.midi_note)  # Get note name

            # Send a MIDI note-off message
            if note.output_port:
                note.output_port.send(mido.Message(
                    'note_off', channel=note.midi_channel, note=note.midi_note))
                print(f"Blob {blob_id} stopped note {note_name}")

            # Clear the note grid block color here (customize as needed)

    def _get_grid_position(self, x, y):
        """
        Convert x, y coordinates to the row and column in the note grid.
        :param x: x-coordinate of the blob.
        :param y: y-coordinate of the blob.
        :return: Tuple of (row, col) corresponding to the note grid position.
        """
        # Calculate row and column based on the grid's dimensions and padding offset
        effective_width = original_width - (2 * padding_offset)
        effective_height = original_height - (2 * padding_offset)

        cell_width = effective_width // self.note_grid.columns
        cell_height = effective_height // len(self.note_grid.grid)

        # Map the blob’s coordinates to the grid dimensions
        # Ensure x and y are adjusted for padding offset, then scale by cell size
        col = (x - padding_offset) * self.note_grid.columns // effective_width
        row = (y - padding_offset) * \
            len(self.note_grid.grid) // effective_height

        if 0 <= row < len(self.note_grid.grid) and 0 <= col < self.note_grid.columns:
            return row, col
        return None, None

    def stop_all_notes(self):
        """Stops all active notes by sending note_off messages."""
        for blob_id, note in list(self.active_notes.items()):
            if note.output_port:
                note.output_port.send(mido.Message(
                    'note_off', channel=note.midi_channel, note=note.midi_note))
            # Remove the note from active notes after stopping it
            self.active_notes.pop(blob_id)
        print("\n\nAll active notes stopped.")


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


def overlay_note_grid(display_img, note_grid, padding_offet, active_notes, alpha=0.5):
    # Calculate effective dimensions of the note grid
    effective_width = display_img.shape[1] - (2 * padding_offset)
    effective_height = display_img.shape[0] - (2 * padding_offset)

    # Determine the number of rows and columns in the note grid
    rows, cols = len(note_grid.grid), len(note_grid.grid[0])

    # Create a temporary overlay for the grid
    overlay = display_img.copy()

    # Calculate cell width and height based on the effective grid size
    cell_width = effective_width // cols
    cell_height = effective_height // rows

    # print(f"\n\nCell Width: {cell_width},\t\tCell Height: {cell_height}\n\n")

    # Loop through each cell in the grid and add note text
    for row in range(rows):
        for col in range(cols):

            # Get the MIDI note number at the position
            note_number = note_grid.get_note_at_position(row, col)
            # Convert the MIDI note number to the note name
            note_name = note_grid.midi_to_note_name(
                note_number, include_octave=True)

            x = padding_offset + (col * cell_width)
            y = padding_offset + (row * cell_height)

            # Determine color based on whether the note is active
            if note_number in [note_data["note"].midi_note for note_data in active_notes.values()]:
                color = (0, 255, 0)  # Green for active notes
            else:
                color = (200, 200, 200)  # Gray for inactive notes

            # Draw the cell on the overlay
            cv2.rectangle(overlay, (x, y), (x + cell_width,
                          y + cell_height), color, -1)
            cv2.rectangle(overlay, (x, y), (x + cell_width,
                          y + cell_height), (100, 100, 100), 1)
            cv2.putText(overlay, note_name, (x + cell_width // 4, y + cell_height // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # Blend the overlay with the original image using the alpha transparency factor
    cv2.addWeighted(overlay, alpha, display_img, 1 - alpha, 0, display_img)

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
        # ser = serial.Serial(comport, baudrate, timeout=0.1)
        use_dummy_data = False
        print(f"Connected to {comport}")
    else:
        use_dummy_data = True
        dummy_generator = DummyDataGenerator()
        advanced_dummy_generator = AdvancedDummyDataGenerator()
        use_advanced_dummy = False
        print(f"\n\nDevice not connected. Using dummy data.")

    # Initialize blob tracker
    blob_tracker = PersistentBlobTracker()

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

    # Define MIDI port name and initialize BlobToMIDIConverter
    midi_port_name = "IAC Driver TacTile"  # Adjust this as needed
    midi_converter = BlobToMIDIConverter(note_grid, midi_port_name)

    while True:

        # Read current trackbar positions for threshold and area parameters
        threshold_min = cv2.getTrackbarPos("Thresh Min", "Sensor Matrix")
        threshold_max = cv2.getTrackbarPos("Thresh Max", "Sensor Matrix")
        area_min = cv2.getTrackbarPos("Area Min", "Sensor Matrix")
        area_max = cv2.getTrackbarPos("Area Max", "Sensor Matrix")

        # Update blob detector parameters
        detector = initialize_blob_detector()

        # If the port isn't connected, generate sensor data
        # Check which generator to use
        if use_dummy_data:
            if use_advanced_dummy:
                sensor_data = advanced_dummy_generator.get_next_frame()
            else:
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

        # Get window dimensions
        window_height, window_width = display_img.shape[:2]

        # Perform blob detection on the image
        keypoints = detector.detect(thresholded_img)

        blob_positions = blob_tracker.update_blobs(keypoints)

        # Process blob positions for MIDI notes
        midi_converter.process_blobs(blob_positions)

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

        # Show note grid if enabled
        if show_note_grid:
            display_img = overlay_note_grid(
                display_img, note_grid, padding_offset, midi_converter.active_notes, alpha=0.5)

        # Show blobs if enabled
        if show_blobs:
            # Convert to color to draw in color
            blob_image = cv2.cvtColor(thresholded_img, cv2.COLOR_GRAY2BGR)

            for blob_id, (position, size) in blob_positions.items():
                x, y = position

                grid_x = (x * effective_width //
                          window_width) + (padding_offset * (effective_width // window_width) + (padding_offset//2) - 5)
                grid_y = (y *
                          effective_height // window_height) + (padding_offset * (effective_width // window_width) + (padding_offset//2) - 5)

                # size = int(keypoint.size)  # Scale size as well

                # Assign a unique color to each blob based on its index
                color = blob_tracker.get_blob_color(blob_id)

                # Draw the blob as a filled circle
                # Fill the blob with a solid color
                cv2.circle(display_img, (x, y), size // 2, color, -1)

                # Draw a crosshair at the center of the blob
                crosshair_size = 7
                cv2.line(display_img, (x - crosshair_size, y), (x + crosshair_size, y),
                         (0, 0, 0), 1)  # Horizontal line
                cv2.line(display_img, (x, y - crosshair_size), (x, y + crosshair_size),
                         (0, 0, 0), 1)  # Vertical line

                # crosshair to check blob's REAL position; doesn't really work as expected
                # cv2.line(display_img, (grid_x - crosshair_size, grid_y), (grid_x + crosshair_size, grid_y),
                #          (0, 0, 255), 1)  # Horizontal line
                # cv2.line(display_img, (grid_x, grid_y - crosshair_size), (grid_x, grid_y + crosshair_size),
                #          (0, 0, 255), 1)  # Vertical line

                # Blob info text
                blob_info = f"ID: {blob_id}, X: {
                    grid_x}, Y: {grid_y}, Size: {size}"
                cv2.putText(display_img, blob_info, (x + 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                # print(f"ID: {blob_id},\t\tX  : {x},\tY  : {y}")
                # print(f"ID: {blob_id},\t\tG_X: {grid_x},\t\tG_Y: {grid_y}\n\n")

        # Display the image with blobs in the OpenCV window
        cv2.imshow("Sensor Matrix", display_img)

        # Wait for a key press and handle 'q', 't', and 'b'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('t'):
            show_threshold = (show_threshold + 1) % 3  # Toggle show_threshold
        elif key == ord('b'):
            show_blobs = not show_blobs  # Toggle show_blobs
        elif key == ord('n'):  # Toggle note grid display
            show_note_grid = not show_note_grid
        elif key == ord('l'):
            # Toggle between regular and advanced dummy data generators
            use_advanced_dummy = not use_advanced_dummy
            print(
                "Switched to", "Advanced Dummy Data" if use_advanced_dummy else "Basic Dummy Data")

        # Key press handling for MIDI note grid controls
        elif key == ord('z'):       # Lower by one octave
            note_grid.transpose_octave('down')
        elif key == ord('x'):     # Raise by one octave
            note_grid.transpose_octave('up')
        elif key == ord('c'):     # Lower by one semitone
            note_grid.transpose_semitone('down')
        elif key == ord('v'):     # Raise by one semitone
            note_grid.transpose_semitone('up')
        elif key == ord('d'):     # Drop D tuning
            note_grid.set_drop_d_tuning()
        elif key == ord('f'):     # Perfect fourths tuning
            note_grid.set_perfect_fourths_tuning()
        elif key == ord('s'):     # Cycle through scale modes
            note_grid.cycle_scale_mode()
        elif key == ord('a'):     # Standard tuning as reference point
            note_grid.set_standard_tuning()
        # else:
        #     # Optional feedback for invalid keys
        #     print(
        #         "Invalid key. Use 'z', 'x', 'c', 'v', 'd', 'f', 's', 'a', or 'q' to quit.")

        # Panic button
        elif key == ord('p'):
            # Stop all notesq
            midi_converter.stop_all_notes()

        # Program ender
        elif key == ord('q'):
            # Stop all notes before exiting
            midi_converter.stop_all_notes()
            break  # Quit the program

    # Release resources
    cv2.destroyAllWindows()
