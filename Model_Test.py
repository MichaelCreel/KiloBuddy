import subprocess
import requests
import json
import time
import re
from pathlib import Path
import matplotlib.pyplot as plt

# Variables required for prompting
OS_VERSION = "linux-linuxmint"
DESKTOP_PATH = str(Path.home() / 'Desktop')
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "test_output.txt"

try:
    with open("initial_prompt", "r") as f:
        lines = f.readlines()
        INITIAL_PROMPT = "".join(lines).strip()
except FileNotFoundError:
    INITIAL_PROMPT = "Failed to find prompt file"
    print("[ERROR] initial_prompt file was not found.")

# Models to test
MODELS = [
    "llama3.1:8b",
    "llama3.2:1b",
    "llama3.2:3b",
    "phi3:mini",
    "qwen2.5-coder:7b",
    "qwen2.5:14b-instruct",
    "mixtral:8x7b",
    "gemma2:9b",
    "qwen2.5:7b",
    "phi3:medium",
    "deepseek-r1:7b",
    "deepseek-r1:14b",
]

# Prompts to test the models with and the correlating correct information
PROMPTS = {
    "website_folder": {
        "command": "create a website folder on my desktop with starter files inside of it",
        "requires_text": True,
        "expected_commands": [
            f'{{cr_dir: "{DESKTOP_PATH}/website"}}',
            f'{{cr_fil: "{DESKTOP_PATH}/website/index.html"}}',
            f'{{cr_fil: "{DESKTOP_PATH}/website/style.css"}}',
            f'{{cr_fil: "{DESKTOP_PATH}/website/main.js"}}'
        ]
    },
    "gettysburg_summary": {
        "command": "summarize the gettysburg address",
        "requires_text": True,
        "expected_commands": []
    },
    "results_summary": {
        "command": "summarize the results file on my desktop",
        "requires_text": False,
        "expected_commands": [
            f'{{ds: "{DESKTOP_PATH}", "results"}}',
            "summarize the results file"
        ]
    },
    "get_size": {
        "command": "tell me the size of assignment dot t x t on my desktop",
        "requires_text": False,
        "expected_commands": [
            f'{{rd_inf: "{DESKTOP_PATH}/assignment.txt", "size"}}',
            "tell user file size"
        ]
    },
    "delete_file": {
        "command": "delete the results text file on my desktop",
        "requires_text": True,
        "expected_commands": [
            f'{{dl: "{DESKTOP_PATH}/results.txt"}}'
        ]
    }
}

RUNS_PER_MODEL = 3

# Matches """text block"""
TEXT_BLOCK_PATTERN = re.compile(r'"""[\s\S]*?"""')
# Matches >> [tasks] << 
TABLE_PATTERN = re.compile(r">>\s*([\s\S]*?)\s*<<", re.MULTILINE)
# Matches [1] {command} # USER/AI --- PENDING (strictly pending for initial generation)
ROW_PATTERN = re.compile(r"\[(\d+)\]\s+(.+?)\s+#\s+(USER|AI)\s+---\s+PENDING")

ANSI_PATTERN = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

def strip_ansi(text):
    return ANSI_PATTERN.sub('', text)

def run_model(model, command):
    """Executes the Ollama generation via the local REST API."""
    combined_prompt = f"OS: {OS_VERSION}\nDEFAULT PATH: {DESKTOP_PATH}\n{INITIAL_PROMPT}\nUser Command: {command}"
    start = time.time()
    
    reply = ""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": combined_prompt},
            timeout=120,
            stream=True
        )
        
        if response.ok:
            for line in response.iter_lines():
                if not line:
                    continue
                obj = json.loads(line.decode("utf-8"))
                if "response" in obj:
                    reply += obj["response"]
                if obj.get("done"):
                    break
        else:
            reply = f"[ERROR] API Request Failed (Status {response.status_code}): {response.text}"
            
    except Exception as e:
        reply = f"[ERROR] {e}"
    
    gen_time = time.time() - start
    
    return reply.strip(), gen_time

def evaluate_response(response, requires_text, expected_commands):
    """Scores a single response based on KiloBuddy's expected syntax formatting."""
    scores = {
        "text_valid": False,
        "table_valid": False,
        "tasks_valid": False,
        "exact_match": False
    }

    if "[ERROR]" in response:
        return scores

    # Text Check
    has_text = bool(TEXT_BLOCK_PATTERN.search(response))
    if requires_text and has_text:
        scores["text_valid"] = True
    elif not requires_text and not has_text:
        scores["text_valid"] = True

    # Table Check
    table_match = TABLE_PATTERN.search(response)
    if table_match:
        scores["table_valid"] = True
        table_content = table_match.group(1).strip()
        
        # Tasks Formatting Check and Exact Match Check
        lines = [line.strip() for line in table_content.split("\n") if line.strip()]
        
        extracted_commands = []
        tasks_perfect = True

        for line in lines:
            row_match = ROW_PATTERN.match(line)
            if not row_match:
                tasks_perfect = False
            else:
                extracted_commands.append(row_match.group(2)) # Group 2 is the actual tool command

        scores["tasks_valid"] = (tasks_perfect and len(lines) > 0) or (len(lines) == 0 and len(expected_commands) == 0)

        # Exact Match
        if scores["tasks_valid"]:
            if len(extracted_commands) == len(expected_commands):
                match = all(ext.strip() == exp.strip() for ext, exp in zip(extracted_commands, expected_commands))
                scores["exact_match"] = match

    elif len(expected_commands) == 0:
        scores["table_valid"] = True
        scores["tasks_valid"] = True
        scores["exact_match"] = True

    return scores

