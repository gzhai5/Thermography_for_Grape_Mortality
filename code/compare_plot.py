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
    return [(mean_curves[:5]+mean_curves[11:16]+mean_curves[21:26], std_curves[:5]+std_curves[11:16]+std_curves[21:26]), (mean_curves[6:11]+mean_curves[16:21]+mean_curves[5:], std_curves[6:11]+std_curves[16:21]+std_curves[5:])]
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
    ax1.plot(np.mean(good_seed_mean, axis=0), label='Mean Good Seed 1-15')
    ax1.plot(np.mean(bad_seed_mean, axis=0), label='Mean Bad Seed 1-15')
    ax2.plot(np.mean(good_seed_std, axis=0), label='Std Good Seed 1-15')
    ax2.plot(np.mean(bad_seed_std, axis=0), label='Std Bad Seed 1-15')
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
    0: 'bad 1',
    1: 'bad 2',
    2: 'bad 3',
    3: 'bad 4',
    4: 'bad 5',
    5: 'good 1',
    6: 'good 2',
    7: 'good 3',
    8: 'good 4',
    9: 'good 5',
    10: 'bad 6',
    11: 'bad 7',
    12: 'bad 8',
    13: 'bad 9',
    14: 'bad 10',
    15: 'good 6',
    16: 'good 7',
    17: 'good 8',
    18: 'good 9',
    19: 'good 10',
    20: 'bad 11',
    21: 'bad 12',
    22: 'bad 13',
    23: 'bad 14',
    24: 'bad 15',
    25: 'good 11',
    26: 'good 12',
    27: 'good 13',
    28: 'good 14',
    29: 'good 15'
}

# load data
data_filepath = './SavedData/thirtySeed01.npy'
ti_cube = np.load(data_filepath)
disp_frame = np.squeeze(ti_cube[100,:,:])

# select pixels for thermal curve extraction
num_selected_points = 30
selected_points = select_pixels(disp_frame, num_selected_points)
extraction_region_radius = 5
thermal_curve_list = extract_mean_val(selected_points, ti_cube, extraction_region_radius)


# plot thermal curves
plot_thermal_curves(thermal_curve_list, order_dict)