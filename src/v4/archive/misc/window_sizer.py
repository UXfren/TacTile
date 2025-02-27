import cv2
import numpy as np

# Define the dimensions for the canvas, grey rectangle, and black square
border = 30
canvas_height, canvas_width = 390, 775
image_height, image_width = canvas_height - \
    (2 * border), canvas_width - (2 * border)
square_size = 30  # Size of the black square

# Create a white canvas and grey rectangle
canvas = np.ones((canvas_height, canvas_width), dtype=np.uint8) * 255
grey_image = np.ones((image_height, image_width), dtype=np.uint8) * 128

# Calculate the starting coordinates of the grey rectangle
start_y = (canvas_height - image_height) // 2
start_x = (canvas_width - image_width) // 2

# Initial square position in percentage (50% each way)
square_x_pct = 50
square_y_pct = 50
square_visible = 1  # Toggle to show/hide square

# Callback functions for the trackbars


def update_x(val):
    global square_x_pct
    square_x_pct = val
    update_canvas()


def update_y(val):
    global square_y_pct
    square_y_pct = val
    update_canvas()


def toggle_square(val):
    global square_visible
    square_visible = val
    update_canvas()

# Function to update the canvas display


def update_canvas():
    # Reset canvas
    display_canvas = canvas.copy()
    display_canvas[start_y:start_y + image_height,
                   start_x:start_x + image_width] = grey_image

    # Draw the 13 x 6 grid
    rows, cols = 6, 13
    cell_height = image_height // rows
    cell_width = image_width // cols

    for i in range(1, rows):
        y = start_y + i * cell_height
        cv2.line(display_canvas, (start_x, y),
                 (start_x + image_width, y), (0, 0, 0), 1)

    for j in range(1, cols):
        x = start_x + j * cell_width
        cv2.line(display_canvas, (x, start_y),
                 (x, start_y + image_height), (0, 0, 0), 1)

    if square_visible:
        # Calculate the absolute position of the square based on percentage
        square_x_abs = start_x + \
            int((square_x_pct / 100) * (image_width - square_size))
        square_y_abs = start_y + \
            int((square_y_pct / 100) * (image_height - square_size))

        # Draw the black square on the grey rectangle
        cv2.rectangle(display_canvas,
                      (square_x_abs, square_y_abs),
                      (square_x_abs + square_size, square_y_abs + square_size),
                      (0, 0, 0), -1)

        # Display position info on the canvas
        text_pct = f"Percentage: X={square_x_pct}%, Y={square_y_pct}%"
        text_abs = f"Position: X={square_x_abs}, Y={square_y_abs}"
        cv2.putText(display_canvas, text_pct, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(display_canvas, text_abs, (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Show the updated canvas
    cv2.imshow("Centered Grey Image with Controls", display_canvas)


# Set up the window and trackbars
cv2.namedWindow("Centered Grey Image with Controls")
cv2.createTrackbar(
    "X Position", "Centered Grey Image with Controls", square_x_pct, 100, update_x)
cv2.createTrackbar(
    "Y Position", "Centered Grey Image with Controls", square_y_pct, 100, update_y)
cv2.createTrackbar("Toggle Square", "Centered Grey Image with Controls",
                   square_visible, 1, toggle_square)

# Initial display
update_canvas()

# Close window on pressing ESC
while True:
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

cv2.destroyAllWindows()