def log_to_file(model, prompt_name, run_idx, response, scores):
    """Appends raw model output and score evaluations to test_output.txt."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"=" * 60 + "\n")
        f.write(f"MODEL: {model} | PROMPT: {prompt_name} | RUN: {run_idx + 1}\n")
        f.write(f"EVALUATION: {scores}\n")
        f.write("-" * 60 + "\n")
        f.write(f"{response}\n")
        f.write(f"=" * 60 + "\n\n")

def main():
    # Clear results log
    with open(LOG_FILE, "w", encoding = "utf-8") as f:
        f.write("")

    results_data = {}

    print(f"Starting evaluations for {len(MODELS)} models.")
    print("-" * 50)

    for model in MODELS:
        print(f"\nEvaluating Model: {model}")
        model_stats = {
            "times": [],
            "text_scores": [],
            "table_scores": [],
            "tasks_scores": [],
            "exact_scores": []
        }

        for prompt_name, config in PROMPTS.items():
            for i in range(RUNS_PER_MODEL):
                print(f"  [{prompt_name}] Run {i+1}/{RUNS_PER_MODEL}... ", end="", flush=True)
                
                output, gen_time = run_model(model, config["command"])
                scores = evaluate_response(output, config["requires_text"], config["expected_commands"])
                
                log_to_file(model, prompt_name, i, output, scores)

                model_stats["times"].append(gen_time)
                model_stats["text_scores"].append(1 if scores["text_valid"] else 0)
                model_stats["table_scores"].append(1 if scores["table_valid"] else 0)
                model_stats["tasks_scores"].append(1 if scores["tasks_valid"] else 0)
                model_stats["exact_scores"].append(1 if scores["exact_match"] else 0)
                
                print(f"{gen_time:.2f}s")

        total_runs = len(PROMPTS) * RUNS_PER_MODEL
        avg_time = sum(model_stats["times"]) / total_runs
        
        pct_text = (sum(model_stats["text_scores"]) / total_runs) * 100
        pct_table = (sum(model_stats["table_scores"]) / total_runs) * 100
        pct_tasks = (sum(model_stats["tasks_scores"]) / total_runs) * 100
        pct_exact = (sum(model_stats["exact_scores"]) / total_runs) * 100
        
        overall_acc = (pct_text + pct_table + pct_tasks + pct_exact) / 4

        results_data[model] = {
            "avg_time": avg_time,
            "accuracy": overall_acc,
            "breakdown": {
                "Text": pct_text,
                "Table": pct_table,
                "Format": pct_tasks,
                "Exact": pct_exact
            }
        }

        print(f"\n--- Results for {model} ---")
        print(f"Avg Generation Time: {avg_time:.2f} seconds")
        print(f"Overall Accuracy:    {overall_acc:.1f}%")
        print(f"  - Text Format:     {pct_text:.1f}%")
        print(f"  - Table Tags:      {pct_table:.1f}%")
        print(f"  - Row Formatting:  {pct_tasks:.1f}%")
        print(f"  - Exact Tool Match:{pct_exact:.1f}%")
        print("-" * 50)

    # Plot data
    print("\nGenerating Scatter Plot...")
    
    models = list(results_data.keys())
    times = [data["avg_time"] for data in results_data.values()]
    accuracies = [data["accuracy"] for data in results_data.values()]

    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#1e1e1e')
    ax.set_facecolor('#252526')

    ax.scatter(times, accuracies, color='#60E666', s=120, zorder=5, edgecolor='white', linewidth=1.5)

    # Model labels
    for i, model in enumerate(models):
        ax.annotate(
            model, 
            (times[i], accuracies[i]), 
            textcoords="offset points", 
            xytext=(0, 10), 
            ha='center',
            fontsize=10,
            fontweight='bold',
            color='white'
        )

    ax.set_title("KiloBuddy Benchmark: Generation Time vs. Syntax Accuracy", fontsize=14, fontweight='bold', color='white', pad=15)
    ax.set_xlabel("Average Generation Time (Seconds) [Faster ←]", fontsize=12, fontweight='bold', color='white', labelpad=10)
    ax.set_ylabel("Overall Accuracy (%) [Higher →]", fontsize=12, fontweight='bold', color='white', labelpad=10)

    ax.tick_params(colors='white', labelsize=10)
    for spine in ax.spines.values():
        spine.set_color('#555555')

    # Bounds
    ax.set_ylim(-5, 105)
    max_time = max(times) if times else 5.0
    ax.set_xlim(max(max_time * 1.3, 5.0), 0)  # Inverted X-axis

    ax.grid(True, linestyle='--', alpha=0.3, color='#888888')
    plt.tight_layout()
    
    plot_path = SCRIPT_DIR / 'model_evaluation_results.png'
    plt.savefig(plot_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    print(f"Saved graph to '{plot_path.name}'")
    plt.show()

if __name__ == "__main__":
    main()
