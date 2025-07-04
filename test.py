"""test.py
Setup and Run hub models.

Make sure to enable an https proxy if necessary, or the setup steps may hang.
"""

# This file shows how to use the benchmark suite from user end.
import gc
import os
import unittest
import argparse
import sys
import time  # Add time module import
import concurrent.futures  # Add concurrent.futures import

import torch
from torchbenchmark import (
    _list_canary_model_paths,
    _list_model_paths,
    get_metadata_from_yaml,
    ModelTask,
)
from torchbenchmark.util.metadata_utils import skip_by_metadata

# Some of the models have very heavyweight setup, so we have to set a very
# generous limit. That said, we don't want the entire test suite to hang if
# a single test encounters an extreme failure, so we give up after a test is
# unresponsive to 5 minutes by default. (Note: this does not require that the
# entire test case completes in 5 minutes. It requires that if the worker is
# unresponsive for 5 minutes the parent will presume it dead / incapacitated.)
TIMEOUT = int(os.getenv("TIMEOUT", 300))  # Seconds

# Add argument parser
parser = argparse.ArgumentParser(description='Run benchmark tests', add_help=False)
parser.add_argument('-t', '--iterations', type=int, default=300,
                    help='Number of iterations to run inference (default: 300)')
# Parse only known arguments to avoid interfering with unittest
args, unknown = parser.parse_known_args()

# Store iterations in a global variable
ITERATIONS = args.iterations

class TestBenchmark(unittest.TestCase):
    def setUp(self):
        gc.collect()

    def tearDown(self):
        gc.collect()


def _create_example_model_instance(task: ModelTask, device: str):
    skip = False
    try:
        task.make_model_instance(test="eval", device=device, extra_args=["--accuracy"])
    except NotImplementedError:
        try:
            task.make_model_instance(
                test="train", device=device, extra_args=["--accuracy"]
            )
        except NotImplementedError:
            skip = True
    finally:
        if skip:
            raise NotImplementedError(
                f"Model is not implemented on the device {device}"
            )


