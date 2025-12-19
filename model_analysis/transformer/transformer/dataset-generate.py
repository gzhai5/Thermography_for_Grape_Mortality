import av
import os
import wandb
from transformers import TrainingArguments
from transformers import Trainer, TrainingArguments, AdamW
from utils.model_configuration import *
from transformers import Trainer
from utils.preprocessing import create_dataset
from utils.data_handling import frames_convert_and_create_dataset_dictionary, read_video_pyav, sample_frame_indices
from utils.model_configuration import initialise_model
from datasets import load_from_disk

# vars to set
cultivar = 'RIES'
size = 21

val_video_dict, val_class_labels = frames_convert_and_create_dataset_dictionary(f'data-size-{size}/{cultivar}/val')
shuffled_val_dataset = create_dataset(val_video_dict)
train_video_dict, train_class_labels = frames_convert_and_create_dataset_dictionary(f'data-size-{size}/{cultivar}/train')
shuffled_train_dataset = create_dataset(train_video_dict)
test_video_dict, test_class_labels = frames_convert_and_create_dataset_dictionary(f'data-size-{size}/{cultivar}/test')
shuffled_test_dataset = create_dataset(test_video_dict)


# store datasets locally
shuffled_train_dataset.save_to_disk(f'dataset-{size}/{cultivar}/train')
shuffled_val_dataset.save_to_disk(f'dataset-{size}/{cultivar}/val')
shuffled_test_dataset.save_to_disk(f'dataset-{size}/{cultivar}/test')


try:
    frames = torch.tensor(shuffled_train_dataset[0]['pixel_values'])
    print(frames.dtype)
except:
    print('error')