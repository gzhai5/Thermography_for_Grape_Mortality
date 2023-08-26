import numpy as np
import imageio
import matplotlib.cm as cm

def npy_to_mp4(npy_file, output_file, fps=24):
    # Load NPY file
    npy_data = np.load(npy_file)

    # Get dimensions from the NPY data
    frames, height, width = npy_data.shape
    print(frames)

    # Create an empty list to store frames
    frame_list = []

    # Convert NPY frames to RGB images
    for i in range(frames):
        # Normalize the frame data to 0-255 range
        frame = (npy_data[i] - npy_data.min()) / (npy_data.max() - npy_data.min())

        # frame = (255*frame).astype(np.uint8)
        # frame = np.stack((frame,) * 3, axis=-1)
        # frame_list.append(frame)

        # Convert grayscale frame to RGB
        colored_frame = cm.hot(frame)[:, :, :3]
        colored_frame = (255 * colored_frame).astype(np.uint8)
        # Append frame to the list
        frame_list.append(colored_frame)

    # Write frames to MP4 video file using imageio
    imageio.mimwrite(output_file, frame_list, fps=fps)

# Example usage
npy_file_path = './CW_C3_B3.npy'
output_file_path = 'c3b3.mp4'
npy_to_mp4(npy_file_path, output_file_path)
