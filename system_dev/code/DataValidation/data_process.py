import numpy as np

def find_top_sensitive_pixels(data: np.ndarray, top_n: int, start_frame: int, end_frame: int, threshold: int) -> list:
    # Ensure the frame range is within the data bounds
    start_frame = max(0, start_frame)
    end_frame = min(data.shape[0], end_frame)

    mean_values = np.mean(data[start_frame:end_frame, :, :], axis=0)
    mask = mask_pixel_filter(mean_values, threshold)

    # Apply the mask and calculate the standard deviation for the masked pixels
    masked_data = data[start_frame:end_frame, :, :] * mask
    std_dev = np.std(masked_data, axis=0)

    # Flatten the std_dev array and get the indices of the top N std deviations
    flat_std_dev = std_dev.flatten()
    indices = np.argpartition(flat_std_dev, -top_n)[-top_n:]
    sorted_indices = indices[np.argsort(flat_std_dev[indices])][::-1]

    # Convert flat indices to 2D indices
    x_coords, y_coords = np.unravel_index(sorted_indices, std_dev.shape)
    return list(zip(x_coords, y_coords))

# two methods apply mask to the data
# 1. mask the pixels with mean < threshold
# 2. mask the pixels with only the center of whole image
def mask_pixel_filter(mean_values, threshold: int):
    mask = mean_values < threshold
    height, width = mean_values.shape
    mask[:int(height/3), :] = False
    mask[int(height*2/3):, :] = False
    mask[:, :int(width/3)] = False
    mask[:, int(width*2/3):] = False
    return mask

def extract_mean_val(pixels: list, data: np.ndarray, radius: int):
    mean_curves = []
    std_curves = []
    for (x, y) in pixels:
        x_coor = int(x)
        y_coor = int(y)
        region = data[:, max(y_coor-radius, 0):min(y_coor+radius, data.shape[1]),
                        max(x_coor-radius, 0):min(x_coor+radius, data.shape[2])]
        mean_curve = np.mean(region, axis=(1, 2))
        std_curve = np.std(region, axis=(1, 2))
        mean_curves.append(mean_curve)
        std_curves.append(std_curve)
    return mean_curves, std_curves


