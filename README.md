# perf-class

This program allows to group the CPU time spent in functions as outputed by perf script into classes. Eg. if your application spend 3% of time in "sort_down", 5% "sort_up", 4% "sort_final", and you give a map like "sort: Sorting", this tool will summarize those as "Sorting 12%".

This program is intended as a preprocessor to show where, roughly, a CPU spend its time in various application. The result such as "Sorting : 12%, Computing : 23%" can be given to a pie chart, typically.

The map file, to describe the mapping, is simply a series of "regex : class", one by line. Each symbol will be matched against the regex, and upon match will be considered of the given class. The tool will start with the top of the stack trace, and if no match is found, re-try with the previous function in the stack, etc. This is needed, and explain why a simple script was not sufficient to achieve the purpose of this script as a lot of time spend in the kernel is in "raw_spin_lock" functions.
Only the calling functions of those generic hit points will allow to find the reason of the time spent there, and therefore allow a mapping to the class.

# Installation
This package can be installed with pip, for instance:
```bash
pip3 --user install perf-class
```

# Example
A result of perf script is providden in the "samples" folder, as well as a sample mapping file.

```
perf-class samples/perf.script --map samples/kernel.map --no-output-failed --min 0.1
```

Will map all symbols exported using "perf record -a -g ... | perf script" in samples/perf.script using the mapping in samples/kernel.map as follow:

```
Finished, matched 98.840972% of cycles
IO 82.277282
Routing 9.182298
Filtering 5.843719
Kernel 1.532659
```

The firstline is written to stderr, so one may pipe stdout of this program safely to recover the file, and use it to plot some nice graphs of how your system reduce some time spent in a group of functions.

Without the last two options, one would get :
```
Finished, matched 98.840972% of cycles
IO 83.242081
Routing 9.289971
Filtering 5.912243
Kernel 1.550632
native_write_msr 0.147001
__switch_to 0.105550
hrtimer_start_range_ns 0.065908
entry_SYSCALL_64_after_hwframe 0.065326
smpboot_thread_fn 0.050715
__nanosleep 0.050668
do_nanosleep 0.045614
sys_nanosleep 0.045609
worker_thread 0.035491
do_syscall_64 0.035475
timerqueue_add 0.035317
syscall_return_via_sysret 0.030425
nanosleep@plt 0.030420
entry_SYSCALL_64 0.030417
kthread_should_stop 0.030415
ReloadConfigThread 0.030098
hrtimer_nanosleep 0.025339
_copy_from_user 0.020287
clockevents_program_event 0.020284
process_one_work 0.020282
__switch_to_asm 0.020260
get_nohz_timer_target 0.015214
__hrtimer_init 0.015213
copy_user_generic_unrolled 0.015210
__pthread_disable_asynccancel 0.015200
tick_program_event 0.015194
get_timespec64 0.014544
ktime_get 0.010146
_raw_spin_unlock_irqrestore 0.010140
schedule 0.010137
enqueue_hrtimer 0.010134
rb_insert_color 0.010134
mwait_idle 0.009315
kthread_should_park 0.005075
put_pwq 0.005074
ksoftirqd_should_run 0.005074
igb_rd32 0.005074
User_IO 0.005074
__pthread_enable_asynccancel 0.005073
_raw_spin_lock_irqsave 0.005073
_cond_resched 0.005073
hrtimer_active 0.005073
__indirect_thunk_start 0.005072
hrtimer_try_to_cancel 0.005071
native_load_tls 0.005071
ret_from_intr 0.005071
read_tsc 0.005070
rcu_all_qs 0.005068
__softirqentry_text_start 0.005063
lapic_next_deadline 0.005061
```

See perf-class --help for other options
