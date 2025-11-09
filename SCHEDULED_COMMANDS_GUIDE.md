# Scheduled Commands Implementation Guide

## Overview

This guide explains how to implement persistent scheduled commands in KiloBuddy, allowing users to automate tasks that run at specific times even after the application restarts.

## Architecture

### Storage Approach

The recommended approach uses a JSON file to store scheduled commands persistently:

```
~/.kilobuddy/scheduled_commands.json  (Linux/macOS)
%APPDATA%\KiloBuddy\scheduled_commands.json  (Windows)
```

### Data Structure

```json
{
  "scheduled_commands": [
    {
      "id": "unique-id-1",
      "name": "Daily Backup",
      "command": "tar -czf ~/backup.tar.gz ~/Documents",
      "schedule": {
        "type": "cron",
        "expression": "0 2 * * *"
      },
      "enabled": true,
      "created": "2024-01-15T10:30:00Z",
      "last_run": "2024-01-16T02:00:00Z",
      "next_run": "2024-01-17T02:00:00Z"
    },
    {
      "id": "unique-id-2",
      "name": "System Update Check",
      "command": "sudo apt update",
      "schedule": {
        "type": "interval",
        "hours": 24
      },
      "enabled": true,
      "created": "2024-01-15T11:00:00Z",
      "last_run": null,
      "next_run": "2024-01-16T11:00:00Z"
    }
  ]
}
```

## Implementation Steps

### 1. Add Scheduled Commands Manager

Create a new class in `KiloBuddy.py`:

```python
import json
import uuid
from datetime import datetime, timedelta
from croniter import croniter  # pip install croniter

class ScheduledCommandsManager:
    def __init__(self):
        self.commands_file = get_source_path("scheduled_commands.json")
        self.scheduled_commands = self.load_commands()
    
    def load_commands(self):
        """Load scheduled commands from JSON file"""
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r') as f:
                    data = json.load(f)
                    return data.get("scheduled_commands", [])
        except Exception as e:
            print(f"ERROR: Failed to load scheduled commands: {e}")
        return []
    
    def save_commands(self):
        """Save scheduled commands to JSON file"""
        try:
            data = {"scheduled_commands": self.scheduled_commands}
            with open(self.commands_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"ERROR: Failed to save scheduled commands: {e}")
            return False
    
    def add_command(self, name, command, schedule_type, schedule_value):
        """Add a new scheduled command
        
        Args:
            name: Human-readable name for the command
            command: The actual command to execute
            schedule_type: 'cron' or 'interval'
            schedule_value: Cron expression or interval in hours
        """
        cmd_id = str(uuid.uuid4())
        
        scheduled_cmd = {
            "id": cmd_id,
            "name": name,
            "command": command,
            "schedule": {
                "type": schedule_type,
                "expression": schedule_value if schedule_type == "cron" else None,
                "hours": schedule_value if schedule_type == "interval" else None
            },
            "enabled": True,
            "created": datetime.now().isoformat(),
            "last_run": None,
            "next_run": self._calculate_next_run(schedule_type, schedule_value)
        }
        
        self.scheduled_commands.append(scheduled_cmd)
        self.save_commands()
        return cmd_id
    
    def _calculate_next_run(self, schedule_type, schedule_value):
        """Calculate the next run time for a scheduled command"""
        now = datetime.now()
        
        if schedule_type == "cron":
            # Use croniter to calculate next run from cron expression
            cron = croniter(schedule_value, now)
            next_run = cron.get_next(datetime)
            return next_run.isoformat()
        elif schedule_type == "interval":
            # Calculate next run based on interval in hours
            next_run = now + timedelta(hours=schedule_value)
            return next_run.isoformat()
        
        return None
    
    def remove_command(self, cmd_id):
        """Remove a scheduled command by ID"""
        self.scheduled_commands = [
            cmd for cmd in self.scheduled_commands 
            if cmd["id"] != cmd_id
        ]
        return self.save_commands()
    
    def enable_command(self, cmd_id, enabled=True):
        """Enable or disable a scheduled command"""
        for cmd in self.scheduled_commands:
            if cmd["id"] == cmd_id:
                cmd["enabled"] = enabled
                return self.save_commands()
        return False
    
    def get_due_commands(self):
        """Get commands that are due to run"""
        now = datetime.now()
        due_commands = []
        
        for cmd in self.scheduled_commands:
            if not cmd["enabled"]:
                continue
            
            next_run_str = cmd.get("next_run")
            if not next_run_str:
                continue
            
            try:
                next_run = datetime.fromisoformat(next_run_str)
                if next_run <= now:
                    due_commands.append(cmd)
            except Exception as e:
                print(f"ERROR: Invalid next_run time for command {cmd['id']}: {e}")
        
        return due_commands
    
    def mark_command_run(self, cmd_id):
        """Mark a command as run and calculate next run time"""
        for cmd in self.scheduled_commands:
            if cmd["id"] == cmd_id:
                cmd["last_run"] = datetime.now().isoformat()
                
                schedule_type = cmd["schedule"]["type"]
                if schedule_type == "cron":
                    schedule_value = cmd["schedule"]["expression"]
                elif schedule_type == "interval":
                    schedule_value = cmd["schedule"]["hours"]
                else:
                    continue
                
                cmd["next_run"] = self._calculate_next_run(schedule_type, schedule_value)
                self.save_commands()
                break
    
    def list_commands(self):
        """List all scheduled commands"""
        return self.scheduled_commands
```

