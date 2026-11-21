"""Build a small, reproducible offline USB helper, never a fake TV app installer."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
FILES=['USB-Jarvis/START-HIER.html','USB-Jarvis/LIES-MICH.txt','docs/FERNSEHER.md']
def build():
    target=ROOT/'updates/JARVIS-TV-USB.zip';target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as archive:
        for name in FILES:
            info=zipfile.ZipInfo(name,date_time=(2026,11,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,(ROOT/name).read_bytes())
    print(f'Offline USB-Starthilfe: {target.name}, {target.stat().st_size} Bytes; keine KI oder TV-App-Installation.')
    return target
if __name__=='__main__':build()
