import torch.nn as nn
from transformers import Trainer


class WeightedLossTrainer(Trainer):
    def compute_loss(self, model, weights_tensor, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        loss_fct = nn.CrossEntropyLoss(weight=weights_tensor)
        loss = loss_fct(logits, labels.long())
        
        return (loss, outputs) if return_outputs else loss