import os, multiprocessing
import wandb
import time
import torch
import seaborn as sns
import matplotlib.pyplot as plt
import argparse
from transformers import Trainer, TrainingArguments, AdamW
from utils.model_configuration import *
from utils.model_configuration import initialise_model, collate_fn
from utils.evaluate import evaluate_testset
from utils.weight import compute_weights
from utils.weighted_loss import WeightedLossTrainer
from utils.load_dataset import load_data
from utils.wandb_key import WANDB_KEY


# script arguments
parser = argparse.ArgumentParser()
parser.add_argument('--lr', type=float, help='Learning rate')
parser.add_argument('--batch_size', type=int, default=8, help='Batch size per GPU')
parser.add_argument('--num_epochs', type=int, default=8, help='Number of epochs')
parser.add_argument('--dataset', type=str, default='ALL', help='Dataset to use (RIES, CF, CON, PN, ALL)')
args = parser.parse_args()


# Params
LR = args.lr if args.lr else 5e-4
BATCH_SIZE = args.batch_size if args.batch_size else 1
NUM_EPOCHS = args.num_epochs if args.num_epochs else 8
DATA = args.data if args.dataset else 'ALL'
print(f"Running ViVit on {DATA} dataset with learning rate {LR}, batch size {BATCH_SIZE}, and {NUM_EPOCHS} epochs.")


start = time.time()
os.environ["CUDA_VISIBLE_DEVICES"]="0,1,2,3"
print(f'CPU count: {multiprocessing.cpu_count()}')
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')


# load datasets
train_dataset, val_dataset, test_dataset = load_data(DATA)
print(f"{DATA} dataset is loaded.")


weights_tensor = compute_weights(train_dataset).to(device)
print('Weights tensor:', weights_tensor)



model = initialise_model(train_dataset, device)
training_output_dir = "./tmp/results"
training_args = TrainingArguments(
    output_dir=training_output_dir,         
    num_train_epochs=NUM_EPOCHS,         
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE, 
    learning_rate=LR,            
    weight_decay=0.01,
    logging_strategy="steps",              
    logging_dir="./logs",           
    logging_steps=10,                
    seed=42,                       
    eval_strategy="steps",    
    eval_steps=50,                   
    warmup_steps=int(0.1 * 20),      
    optim="adamw_torch",          
    lr_scheduler_type="cosine",      
    fp16=True,
    dataloader_num_workers=8,
    dataloader_persistent_workers=True,
    dataloader_pin_memory=True, 
    report_to="wandb",
    load_best_model_at_end=True,  # Automatically load the best model
    metric_for_best_model="eval_loss",  # Use validation loss to determine the best model
    greater_is_better=False,  # Lower loss is better
)


wandb.login(key=WANDB_KEY)
PROJECT, MODEL_NAME, DATASET = "ViViT", "google/vivit-b-16x2-kinetics400", "bud-dataset"
NAME = f"new-frame60-{DATA}-21-N-bs{4*BATCH_SIZE}-weight-{LR}-epoch{NUM_EPOCHS}-cos"
wandb.init(project=PROJECT, tags=[MODEL_NAME, DATASET], notes ="Fine tuning ViViT with grape buds dataset", name=NAME)


optimizer = torch.optim.AdamW(model.parameters(), lr=LR, betas=(0.9, 0.999), eps=1e-08)
# Define the trainer
trainer = WeightedLossTrainer(
    model=model,
    weights_tensor=weights_tensor,                   
    args=training_args,
    data_collator=collate_fn,             
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    optimizers=(optimizer, None),  
    compute_metrics = compute_metrics
)

# train
with wandb.init(project=PROJECT, job_type="train", tags=[MODEL_NAME, DATASET], notes =f"Fine tuning {MODEL_NAME} with {DATASET}."):
    train_results = trainer.train()
print(f"Train and process time passed: {((time.time() - start) / 60):.1f} minutes")


# Save the model
trainer.save_model(f"./best_models/{NAME}/")


# Test on the test dataset
results = evaluate_testset(test_dataset, f"./best_models/{NAME}/")
print(f"Accuracy: {results['accuracy']:.4f}")
print(f"Precision: {results['precision']:.4f}")
print(f"Recall: {results['recall']:.4f}")
print(f"F1-score: {results['f1']:.4f}")
print(f"ROC-AUC: {results['roc_auc']:.4f}")
print(f"Confusion Matrix:\n{results['confusion_matrix']}")
plt.figure(figsize=(6, 6))
sns.heatmap(results['confusion_matrix'], annot=True, fmt="d", cmap="Blues", xticklabels=["Dead", "Alive"], yticklabels=["Dead", "Alive"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.savefig(f"./best_models/{NAME}/confusion_matrix.png", dpi=300, bbox_inches="tight")
plt.close()
print("Confusion matrix saved as confusion_matrix.png")