import numpy as np
import matplotlib.pyplot as plt


def select_pixels(image):
    # Display the image using matplotlib
    fig, ax = plt.subplots()
    ax.imshow(image)
    plt.title("Select points on the image (Press 'q' to finish selection)")

    points = []

    def onclick(event):
        # Exit if 'q' is pressed
        if plt.get_current_fig_manager().toolbar.mode == '':
            if event.key == 'q':
                plt.close(fig)
            elif event.xdata is not None and event.ydata is not None:
                # Record the point and display it
                points.append((event.xdata, event.ydata))
                ax.plot(event.xdata, event.ydata, 'ro')
                fig.canvas.draw()

    # Connect the click event to the onclick function
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    key_cid = fig.canvas.mpl_connect('key_press_event', onclick)

    # Show the plot and wait for the user to finish selecting points
    plt.show()

    # Disconnect the event handlers
    fig.canvas.mpl_disconnect(cid)
    fig.canvas.mpl_disconnect(key_cid)

    return points


def extract_mean_val(pixels, data, radius):
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

def plot_thermal_curves(mean_curves, std_curves):
    time_points = np.arange(len(mean_curves[0]))
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))

    # Plotting mean curves
    for i, curve in enumerate(mean_curves):
        label = f"{i+1}st selected point" if i == 0 else f"{i+1}th selected point"
        axes[0].plot(time_points, curve, label=label)
    axes[0].set_ylabel('Average Temperature')
    axes[0].set_title('Mean Temperature over Time')
    axes[0].legend()

    # Plotting standard deviation curves
    for i, curve in enumerate(std_curves):
        label = f"{i+1}st selected point" if i == 0 else f"{i+1}th selected point"
        axes[1].plot(time_points, curve, label=label)
    axes[1].set_ylabel('Standard Deviation')
    axes[1].set_xlabel('Time')
    axes[1].set_title('Standard Deviation over Time')
    axes[1].legend()

    plt.tight_layout()
    plt.show()

def find_top_std_pixels(data, top_n=5):
    # Calculate the standard deviation for each pixel over time
    std_dev = np.std(data, axis=0)

    # Flatten the std_dev array and get the indices of the top N std deviations
    flat_std_dev = std_dev.flatten()
    indices = np.argpartition(flat_std_dev, -top_n)[-top_n:]

    # Convert flat indices to 2D indices
    x_coords, y_coords = np.unravel_index(indices, std_dev.shape)

    return list(zip(x_coords, y_coords))

def plot_initial_frame_with_points(frame, points):
    fig, ax = plt.subplots()
    ax.imshow(frame)
    for x, y in points:
        ax.plot(y, x, 'ro', markersize=1)  # y, x because matplotlib plots with y-axis as rows and x-axis as columns
    plt.title("Top 5 points with highest standard deviation")
    plt.show()


def main():
    # Load data
    data_filepath = '../../../../../test_data/Ries_B28_N05.npy'
    data = np.load(data_filepath)
    disp_frame = np.squeeze(data[100,:,:])

    # Find top 5 pixels with highest standard deviation and plot them
    top_pixels = find_top_std_pixels(data, 5000)
    plot_initial_frame_with_points(disp_frame, top_pixels)

    # Select pixels
    pixels = select_pixels(disp_frame)
    extraction_region_radius = 5

    # Extract mean and standard deviation values
    mean_curves, std_curves = extract_mean_val(pixels, data, extraction_region_radius)

    # Plot thermal curves
    plot_thermal_curves(mean_curves, std_curves)

if __name__ == "__main__":
    main()