# ForgeLLM Hardware Laboratory Checklist

## Before changing a machine

- identify owner and permitted downtime;
- back up current driver/toolkit/package manifests;
- record BIOS/firmware, secure-boot and kernel constraints;
- record physical topology and power/cooling limits;
- confirm whether the machine may host a self-hosted runner;
- define rollback procedure.

## Before a benchmark

- clean Git worktree and immutable commits;
- capture inventory JSON;
- capture container digest and model revision;
- stop unrelated workloads or record them;
- record power mode, clocks and persistence settings without changing them silently;
- warm up to a stable state;
- validate correctness on a small case;
- randomize or interleave baseline/candidate order when drift matters;
- capture raw samples and profiler traces;
- monitor temperature, throttling, ECC/errors and memory pressure.

## After a benchmark

- hash artifacts;
- validate result schema;
- restore temporary clock/power settings;
- record failures and discarded runs with reasons;
- have a reviewer reproduce the critical result;
- update claims only within the measured scope.
