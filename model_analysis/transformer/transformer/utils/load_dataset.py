from utils.video_disk_dataset import VideoDiskDataset, reshuffle_dataset
from torch.utils.data import ConcatDataset



def load_data(cultivar: str):
    if cultivar == "RIES":
        train_dataset_ries = VideoDiskDataset(f'../refined_data_21/RIES/frame-60/train/metadata.json')
        train_dataset_ries.shuffle(random_state=42)
        val_dataset_ries = VideoDiskDataset(f'../refined_data_21/RIES/frame-60/valid/metadata.json')
        test_dataset_ries = VideoDiskDataset(f'../refined_data_21/RIES/frame-60/test/metadata.json')
        return train_dataset_ries, val_dataset_ries, test_dataset_ries
    elif cultivar == "CF":
        train_dataset_cf = VideoDiskDataset(f'../refined_data_21/CF/frame-60/train/metadata.json')
        train_dataset_cf.shuffle(random_state=42)
        val_dataset_cf = VideoDiskDataset(f'../refined_data_21/CF/frame-60/valid/metadata.json')
        test_dataset_cf = VideoDiskDataset(f'../refined_data_21/CF/frame-60/test/metadata.json')
        return train_dataset_cf, val_dataset_cf, test_dataset_cf
    elif cultivar == "CON":
        train_dataset_con = VideoDiskDataset(f'../refined_data_21/CON/frame-60/train/metadata.json')
        train_dataset_con.shuffle(random_state=42)
        val_dataset_con = VideoDiskDataset(f'../refined_data_21/CON/frame-60/valid/metadata.json')
        test_dataset_con = VideoDiskDataset(f'../refined_data_21/CON/frame-60/test/metadata.json')
        return train_dataset_con, val_dataset_con, test_dataset_con
    elif cultivar == "PN":
        train_dataset_pn = VideoDiskDataset(f'../refined_data_21/PN/frame-60/train/metadata.json')
        train_dataset_pn.shuffle(random_state=42)
        val_dataset_pn = VideoDiskDataset(f'../refined_data_21/PN/frame-60/valid/metadata.json')
        test_dataset_pn = VideoDiskDataset(f'../refined_data_21/PN/frame-60/test/metadata.json')
        return train_dataset_pn, val_dataset_pn, test_dataset_pn
    elif cultivar == "ALL":
        train_dataset_ries = VideoDiskDataset(f'../refined_data_21/RIES/frame-60/train/metadata.json')
        train_dataset_pn = VideoDiskDataset(f'../refined_data_21/PN/frame-60/train/metadata.json')
        train_dataset_con = VideoDiskDataset(f'../refined_data_21/CON/frame-60/train/metadata.json')
        train_dataset_cf = VideoDiskDataset(f'../refined_data_21/CF/frame-60/train/metadata.json')
        train_dataset = ConcatDataset([train_dataset_ries, train_dataset_cf, train_dataset_con, train_dataset_pn])
        reshuffle_dataset(train_dataset, seed=42)
        val_dataset_ries = VideoDiskDataset(f'../refined_data_21/RIES/frame-60/valid/metadata.json')
        val_dataset_cf = VideoDiskDataset(f'../refined_data_21/CF/frame-60/valid/metadata.json')
        val_dataset_con = VideoDiskDataset(f'../refined_data_21/CON/frame-60/valid/metadata.json')
        val_dataset_pn = VideoDiskDataset(f'../refined_data_21/PN/frame-60/valid/metadata.json')
        val_dataset = ConcatDataset([val_dataset_ries, val_dataset_cf, val_dataset_con, val_dataset_pn])
        reshuffle_dataset(val_dataset, seed=42)
        test_dataset_ries = VideoDiskDataset(f'../refined_data_21/RIES/frame-60/test/metadata.json')
        test_dataset_cf = VideoDiskDataset(f'../refined_data_21/CF/frame-60/test/metadata.json')
        test_dataset_con = VideoDiskDataset(f'../refined_data_21/CON/frame-60/test/metadata.json')
        test_dataset_pn = VideoDiskDataset(f'../refined_data_21/PN/frame-60/test/metadata.json')
        test_dataset = ConcatDataset([test_dataset_ries, test_dataset_cf, test_dataset_con, test_dataset_pn])
        return train_dataset, val_dataset, test_dataset
    else:
        raise ValueError(f"Unknown cultivar: {cultivar}. Expected one of ['RIES', 'CF', 'CON', 'PN', 'ALL'].")