### 2. Add Background Scheduler Thread

Add a background thread that checks for due commands:

```python
import threading
import time

# Global scheduler manager
scheduler_manager = None

def start_scheduler():
    """Start the background scheduler thread"""
    global scheduler_manager
    scheduler_manager = ScheduledCommandsManager()
    
    def scheduler_loop():
        while True:
            try:
                # Check every minute for due commands
                due_commands = scheduler_manager.get_due_commands()
                
                for cmd in due_commands:
                    print(f"INFO: Running scheduled command: {cmd['name']}")
                    
                    # Execute the command
                    user_call(cmd["command"])
                    
                    # Mark as run and calculate next run time
                    scheduler_manager.mark_command_run(cmd["id"])
                    
            except Exception as e:
                print(f"ERROR: Scheduler error: {e}")
            
            # Sleep for 60 seconds before checking again
            time.sleep(60)
    
    # Start the scheduler thread as daemon
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    print("INFO: Background scheduler started")
```

### 3. Add Dashboard Integration

Add a new tab to the dashboard for managing scheduled commands:

```python
def setup_scheduled_commands_tab(self):
    """Add scheduled commands management tab to dashboard"""
    
    # Create scheduled commands frame
    scheduled_frame = ctk.CTkFrame(self.root, fg_color=self.frame_color, corner_radius=15)
    
    # Header
    header = ctk.CTkLabel(scheduled_frame, text="Scheduled Commands", 
                         font=ctk.CTkFont(size=self.header_font_size, weight="bold"),
                         text_color="white")
    header.pack(pady=20)
    
    # List of scheduled commands
    self.scheduled_list = ctk.CTkTextbox(scheduled_frame, 
                                         font=ctk.CTkFont(size=14),
                                         fg_color=self.background_color,
                                         text_color="white",
                                         height=300)
    self.scheduled_list.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Button frame
    button_frame = ctk.CTkFrame(scheduled_frame, fg_color="transparent")
    button_frame.pack(fill="x", padx=20, pady=10)
    
    # Add command button
    add_btn = ctk.CTkButton(button_frame, text="Add Scheduled Command",
                           command=self.show_add_scheduled_command_dialog,
                           fg_color="#4CAF50", hover_color="#45a049")
    add_btn.pack(side="left", padx=5)
    
    # Refresh button
    refresh_btn = ctk.CTkButton(button_frame, text="Refresh",
                               command=self.refresh_scheduled_commands,
                               fg_color="#2196F3", hover_color="#1976D2")
    refresh_btn.pack(side="left", padx=5)
    
    # Initial load
    self.refresh_scheduled_commands()
    
    return scheduled_frame

def refresh_scheduled_commands(self):
    """Refresh the list of scheduled commands"""
    global scheduler_manager
    
    self.scheduled_list.delete("0.0", "end")
    
    commands = scheduler_manager.list_commands()
    
    if not commands:
        self.scheduled_list.insert("0.0", "No scheduled commands yet.\n\nClick 'Add Scheduled Command' to create one.")
        return
    
    for cmd in commands:
        status = "✓ Enabled" if cmd["enabled"] else "✗ Disabled"
        next_run = cmd.get("next_run", "Not scheduled")
        
        text = f"[{status}] {cmd['name']}\n"
        text += f"  Command: {cmd['command']}\n"
        text += f"  Next Run: {next_run}\n"
        text += f"  ID: {cmd['id']}\n\n"
        
        self.scheduled_list.insert("end", text)
```

### 4. Initialize in Main

Update the `main()` function to start the scheduler:

```python
def main():
    if not initialize():
        print("FATAL: Failed to initialize KiloBuddy. Exiting.\nFATAL 2")
        return
    
    # Start the background scheduler
    start_scheduler()
    
    print(f"INFO: KiloBuddy successfully started. Say '{WAKE_WORD}' followed by your command.")
    
    try:
        while True:
            if listen_for_wake_word():
                command = listen_for_command()
                if command:
                    process_command(command)
                print("INFO: Returning to wake word listening...")
    except KeyboardInterrupt:
        print("\nINFO: KiloBuddy Shutting Down...")
    finally:
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
```

## System Scheduler Integration (Alternative Approach)

