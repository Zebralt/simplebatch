# Simplebatch

Utility functions to perform threaded batch calls upon a callable in Python.

Easily accessible through a decorator:

```python
from simplebatch import batchize
from concurrent.futures import ThreadPoolExecutor

@batchize  # No quota restrictions with default ThreadPoolExecutor configuration
# or
@batchize(
  executor=ThreadPoolExecutor(max_workers=5),
  quota=300,   # N elements every
  interval=60  # seconds
)
def single_action(a):
  return a + 1
  
assert single_action(1) == 2
assert *single_action.batch(range(3)), == (1, 2, 3)
```
