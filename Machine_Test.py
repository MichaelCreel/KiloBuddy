from setfit import SetFitModel
import torch

model_path = "./intent_model"
model = SetFitModel.from_pretrained(model_path)

test_sentences = [
    "increase the volume",
    "create a new directory called homework",
    "set a timer for 10 minutes",
    "play some jazz",
    "remind me to call mom at 5 pm",
]

probabilities = model.predict_proba(test_sentences)

if isinstance(probabilities, torch.Tensor):
    probabilities = probabilities.cpu().numpy()

print("--- Model Predictions ---")
for i, sentence in enumerate(test_sentences):
    probs = probabilities[i]
    best_intent = probs.argmax()
    confidence = probs[best_intent]

    if confidence < 0.60:
        final_intent = -1
        note = f"{confidence:.2f} (Forced AI)"
    else:
        final_intent = best_intent
        note = f"{confidence:.2f}"

    print(f"Input: {sentence}")
    print(f"Intent: {final_intent}")
    print(f"Confidence: {note}\n")