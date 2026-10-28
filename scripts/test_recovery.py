import os
from pathlib import Path
from backend.app.services.recovery.recovery_manager import analyze_image_deep, execute_advanced_recovery

samples_dir = Path("test_samples")
for f in sorted(samples_dir.iterdir()):
    if "corrupt" in f.name:
        print("="*60)
        print(f"Testing: {f.name} ({f.stat().st_size} bytes)")
        try:
            analysis = analyze_image_deep(str(f))
            print(f"Format: {analysis.image_format}, Corrupt: {analysis.is_corrupt}, Score: {analysis.integrity_score}%")
            print(f"Issues: {[i.message for i in analysis.issues]}")
            res = execute_advanced_recovery(str(f), action="smart_auto")
            files = res.get("recovered_files", [])
            print(f"Recovered count: {len(files)}")
            for r in files:
                print(f"  - [{r.get('method')}]: {r.get('width')}x{r.get('height')} -> {r.get('filename')} (has preview: {bool(r.get('preview_base64'))})")
        except Exception as e:
            import traceback
            traceback.print_exc()
