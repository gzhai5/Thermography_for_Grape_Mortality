import numpy as np
import imageio

def npy_to_mp4(npy_file, output_file, fps=24):
    # Load NPY file
    npy_data = np.load(npy_file)

    # Get dimensions from the NPY data
    frames, height, width = npy_data.shape

    # Create an empty list to store frames
    frame_list = []

    # Convert NPY frames to RGB images
    for i in range(frames):
        # Normalize the frame data to 0-255 range
        frame = (255 * (npy_data[i] - npy_data.min()) / (npy_data.max() - npy_data.min())).astype(np.uint8)
        # Convert grayscale frame to RGB
        frame = np.stack((frame,) * 3, axis=-1)
        # Append frame to the list
        frame_list.append(frame)

    # Write frames to MP4 video file using imageio
    imageio.mimwrite(output_file, frame_list, fps=fps)

# Example usage
npy_file_path = 'path/to/input.npy'
output_file_path = 'path/to/output.mp4'
npy_to_mp4(npy_file_path, output_file_path)
