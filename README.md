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

## Usage Examples

### Basic Usage
```bash
# Run with -t settings (by default 1 iterations)
python3 test.py -k "test_basic_gnn_edgecnn_eval_cuda" -t 300
```


## Docker Registry

https://hub.docker.com/repository/docker/butterman2/torchbench-simple



## Contributing

We welcome contributions! Please feel free to submit a Pull Request.
