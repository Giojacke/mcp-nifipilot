# Example: Create a Data Pipeline

## Prompt
"Create a process group called 'Log-Ingestion'. Inside, add a
GetFile processor reading from '/var/log/app', connect it to
UpdateAttribute to add a 'source' attribute with value 'app-logs',
then connect to PutFile writing to '/backup/logs'.
Use dry-run first, then execute if looks correct."

## What the agent does
1. get_system_diagnostics → verify NiFi is healthy
2. get_process_groups → check existing structure
3. create_process_group → create 'Log-Ingestion'
4. create_processor (GetFile) → x=200, y=200
5. create_processor (UpdateAttribute) → x=200, y=400
6. create_processor (PutFile) → x=200, y=600
7. create_connection → GetFile → UpdateAttribute
8. create_connection → UpdateAttribute → PutFile
9. get_processors → confirm all created
10. Report IDs and status

## Expected result
A complete 3-processor pipeline ready to start.
