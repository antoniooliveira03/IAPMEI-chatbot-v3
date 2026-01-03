import subprocess

# List your scripts in order
scripts = [
    #"01_cleaning.py",
    "02_chunk.py",
    "03_metadata.py"
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