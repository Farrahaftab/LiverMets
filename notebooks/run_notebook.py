"""Execute the notebook top to bottom and save the executed copy (outputs included)."""
import os
import sys
import time

import nbformat
from nbclient import NotebookClient

src, dst = sys.argv[1], sys.argv[2]
nb = nbformat.read(src, as_version=4)
client = NotebookClient(nb, timeout=5400, kernel_name='python3', allow_errors=False,
                        resources={'metadata': {'path': os.path.dirname(os.path.abspath(src))}})
t0 = time.time()
try:
    client.execute()
    status = 'OK'
except Exception as exc:  # keep partial outputs for debugging
    status = f'FAILED: {type(exc).__name__}: {str(exc)[:1500]}'
nbformat.write(nb, dst)
print(f'{status} in {time.time()-t0:,.0f}s -> {dst}', flush=True)
