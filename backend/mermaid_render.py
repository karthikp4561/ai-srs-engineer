import subprocess
import tempfile
import os
import uuid


def render_mermaid_to_png(mermaid_code: str) -> str | None:
    """Renders Mermaid syntax to a PNG file and returns the file path, or None on failure."""
    temp_dir = tempfile.gettempdir()
    input_path = os.path.join(temp_dir, f"mmd_{uuid.uuid4().hex}.mmd")
    output_path = os.path.join(temp_dir, f"mmd_{uuid.uuid4().hex}.png")

    try:
        with open(input_path, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        result = subprocess.run(
            f'mmdc -i "{input_path}" -o "{output_path}" -b white -w 1000',
            capture_output=True, text=True, timeout=30, shell=True
        )

        if result.returncode != 0 or not os.path.exists(output_path):
            print("Mermaid render failed:", result.stderr)
            return None

        return output_path
    except Exception as e:
        print("Mermaid render exception:", e)
        return None
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)