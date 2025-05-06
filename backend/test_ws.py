import subprocess
print(subprocess.check_output(["where", "ffmpeg"]).decode().strip())