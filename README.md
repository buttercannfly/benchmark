# PyTorch Benchmarking Tool

This project is an enhanced version of the original PyTorch benchmarking tool, featuring improved deployment scripts and additional functionality for more flexible benchmarking.

## Key Improvements

### 1. Simplize Deployment Script
Our deployment process has been significantly improved with:
- Simplified environment setup
- Better error handling and validation
- Clear documentation and usage instructions
- More maintainable code structure

### 2. Enhanced Evaluation Control
We've added a new `-t` parameter that allows users to control the number of evaluation iterations, providing more flexibility in benchmarking.

### 3. Separet time for each phase
We've separate the total test time into model setup 、 train/eval 、 model delete and record time for each phase

## Usage Examples

### Basic Usage
```bash
# Run with -t settings (by default 1 iterations)
python3 test.py -k "test_basic_gnn_edgecnn_eval_cuda" -t 300
```

### Example Result

```
Using pod: torchbench-65d578f97c-s8wnr
=== Running tests with tensor-fusion DISABLED ===
Testing model: basic_gnn_edgecnn with tensor-fusion DISABLED
---------------------------------------------------------
Executing: python3 test.py -k "test_basic_gnn_edgecnn_eval_cuda" -t 1000
Model initialization time: 1.10 seconds
Evaluation time: 17.85 seconds
Cleanup time: 0.07 seconds
Total time: 19.01 seconds
=== Performance Comparison (Tensor-Fusion Disabled vs Enabled) ===
Model Name | Metric | Disabled (s) | Enabled (s) | Speedup
------------------------------------------------------------
basic_gnn_edgecnn | init   | 1.10        | 1.16       | 0.95x
basic_gnn_edgecnn | eval   | 17.85       | 19.51      | 0.91x
basic_gnn_edgecnn | cleanup | 0.07        | 0.07       | 1.00x
basic_gnn_edgecnn | total  | 19.01       | 20.74      | 0.92x
```


## Docker Registry

https://hub.docker.com/repository/docker/butterman2/torchbench-simple



## Contributing

We welcome contributions! Please feel free to submit a Pull Request.
