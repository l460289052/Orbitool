+ ~~use coroutines (and yield) to substitute for thread (avoid context changing)~~
+ complete data flow
  + ~~file~~
  + ~~noise~~
    + ~~rewrite noise function~~
    + ~~denoise~~
    + ~~process pool~~
  + ~~peak shape~~
  + ~~calibration~~
  + ~~fit~~
    + ~~peak fit~~
    + ~~peak filter~~
    + ~~peak refit~~
  + ~~mass defect~~
  + ~~time series~~
  + ~~save/load~~
  + ~~formula~~
+ details
  + plot
  + shortcuts
  + export


+ add tqdm to for range and add left time assume
+ add two stage tqdm (read & write)
  ```python
  for i in manager.tqdm(range(100), len = 100, msg = "123"):
    pass
  ```