# `mmiLoader.py` Refactoring Plan

The `mmiLoader.py` script is a core component that dynamically parses USB content and generates the UI/JSON structures for the ConnectBox. Currently, it is a monolithic, deeply nested ~1,200 line script that uses outdated practices. The goal is to modernize it for stability without altering its core logic.

## User Review Required
> [!IMPORTANT]
> Since this is a critical loading script for the media server, any deviations in output could break the UI. I will focus purely on **structural and robustness refactoring** rather than feature changes. Are there any specific behaviors in the loader that you want me to fundamentally change or fix while I am in there?

## Proposed Changes

### 1. Robust Exception Handling
The script currently relies heavily on bare `except: pass` blocks, which catch and silently swallow critical errors like `NameError` or `SyntaxError`.
- **[MODIFY]** Replace bare `except:` blocks with targeted exceptions (e.g., `except OSError:`, `except subprocess.CalledProcessError:`).
- **[MODIFY]** Introduce proper error logging using the existing `logging` module so issues can be diagnosed.

### 2. Modernizing Subprocess Calls
- **[MODIFY]** Replace legacy `os.system()` and `os.popen()` calls with `subprocess.run()`. This prevents shell injection vulnerabilities and allows the script to natively catch non-zero exit codes.

### 3. Modularizing the Monolith
The entire script logic lives inside one massive `mmiloader_code()` function.
- **[MODIFY]** Break the monolith into focused helper functions:
  - `update_display_status(message)`: Centralizes the `/tmp/creating_menus.txt` file writing.
  - `process_directory(path)`: Handles the recursive folder analysis.
  - `generate_thumbnail(file_path, media_type)`: Handles the `ffmpeg` operations for audio/video thumbnails.
  - `build_metadata_json()`: Handles generating the `main.json` and `interface.json` files.

### 4. Path Management
- **[MODIFY]** Normalize path construction using `os.path.join` consistently rather than string concatenation (`+ "/" +`) to prevent double-slash pathing issues.

### 5. Variable Scope and Cleanup
- **[MODIFY]** Remove unused functions (e.g., the unused `intersection` helper).
- **[MODIFY]** Give variables descriptive names (replace `x`, `y`, `z` with meaningful boolean flags or counters).

## Verification Plan
1. Ensure the script passes a strict `python -m py_compile` syntax check.
2. Ensure there are zero bare `except:` blocks remaining in the code.
3. Validate that the logic flow matches the original intent (thumbnails, webpaths, collections).
4. Run the script manually via SSH (if testing on device) to ensure it indexes a test USB drive correctly.
