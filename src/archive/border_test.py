import numpy as np
import cv2

# Test with a blank image to confirm yellow border is correctly applied
test_image = np.zeros((100, 100), dtype=np.uint8)  # Small black square
yellow_bgr = (128)  # Yellow color

padded_test_image = cv2.copyMakeBorder(
    test_image, 30, 30, 30, 30,
    cv2.BORDER_CONSTANT, value=yellow_bgr
)

cv2.imshow("Yellow Border Test", padded_test_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
