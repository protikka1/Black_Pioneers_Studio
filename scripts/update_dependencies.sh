cat > scripts/update_dependencies.sh <<'EOF'
#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
BACKUP_FILE="$PROJECT_DIR/requirements.backup.txt"

echo "Black Pioneers Studio dependency updater"
echo "Project: $PROJECT_DIR"
echo

cd "$PROJECT_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment was not found:"
    echo "$VENV_DIR"
    echo
    echo "Create it with:"
    echo "python3 -m venv venv"
    exit 1
fi

source "$VENV_DIR/bin/activate"

echo "Python:"
python --version

echo
echo "Pip:"
python -m pip --version

if [ -f "$REQUIREMENTS_FILE" ]; then
    cp "$REQUIREMENTS_FILE" "$BACKUP_FILE"
    echo
    echo "Backup created:"
    echo "$BACKUP_FILE"
fi

echo
echo "Upgrading pip..."
python -m pip install --upgrade pip

echo
echo "Currently outdated packages:"
python -m pip list --outdated

echo
echo "Upgrading project dependencies..."

python -m pip install --upgrade \
    streamlit \
    moviepy \
    Pillow \
    edge-tts \
    imageio-ffmpeg \
    pandas \
    openpyxl

echo
echo "Checking dependency compatibility..."

if ! python -m pip check; then
    echo
    echo "ERROR: Dependency conflicts were detected."

    if [ -f "$BACKUP_FILE" ]; then
        echo "Restoring packages from requirements backup..."
        python -m pip install -r "$BACKUP_FILE"
    fi

    exit 1
fi

echo
echo "Writing updated requirements.txt..."
python -m pip freeze > "$REQUIREMENTS_FILE"

echo
echo "Updated package versions:"
grep -Ei \
    '^(streamlit|moviepy|pillow|edge-tts|imageio-ffmpeg|pandas|openpyxl)==' \
    "$REQUIREMENTS_FILE"

echo
echo "Dependency update completed successfully."
echo
echo "Review changes with:"
echo "git diff requirements.txt"
EOF