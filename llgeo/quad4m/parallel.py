import time
import multiprocessing as mproc

def sample_fun(sec):
    print('Sleeping for {:4.2f} second'.format(sec))
    time.sleep(sec)
    print('Done sleeping!')

start = time.perf_counter()

# Create the processes
processes = [mproc.Process(target = sample_fun, args = [1]) for _ in range(5)]

# Start processes
[p.start() for p in processes]

# Join the processes (wait until finish before conducting rest of script)
[p.join()  for p in processes]

finish = time.perf_counter()
tspent = round(finish-start, 2)

print('Finished in {:4.2f} second(s)'.format(tspent))