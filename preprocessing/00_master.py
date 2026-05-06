import subprocess

# List scripts in order
scripts = [
    "summarised_data.py"
    "01_cleaning.py",
    "02_chunk.py",
    "03_vectorize.py"
]

for script in scripts:
    print(f"Running {script}...")
    result = subprocess.run(["python", script], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[ERROR] {script} failed:")
        print(result.stderr)
        break
    else:
        print(result.stdout)