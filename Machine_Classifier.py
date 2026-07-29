#!/usr/bin/env python3
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments

# Define training dataset
# Text is input command (either voice or typed)
# Label is the corresponding intent category (the goal of the command)
train_data = {
    "text": [
        # Volume
        "turn up the volume", "make it louder", "increase the sound", "raise the volume", "turn down the volume", "make it quieter", " decrease the sound", "lower the volume", # 0: Adjust Volume
        # Create Folder
        "create a new folder called notes", "make a directory", "make a directory called projects", "create a folder", # 1: Create Folder
    ],
    "label": [
        0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 1, 1
    ]
}
set = Dataset.from_dict(train_data)

# Load sentence model
model = SetFitModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

# Train model
trainer = Trainer(
    model = model,
    train_dataset = set,
    args = TrainingArguments(
        batch_size = 16,
        num_epochs = 1,
    )
)
trainer.train()

# Save the model
model.save_pretrained("./intent_model")
