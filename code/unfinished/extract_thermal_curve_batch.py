import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import os.path as osp

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
        thermal_curve = np.insert(thermal_curve, 0, y_coor) # add y coordinate 
        thermal_curve = np.insert(thermal_curve, 0, x_coor) # add x coordinate
        thermal_curve_list.append(thermal_curve)
    return thermal_curve_list

def display_ti_video(data):
    fig, ax = plt.subplots()
    for i in range(data.shape[0]):
        frame = np.squeeze(data[i,:,:])
        ax.imshow(frame)
        plt.pause(0.033)
        ax.cla()
    plt.close()

folder_dict = {'natural':r'E:\Grape_Thermal_Data\20230330', 'frozen':r'E:\Grape_Thermal_Data\20230404'}
num_selected_points = 3
frame_for_display = 180
extraction_region_radius = 5

ti_feature_names = ['{0}'.format(i) for i in np.arange(1, 481)]
column_names = ['treatment', 'cultivar', 'cane', 'node', 'pt_type', 'pt_pos', 'status'] + ti_feature_names

# assume selection order: bud, top, and bottom woody
order_dict = {
    0: 'bud',
    1: 'top',
    2: 'bottom'
}

# csv output file name
output_csvname = 'ti_curves.csv'

# create a pandas dataframe for data saving
df = pd.DataFrame(columns=column_names)

test_ind = 0

for (treatment, base_folder) in folder_dict.items():
    print('Start processing samples of {0} in {1}'.format(treatment, base_folder))
    data_files = os.listdir(base_folder)
    # print(data_files)
    for file_name in data_files:
        data_filepath = osp.join(base_folder, file_name)
        print('Processing {0}'.format(data_filepath))
        meta_info = file_name.split('_')
        cultivar = meta_info[0]
        cane_num = meta_info[1]
        node_num = meta_info[2]
        # load data
        ti_cube = np.load(data_filepath)
        disp_frame = np.squeeze(ti_cube[frame_for_display, : , :])
        # select pixels for thermal curve extraction
        selected_points = select_pixels(disp_frame, num_selected_points)
        
        thermal_curve_list = extract_mean_val(selected_points, ti_cube, extraction_region_radius)
        

        for i in range(num_selected_points):
            data_points = thermal_curve_list[i]
            ti_curve = data_points[2:].tolist()
            point_type = '{0}'.format(order_dict.get(i))
            point_loc = '{0}_{1}'.format(data_points[0], data_points[1])
            data_entry = [treatment,cultivar,cane_num,node_num,point_type, point_loc,''] + ti_curve
            df_entry = pd.DataFrame(data=[data_entry], columns=column_names)
            df = pd.concat([df_entry, df.loc[:]]).reset_index(drop=True)
        
        test_ind += 1

    #     if test_ind >= 4:
    #         break
    # if test_ind >= 4:
    #     break

df.to_csv(output_csvname)
print('Exported all the thermal curves into {0}'.format(output_csvname))        

