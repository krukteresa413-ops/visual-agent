"""Check image generation dependencies and config on ECS"""
import os

print("=== Python Deps ===")
for mod in ["requests", "PIL", "httpx"]:
    try:
        __import__(mod)
        print(f"  {mod}: OK")
    except ImportError:
        print(f"  {mod}: MISSING")

print("\n=== Env Config ===")
for k in ["COMFYUI_URL", "IMAGE_GEN_PROVIDER", "STABLE_DIFFUSION_URL", "DEEPSEEK_API_KEY"]:
    val = os.environ.get(k, "NOT SET")
    if val and len(val) > 30:
        val = val[:10] + "..." + val[-4:]
    print(f"  {k}: {val}")

print("\n=== .env file ===")
env_path = "/opt/visual-agent/app/backend/.env"
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "KEY" in line.upper():
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        k, v = parts
                        print(f"  {k}=*** ({len(v)} chars)")
                    else:
                        print(f"  {line}")
                else:
                    print(f"  {line}")
