import numpy as np
import matplotlib.pyplot as plt

def select_pixels(image, N):
    # Display the image using matplotlib
    fig, ax = plt.subplots()
    ax.imshow(image)
    
    # Use the ginput function to allow the user to select N pixels
    pixels = plt.ginput(N, timeout=-1)
    
    # Close the plot window
    plt.close()
    
    # Return the pixel coordinates
    return pixels

def extract_mean_val(pixels, data, radius):
    thermal_curve_list = []
    for (x, y) in pixels:
        x_coor = int(x)
        y_coor = int(y)
        thermal_curve = data[:, y_coor-radius:y_coor+radius, x_coor-radius:x_coor+radius]
        thermal_curve = np.squeeze(np.mean(thermal_curve, axis=(1, 2)))
        thermal_curve_list.append((x_coor, y_coor, thermal_curve))
    return thermal_curve_list

def plot_thermal_curves(thermal_curve_list, order_dict):
    for i, (x, y, curve) in enumerate(thermal_curve_list):
        point_type = order_dict.get(i, f'point{i}')  # use a default string if no key found
        point_label = f'{point_type} ({x}, {y})'
        plt.plot(curve, label=point_label)

    plt.xlabel('Time')
    plt.ylabel('Mean Temperature')
    plt.legend()
    plt.show()

# assume selection order: bud, top, and bottom woody
order_dict = {
    0: 'good 1',
    1: 'good 2',
    2: 'good 3',
    3: 'good 4',
    4: 'good 5',
    5: 'bad 1',
    6: 'bad 2',
    7: 'bad 3',
    8: 'bad 4',
    9: 'bad 5'
}

# load data
data_filepath = './SavedData/heatcool.npy'
ti_cube = np.load(data_filepath)
disp_frame = np.squeeze(ti_cube[100,:,:])

# select pixels for thermal curve extraction
num_selected_points = 10
selected_points = select_pixels(disp_frame, num_selected_points)
extraction_region_radius = 5
thermal_curve_list = extract_mean_val(selected_points, ti_cube, extraction_region_radius)

# plot thermal curves
plot_thermal_curves(thermal_curve_list, order_dict)