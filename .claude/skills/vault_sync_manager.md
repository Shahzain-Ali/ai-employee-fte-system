# Vault Sync Manager — Agent Skill

## Purpose
Manages bidirectional Git sync between Cloud and Local agents via GitHub.

## Sync Mechanism
- **Push**: gitwatch (event-based via inotifywait) — auto-commits and pushes on file change
- **Pull**: cron job every 3 minutes — `git pull --rebase origin main`

## Claim-by-Move Protocol
When multiple agents could process the same task:
1. Agent scans `Needs_Action/<domain>/` for unclaimed files
2. Agent MOVES file to `In_Progress/<agent>/` (atomic operation)
3. First agent to complete the move owns the task
4. If file already gone = other agent claimed it → skip

## Conflict Resolution
| File Type | Strategy | Rationale |
|-----------|----------|-----------|
| Task files in Needs_Action/ | Accept theirs | Claim-by-move resolves |
| Task files in In_Progress/ | Accept theirs | First mover owns it |
| Log files | Concatenate | Append-only logs |
| Updates/ files | Accept theirs | Unique timestamp names |
| Dashboard.md | Accept ours | Single-writer (Local) |

## Troubleshooting
- **Sync stuck**: Check `git status` in vault, resolve any conflicts
- **gitwatch not pushing**: Check inotifywait is running (`pgrep inotifywait`)
- **Cron not pulling**: Check `crontab -l` and `/var/log/git-pull.log`
- **GitHub unreachable**: Queue pushes, continue local work, retry on reconnect
