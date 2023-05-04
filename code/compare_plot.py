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
    mean_curves = []
    std_curves = []
    for (x, y) in pixels:
        x_coor = int(x)
        y_coor = int(y)
        thermal_curve = data[:, y_coor-radius:y_coor+radius, x_coor-radius:x_coor+radius]
        mean_curve = np.squeeze(np.mean(thermal_curve, axis=(1, 2)))
        std_curve = np.squeeze(np.std(thermal_curve, axis=(1, 2)))
        mean_curves.append(mean_curve)
        std_curves.append(std_curve)
    return [(mean_curves[:5], std_curves[:5]), (mean_curves[5:], std_curves[5:])]
    # thermal_curve_list = []
    # for (x, y) in pixels:
    #     x_coor = int(x)
    #     y_coor = int(y)
    #     thermal_curve = data[:, y_coor-radius:y_coor+radius, x_coor-radius:x_coor+radius]
    #     mean_curve = np.squeeze(np.mean(thermal_curve, axis=(1, 2)))
    #     std_curve = np.squeeze(np.std(thermal_curve, axis=(1, 2)))
    #     thermal_curve_list.append((x_coor, y_coor, mean_curve, std_curve))
    # return thermal_curve_list

def plot_thermal_curves(thermal_curve_list, order_dict):

    # plot two groups
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    good_seed_mean, good_seed_std = thermal_curve_list[0]
    bad_seed_mean, bad_seed_std = thermal_curve_list[1]
    ax1.plot(np.mean(good_seed_mean, axis=0), label='Mean Good Seed 1-5')
    ax1.plot(np.mean(bad_seed_mean, axis=0), label='Mean Bad Seed 1-5')
    ax2.plot(np.mean(good_seed_std, axis=0), label='Std Good Seed 1-5')
    ax2.plot(np.mean(bad_seed_std, axis=0), label='Std Bad Seed 1-5')
    ax1.set_ylabel('Mean Temperature')
    ax2.set_ylabel('Standard Deviation')
    ax2.set_xlabel('Time')
    ax1.legend()
    ax2.legend()
    plt.show()

    # # plot 10 curves
    # fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    # for i, (x, y, mean_curve, std_curve) in enumerate(thermal_curve_list):
    #     point_type = order_dict.get(i, f'point{i}')  # use a default string if no key found
    #     point_label = f'{point_type} ({x}, {y})'
    #     ax1.plot(mean_curve, label=point_label)
    #     ax2.plot(std_curve, label=point_label)
    # ax1.set_ylabel('Mean Temperature')
    # ax2.set_ylabel('Standard Deviation')
    # ax2.set_xlabel('Time')
    # ax1.legend()
    # ax2.legend()
    # plt.show()

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
data_filepath = './SavedData/badgood.npy'
ti_cube = np.load(data_filepath)
disp_frame = np.squeeze(ti_cube[100,:,:])

# select pixels for thermal curve extraction
num_selected_points = 10
selected_points = select_pixels(disp_frame, num_selected_points)
extraction_region_radius = 5
thermal_curve_list = extract_mean_val(selected_points, ti_cube, extraction_region_radius)


# plot thermal curves
plot_thermal_curves(thermal_curve_list, order_dict)