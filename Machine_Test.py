from setfit import SetFitModel
import torch
import numpy as np
import time

model_path = "./intent_model"
model = SetFitModel.from_pretrained(model_path)

# Classes:
# 0: Adjust Volume
# 1: Create Folder

test_sentences = [
    ("increase the volume", 0),
    ("create a new directory called homework", 1),
    ("set a timer for 10 minutes", -1),
    ("play some jazz", -1),
    ("remind me to call mom at 5 pm", -1),
    ("what is the weather like today", -1),
    ("create a notes text file", 1),
    ("tell me a joke", -1),
    ("delete the assignment in my documents", -1),
    ("read my results file", -1),
    ("tell me the size of my homework folder", -1),
    ("move the notes file to my downloads folder", -1),
    ("rename my apps folder to applications", -1),
    ("open my email", -1),
    ("add my system specs to a text file on my desktop", -1),
    ("where is my homework folder", -1),
    ("install a system monitor", -1)
]

correct = 0
mismatch = []

print("--- Model Predictions ---")
for i, (sentence, expected_intent) in enumerate(test_sentences):
    start_time = time.time()
    probs = model.predict_proba([sentence])
    end_time = time.time()

    if isinstance(probs, torch.Tensor):
        probs = probs.detach().cpu().numpy()
    probs = np.array(probs).squeeze()

    best_intent = probs.argmax()
    confidence = probs[best_intent]

    if confidence < 0.60:
        final_intent = -1
        note = f"{confidence:.2f} (Forced AI)"
    else:
        final_intent = best_intent
        note = f"{confidence:.2f}"

    print(f"Input: {sentence}")
    print(f"Expected Intent: {expected_intent}")
    print(f"Predicted Intent: {final_intent}")
    print(f"Confidence: {note}")
    print(f"Time: {end_time - start_time:.4f} seconds\n")

    if final_intent == expected_intent:
        correct += 1
    else:
        mismatch.append((sentence, expected_intent, final_intent))

print(f"Total Correct: {correct}/{len(test_sentences)}")
print(f"Accuracy: {correct/len(test_sentences):.2%}")
print("\n--- Mismatched Predictions ---")
for sentence, expected_intent, final_intent in mismatch:
    print(f"\tEXPIN: [{expected_intent}] PREDIN: [{final_intent}] INPUT: {sentence}")