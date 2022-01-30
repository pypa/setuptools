def measure_startup_perf():
    # run by pytest_perf
    import subprocess
    import sys  # end warmup

    subprocess.check_call([sys.executable, '-c', 'pass'])
