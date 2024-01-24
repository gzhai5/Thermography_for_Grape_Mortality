import numpy as np
import os
import matplotlib.pyplot as plt


def select_pixel(image, file_name):
    # Display the image using matplotlib
    fig, ax = plt.subplots()
    ax.imshow(image)
    plt.title(f"Select a point on the image: {file_name} (Click and then press 'q' to confirm)")

    point = []

    def onclick(event):
        # Exit if 'q' is pressed
        if plt.get_current_fig_manager().toolbar.mode == '':
            if event.key == 'q':
                plt.close(fig)
            elif event.xdata is not None and event.ydata is not None and len(point) == 0:
                # Record the point and display it
                point.append((event.xdata, event.ydata))
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

    return point[0] if point else None


def extract_mean_val(point, data, radius):
    x, y = int(point[0]), int(point[1])
    region = data[:, max(y-radius, 0):min(y+radius, data.shape[1]),
                     max(x-radius, 0):min(x+radius, data.shape[2])]
    mean_curve = np.mean(region, axis=(1, 2))
    std_curve = np.std(region, axis=(1, 2))
    return mean_curve, std_curve

def plot_combined_curves(mean_curves, std_curves, split_index):
    time_points = np.arange(len(mean_curves[0]))
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))

    # Plotting mean curves
    for i, curve in enumerate(mean_curves):
        color = 'blue' if i < split_index else 'green'
        label = f"Data {i+1}"
        axes[0].plot(time_points, curve, label=label, color=color)
    axes[0].set_ylabel('Average Temperature')
    axes[0].set_title('Mean Temperature over Time')
    axes[0].legend()

    # Plotting standard deviation curves
    for i, curve in enumerate(std_curves):
        color = 'blue' if i < split_index else 'green'
        label = f"Data {i+1}"
        axes[1].plot(time_points, curve, label=label, color=color)
    axes[1].set_ylabel('Standard Deviation')
    axes[1].set_xlabel('Time')
    axes[1].set_title('Standard Deviation over Time')
    axes[1].legend()

    plt.tight_layout()
    plt.show()

def normalize_curves_using_min(curves):
    normalized_curves = []
    for curve in curves:
        min_val = np.min(curve)
        normalized_curve = curve - min_val
        normalized_curves.append(normalized_curve)
    return normalized_curves


def main():
    # Load data
    data_filepaths = [
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B01_N01.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B03_N06.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B04_N05.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B17_N07.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B22_N04.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B26_N05.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B29_N04.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B29_N06.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B14_N07.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B21_N08.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B08_N06.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con2.0_B25_N09.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con_2.1_F_B37_N06.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con_2.1_F_B35_N07.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con_2.1_F_B38_N03.npy',
                        '/Volumes/My Book Duo/Bud Thermography Data/Con_2.1_F_B44_N09.npy',
                    ]
    
    extraction_region_radius = 3
    mean_curves = []
    std_curves = []

    for filepath in data_filepaths:
        data = np.load(filepath)
        disp_frame = np.squeeze(data[100,:,:])

        # Extract the file name from the filepath for the title
        file_name = os.path.basename(filepath)
        pixel = select_pixel(disp_frame, file_name)
        
        if pixel:
            mean_curve, std_curve = extract_mean_val(pixel, data, extraction_region_radius)
            mean_curves.append(mean_curve)
            std_curves.append(std_curve)

    # Normalize the curves
    mean_curves = normalize_curves(mean_curves)
    std_curves = normalize_curves(std_curves)

    # Plot combined thermal curves
    plot_combined_curves(mean_curves, std_curves, split_index=8)

if __name__ == "__main__":
    main()