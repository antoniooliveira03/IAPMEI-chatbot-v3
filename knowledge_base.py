import subprocess

# List your scripts in order
scripts = [
    "01_load_clean.py",
    "02_chunking.py",
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