For more reliable execution, especially after system reboots, integrate with the OS scheduler:

### Linux (cron)

```python
def add_to_cron(command, schedule):
    """Add command to user's crontab"""
    from crontab import CronTab
    
    # Get user's crontab
    cron = CronTab(user=True)
    
    # Create new job
    job = cron.new(command=command)
    job.setall(schedule)
    job.enable()
    
    # Write to crontab
    cron.write()
    
    return job
```

### Windows (Task Scheduler)

```python
def add_to_task_scheduler(name, command, schedule):
    """Add command to Windows Task Scheduler"""
    import win32com.client
    
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    
    root_folder = scheduler.GetFolder('\\')
    task_def = scheduler.NewTask(0)
    
    # Set trigger (schedule)
    triggers = task_def.Triggers
    trigger = triggers.Create(2)  # Daily trigger
    trigger.StartBoundary = schedule
    trigger.Enabled = True
    
    # Set action (command)
    actions = task_def.Actions
    action = actions.Create(0)  # Execute action
    action.Path = 'cmd.exe'
    action.Arguments = f'/c {command}'
    
    # Register task
    root_folder.RegisterTaskDefinition(
        name,
        task_def,
        6,  # TASK_CREATE_OR_UPDATE
        None,  # User
        None,  # Password
        3  # TASK_LOGON_INTERACTIVE_TOKEN
    )
```

### macOS (launchd)

```python
def add_to_launchd(name, command, schedule):
    """Add command to macOS launchd"""
    plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.kilobuddy.{name}.plist")
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kilobuddy.{name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/sh</string>
        <string>-c</string>
        <string>{command}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{schedule['hour']}</integer>
        <key>Minute</key>
        <integer>{schedule['minute']}</integer>
    </dict>
</dict>
</plist>
"""
    
    with open(plist_path, 'w') as f:
        f.write(plist_content)
    
    # Load the job
    subprocess.run(['launchctl', 'load', plist_path])
```

## Usage Examples

### Via Voice Command

User says: "Computer, schedule a backup of my documents every day at 2 AM"

The AI would generate a task list:
```
>>
[1] Add scheduled command: tar -czf ~/backup.tar.gz ~/Documents at 0 2 * * * # GEMINI --- DO NEXT
<<
```

### Via Dashboard

1. Click "Add Scheduled Command"
2. Enter command name: "Daily Backup"
3. Enter command: `tar -czf ~/backup.tar.gz ~/Documents`
4. Select schedule type: "Cron"
5. Enter cron expression: `0 2 * * *`
6. Click "Save"

## Cron Expression Reference

Common cron patterns for scheduled commands:

```
* * * * *        - Every minute
0 * * * *        - Every hour
0 2 * * *        - Every day at 2 AM
0 2 * * 0        - Every Sunday at 2 AM
0 2 1 * *        - First day of every month at 2 AM
*/15 * * * *     - Every 15 minutes
0 9-17 * * 1-5   - Every hour from 9 AM to 5 PM, Monday to Friday
```

Format: `minute hour day month day_of_week`

## Dependencies

Add these to the installer:

```python
REQUIRED_PACKAGES = [
    # ... existing packages ...
    "croniter",      # For parsing cron expressions
    "python-crontab" # For Linux cron integration (optional)
]
```

## Security Considerations

1. **Validate commands** before scheduling
2. **Require confirmation** for dangerous scheduled commands
3. **Log all scheduled executions** for audit trail
4. **Limit number** of scheduled commands per user (e.g., max 50)
5. **Sandbox execution** of scheduled commands when possible

## Testing

Test the scheduled commands feature:

```python
# Test adding a command
scheduler = ScheduledCommandsManager()
cmd_id = scheduler.add_command(
    name="Test Command",
    command="echo 'Hello World'",
    schedule_type="interval",
    schedule_value=1  # Every hour
)

# Test listing commands
commands = scheduler.list_commands()
assert len(commands) == 1

# Test getting due commands
due = scheduler.get_due_commands()

# Test removing command
scheduler.remove_command(cmd_id)
```

## Future Enhancements

1. **Command chaining**: Run multiple commands in sequence
2. **Conditional execution**: Only run if certain conditions are met
3. **Notifications**: Alert user when scheduled commands complete/fail
4. **Remote scheduling**: Schedule commands from mobile app
5. **Command templates**: Pre-defined command templates for common tasks
6. **Execution history**: Track success/failure of scheduled runs
7. **Retry logic**: Automatically retry failed commands

## Conclusion

This implementation provides a robust foundation for persistent scheduled commands in KiloBuddy. The JSON-based storage ensures commands persist across restarts, while the background scheduler thread or OS integration ensures reliable execution.

Choose the approach based on your needs:
- **Background thread**: Simpler, cross-platform, requires KiloBuddy running
- **OS scheduler**: More reliable, works even when app is closed, platform-specific code
