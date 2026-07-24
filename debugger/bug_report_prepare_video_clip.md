# Bug Report: prepare_video_clip Duration Crash

Date: 2026-07-24
Project: Black_Pioneers_Studio
File: app.py
Function: prepare_video_clip

## Summary

Video generation could fail when a source video had an unreadable or zero duration.

## Symptoms

- Failure during short generation in the video preparation path.
- Risky arithmetic at the duration repeat logic:
  - required_duration / clip.duration

## Root Cause

The code assumed clip.duration was always a valid positive number. In some media files, MoviePy can return None or 0 for duration.

## Technical Risk

- Comparison against None:
  - clip.duration >= required_duration
- Division by None or zero:
  - required_duration / clip.duration

## Fix Applied

Updated prepare_video_clip to:

1. Normalize duration with a safe fallback:
   - clip_duration = float(clip.duration or 0.0)
2. Guard invalid duration early:
   - if clip_duration <= 0: close clip and raise ValueError with file path context
3. Use clip_duration for all comparisons and arithmetic.
4. Keep resize operation type-safe for static analysis.

## Files Changed

- app.py

## Validation

- Command run:
  - python3 -m py_compile app.py
- Result:
  - Passed
- Diagnostics:
  - No errors remaining in app.py

## User Impact

- Prevents crashes caused by malformed/unsupported video metadata.
- Surfaces a clear error message identifying the problematic asset.

## Recommended Follow-up

- Optionally catch this ValueError in the Streamlit UI and show a friendly upload error with the file name.
