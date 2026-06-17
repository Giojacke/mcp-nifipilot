# Example: Monitor Running Flows

## Prompt
"Check the current state of all my NiFi flows. Tell me if there
are any queues backing up, processors with errors, or anything
that needs attention."

## What the agent does
1. get_system_diagnostics → heap, CPU, uptime
2. get_process_groups → list all groups
3. get_flow_status (each group) → running/stopped/invalid counts
4. get_connections (each group) → queue depths
5. Report findings with health indicators

## Expected result
A complete health report of all NiFi flows.
