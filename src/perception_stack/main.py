import argparse
import numpy as np

def run_ci_smoke_test():
    print("Running CI smoke test...")

    # 模拟一张图
    dummy_image = np.zeros((720, 1280, 3), dtype=np.uint8)

    # 这里只验证 pipeline 能被 import
    from perception_stack.sync import dummy_sync

    print("CI smoke test passed.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci_mode", action="store_true")
    args = parser.parse_args()

    if args.ci_mode:
        run_ci_smoke_test()
    else:
        print("Normal mode (not implemented yet)")

if __name__ == "__main__":
    main()
