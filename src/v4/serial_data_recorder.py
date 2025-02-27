import numpy as np
import cv2
import serial_reader
# import keyboard

# Configuration
comport = '/dev/cu.usbmodem126032001'
baudrate = 115200
frames = []
recording = False
max_frames = 900  # Define how many frames to save

# Start/Stop recording on 'p' key, quit on 'q' key


def main():
    global recording, frames

    print("Press 'r' to start/stop recording, 'q' to quit.")

    # Create an OpenCV window with a placeholder image to capture key events
    cv2.imshow("Sensor Matrix", np.zeros((100, 100), dtype=np.uint8))

    # Read from serial in a loop
    for sensor_data in serial_reader.read_serial(comport, baudrate):
        # Check if the 'q' key has been pressed to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Exiting...")
            break
        elif key == ord('r'):
            recording = not recording
            if recording:
                print("Recording started.")
            else:
                print("Recording stopped.")

        # Record frame if recording is active
        if recording:
            frames.append(sensor_data)
            print(f"Frame recorded: {len(frames)}")

            # Stop recording once max_frames is reached
            if len(frames) >= max_frames:
                print("Max frames reached. Recording stopped.")
                recording = False

    # Save frames to a file for looping later
    save_frames(frames)


def save_frames(frames, filename="recorded_frames.npy"):
    np.save(filename, frames)
    print(f"{len(frames)} frames saved to {filename}")


if __name__ == '__main__':
    main()
