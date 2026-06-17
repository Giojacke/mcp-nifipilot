# Example: Debug Backed-up Queues

## Prompt
"One of my NiFi connections has thousands of FlowFiles queued
and the pipeline seems stuck. Help me identify the problem
and fix it safely."

## What the agent does
1. get_flow_status → identify which group has issues
2. get_connections → find connections with high queue counts
3. get_queue_status → get exact count and size
4. get_processors → check if downstream processor is stopped/invalid
5. Report diagnosis and suggest fix
6. Wait for user confirmation before any action

## Expected result
Root cause identified with safe remediation steps.