def _load_test(path, device):
    model_name = os.path.basename(path)
    print(f"Loading test for model {model_name} on {device}")


    def _skip_cuda_memory_check_p(metadata):
        if device != "cuda":
            return True
        if "skip_cuda_memory_leak" in metadata and metadata["skip_cuda_memory_leak"]:
            return True
        return False

    def example_fn(self):
        task = ModelTask(model_name, timeout=TIMEOUT)
        with task.watch_cuda_memory(
            skip=_skip_cuda_memory_check_p(metadata), assert_equal=self.assertEqual
        ):
            try:
                _create_example_model_instance(task, device)
                accuracy = task.get_model_attribute("accuracy")
                assert (
                    accuracy == "pass"
                    or accuracy == "eager_1st_run_OOM"
                    or accuracy == "eager_2nd_run_OOM"
                ), f"Expected accuracy pass, get {accuracy}"
                task.del_model_instance()
            except NotImplementedError as e:
                self.skipTest(
                    f'Accuracy check on {device} is not implemented because "{e}", skipping...'
                )

    def train_fn(self):
        metadata = get_metadata_from_yaml(path)
        task = ModelTask(model_name, timeout=TIMEOUT)
        allow_customize_batch_size = task.get_model_attribute(
            "ALLOW_CUSTOMIZE_BSIZE", classattr=True
        )
        # to speedup test, use batch size 1 if possible
        batch_size = 1 if allow_customize_batch_size else None
        with task.watch_cuda_memory(
            skip=_skip_cuda_memory_check_p(metadata), assert_equal=self.assertEqual
        ):
            try:
                task.make_model_instance(
                    test="train", device=device, batch_size=batch_size
                )
                task.invoke()
                task.check_details_train(device=device, md=metadata)
                task.del_model_instance()
            except NotImplementedError as e:
                self.skipTest(
                    f'Method train on {device} is not implemented because "{e}", skipping...'
                )

    def eval_fn(self):
        metadata = get_metadata_from_yaml(path)
        task = ModelTask(model_name, timeout=TIMEOUT)
        allow_customize_batch_size = task.get_model_attribute(
            "ALLOW_CUSTOMIZE_BSIZE", classattr=True
        )
        # to speedup test, use batch size 1 if possible
        batch_size = 1 if allow_customize_batch_size else None
        with task.watch_cuda_memory(
            skip=_skip_cuda_memory_check_p(metadata), assert_equal=self.assertEqual
        ):
            try:
                # Measure model initialization time
                init_start_time = time.time()
                task.make_model_instance(
                    test="eval", device=device, batch_size=batch_size
                )
                init_time = time.time() - init_start_time
                print(f"\nModel initialization time: {init_time:.2f} seconds")

                # Measure evaluation time
                eval_start_time = time.time()

                # Define a function to execute a single iteration
                def run_iteration():
                    # Only measure invoke time
                    invoke_start = time.time()
                    task.invoke()
                    invoke_time = time.time() - invoke_start
                    
                    # Run checks after timing
                    task.check_details_eval(device=device, md=metadata)
                    task.check_eval_output()
                    return invoke_time
                
                # Use ThreadPoolExecutor for parallel execution
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit all iterations to the executor
                    futures = [executor.submit(run_iteration) for _ in range(ITERATIONS)]
                    # Wait for all iterations to complete and sum up invoke times
                    invoke_times = [future.result() for future in concurrent.futures.wait(futures)[0]]
                    eval_time = sum(invoke_times)
                
                print(f"Evaluation time (invoke only): {eval_time:.2f} seconds")

                # Measure cleanup time
                cleanup_start_time = time.time()
                task.del_model_instance()
                cleanup_time = time.time() - cleanup_start_time
                print(f"Cleanup time: {cleanup_time:.2f} seconds")

                # Print total time
                total_time = init_time + eval_time + cleanup_time
                print(f"Total time: {total_time:.2f} seconds")
            except NotImplementedError as e:
                self.skipTest(
                    f'Method eval on {device} is not implemented because "{e}", skipping...'
                )

    def check_device_fn(self):
        task = ModelTask(model_name, timeout=TIMEOUT)
        with task.watch_cuda_memory(
            skip=_skip_cuda_memory_check_p(metadata), assert_equal=self.assertEqual
        ):
            try:
                task.make_model_instance(test="eval", device=device)
                task.check_device()
                task.del_model_instance()
            except NotImplementedError as e:
                self.skipTest(
                    f'Method check_device on {device} is not implemented because "{e}", skipping...'
                )

    metadata = get_metadata_from_yaml(path)
    for fn, fn_name in zip(
        [example_fn, train_fn, eval_fn, check_device_fn],
        ["example", "train", "eval", "check_device"],
    ):
        # set exclude list based on metadata
        setattr(
            TestBenchmark,
            f"test_{model_name}_{fn_name}_{device}",
            (
                unittest.skipIf(
                    skip_by_metadata(
                        test=fn_name, device=device, extra_args=[], metadata=metadata
                    ),
                    "This test is skipped by its metadata",
                )(fn)
            ),
        )


def _load_tests():
    
    devices = ["cpu"]
    if torch.cuda.is_available():
        devices.append("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        devices.append("mps")
    if device := os.getenv("ACCELERATOR"):
        devices.append(device)
    model_paths = _list_model_paths()
    print(f"Found {len(model_paths)} model paths")
    if os.getenv("USE_CANARY_MODELS"):
        canary_paths = _list_canary_model_paths()
        print(f"Found {len(canary_paths)} canary model paths")
        model_paths.extend(canary_paths)

    if not model_paths:
        print("WARNING: No model paths found, no tests will be run!")
    if os.getenv("USE_CANARY_MODELS"):
        model_paths.extend(_list_canary_model_paths())
    if hasattr(torch, "hpu") and torch.hpu.is_available():
        devices.append("hpu")
    for path in model_paths:
        # TODO: skipping quantized tests for now due to BC-breaking changes for prepare
        # api, enable after PyTorch 1.13 release
        if "quantized" in path:
            continue
        for device in devices:
            _load_test(path, device)


_load_tests()
if __name__ == "__main__":
    # Pass unknown arguments to unittest
    sys.argv[1:] = unknown
    unittest.main()
