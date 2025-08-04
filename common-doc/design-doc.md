# AI Agent Config Sync Tool - Design Document

## Overview

The AI Agent Config Sync Tool is a CLI application that synchronizes Claude Code and Gemini CLI configurations between local environments (Linux/Windows) and a remote server. The tool provides backup and restore functionality with built-in file protection and validation.

## Requirements

### Functional Requirements

- **CLI-only Configuration**: All parameters provided via command-line arguments, no configuration files
- **Dual Environment Support**: Handle both Linux and Windows environments (Windows via `/mnt/c/` path)
- **File Protection**: Use rsync's `--update` flag by default to prevent overwriting newer files
- **Source Validation**: Check source file existence, warn and skip if missing
- **Environment Selection**: Allow selection of CLAUDE.md and GEMINI.md from specific environments
- **Cross-environment Copying**: Copy selected environment files to alternate environment during backup

### Non-Functional Requirements

- **Packaging**: Distribute as executable using PyInstaller
- **Error Handling**: Graceful handling of missing files and network issues
- **Transparency**: Verbose output options for operation visibility
- **Performance**: Efficient rsync-based file transfers

## CLI Interface Design

### Main Command Structure

```bash
sync-ai-config <subcommand> [options]
```

### Subcommands

#### Backup Command
Upload local configurations to remote server:

```bash
sync-ai-config backup --remote-host <user@host> --remote-path <path> [options]
```

**Required Arguments:**
- `--remote-host <user@host>` - Remote server connection (e.g., `cxwudi@5.78.95.153`)
- `--remote-path <path>` - Remote directory path (e.g., `~/sync-files/ai-agents-related/`)

**Optional Flags:**
- `--include-windows` - Also backup Windows configs from `/mnt/c/`
- `--windows-user <username>` - Windows username (required with `--include-windows`)
- `--claude-env <linux|windows>` - CLAUDE.md environment to use as primary (default: linux)
- `--gemini-env <linux|windows>` - GEMINI.md environment to use as primary (default: linux)
- `--force` - Disable rsync `--update` mode, overwrite newer remote files
- `--dry-run` - Show operations without executing
- `--verbose` - Show detailed rsync output

#### Restore Command
Download configurations from remote server:

```bash
sync-ai-config restore --remote-host <user@host> --remote-path <path> [options]
```

**Required Arguments:**
- `--remote-host <user@host>` - Remote server connection
- `--remote-path <path>` - Remote directory path

**Optional Flags:**
- `--include-windows` - Also restore Windows configs to `/mnt/c/`
- `--windows-user <username>` - Windows username (required with `--include-windows`)
- `--force` - Disable rsync `--update` mode, overwrite newer local files
- `--dry-run` - Show operations without executing
- `--verbose` - Show detailed rsync output

## Architecture Design

### Class Structure

The application follows a service-oriented architecture with dependency injection:

```mermaid
classDiagram
    %% Main orchestrator
    class SyncService {
        -cli_parser: CliParser
        -config_repo: ConfigRepository
        -backup_service: BackupService
        -restore_service: RestoreService
        +run(args: List[str]) None
        +execute_backup() None
        +execute_restore() None
    }
    
    %% Command line parsing
    class CliParser {
        +parse_args(args: List[str]) ParsedConfig
        +validate_args(config: ParsedConfig) None
        -create_parser() ArgumentParser
    }
    
    %% Stateful configuration repository
    class ConfigRepository {
        +set_config(config: ParsedConfig) None
        +get_backup_paths() BackupPaths
        +get_restore_paths() RestorePaths
        +is_windows_backup_enabled() bool
        +get_remote_connection() RemoteConnection
    }
    
    %% Backup operations
    class BackupService {
        -config_repo: ConfigRepository
        -exec_service: ExecService
        -path_validator: PathValidator
        +backup_configs() None
        +backup_linux_configs() None
        +backup_windows_configs() None
    }
    
    %% Restore operations
    class RestoreService {
        -config_repo: ConfigRepository
        -exec_service: ExecService
        -path_validator: PathValidator
        +restore_configs() None
        +restore_linux_configs() None
        +restore_windows_configs() None
    }
    
    %% Common execution service
    class ExecService {
        +execute_rsync(source: str, dest: str, options: RsyncOptions) RsyncResult
        +copy_file(source: str, dest: str) None
        +check_file_exists(path: str) bool
    }
    
    %% Path validation service
    class PathValidator {
        -exec_service: ExecService
        +validate_source_exists(path: str) bool
        +validate_remote_connection(connection: RemoteConnection) bool
        +warn_if_missing(path: str) None
    }
    
    %% Relationships
    SyncService --> CliParser : uses
    SyncService --> ConfigRepository : uses  
    SyncService --> BackupService : uses
    SyncService --> RestoreService : uses
    
    BackupService --> ConfigRepository : uses
    BackupService --> ExecService : uses
    BackupService --> PathValidator : uses
    
    RestoreService --> ConfigRepository : uses
    RestoreService --> ExecService : uses
    RestoreService --> PathValidator : uses
    
    PathValidator --> ExecService : uses
```

### Key Design Patterns

1. **Service Orchestration**: `SyncService` coordinates parsing, configuration, and operation execution
2. **Repository Pattern**: `ConfigRepository` maintains stateful configuration as single source of truth
3. **Dependency Injection**: Clean separation via `di_module.py`, no DI imports in business logic
4. **Strategy Pattern**: Separate `BackupService` and `RestoreService` for operation-specific logic

## File Handling Specification

### File Paths

#### Linux Environment
- Claude JSON: `~/.claude.json`
- Claude MD: `~/.claude/CLAUDE.md`
- Gemini Settings: `~/.gemini/settings.json`
- Gemini MD: `~/.gemini/GEMINI.md`

#### Windows Environment (via Linux)
- Claude JSON: `/mnt/c/Users/{username}/.claude.json`
- Claude MD: `/mnt/c/Users/{username}/.claude/CLAUDE.md`
- Gemini Settings: `/mnt/c/Users/{username}/.gemini/settings.json`
- Gemini MD: `/mnt/c/Users/{username}/.gemini/GEMINI.md`

#### Remote Server Naming Convention
- `.claude.linux.json` / `.claude.windows.json`
- `CLAUDE.md` (primary environment selection)
- `gemini.settings.linux.json` / `gemini.settings.windows.json`
- `GEMINI.md` (primary environment selection)

### Rsync Configuration

#### Default Protection Mode
```bash
rsync -avz --update <source> <destination>
```

#### Force Mode (with --force flag)
```bash
rsync -avz <source> <destination>
```

**Rsync Flags:**
- `-a`: Archive mode (recursive, preserve permissions, timestamps, etc.)
- `-v`: Verbose output (when `--verbose` specified)
- `-z`: Compress during transfer
- `--update`: Skip files newer at destination (default behavior)

### Environment Selection Logic

#### Backup Behavior
1. **CLAUDE.md/GEMINI.md Selection**: Use `--claude-env`/`--gemini-env` to choose source environment
2. **Cross-environment Copy**: Copy selected MD file to alternate environment before backup
3. **Primary Upload**: Upload selected MD file as `CLAUDE.md`/`GEMINI.md` on remote server

#### Restore Behavior
1. **Primary Download**: Download `CLAUDE.md`/`GEMINI.md` from remote server
2. **Environment Distribution**: Restore to both Linux and Windows (if `--include-windows` specified)

## Error Handling

### Source File Validation
```python
def validate_source_exists(self, path: str) -> bool:
    """Validates that a source file exists.

    If the file does not exist, a warning is logged.

    Args:
        path: The path to the file to validate.

    Returns:
        True if the file exists, False otherwise.
    """
    if not self.exec_service.check_file_exists(path):
        logger.warning("Source file does not exist, skipping: %s", path)
        return False
    return True
```

### Error Scenarios
- **Missing Source Files**: Log warning, skip file, continue operation
- **Network Connectivity**: Fail with descriptive error message
- **Permission Issues**: Fail with permission error details
- **Invalid Arguments**: Fail fast with usage information

## Implementation Approach

### Development Phases

1. **Phase 1: Core CLI and Configuration**
   - Implement `CliParser` with argument validation
   - Create `ConfigRepository` for stateful configuration management
   - Set up dependency injection infrastructure

2. **Phase 2: File Operations**
   - Implement `ExecService` with rsync execution
   - Create `PathValidator` for file existence checks
   - Add comprehensive logging and error handling

3. **Phase 3: Business Logic Services**
   - Implement `BackupService` with environment selection logic
   - Implement `RestoreService` with file distribution
   - Add cross-environment file copying functionality

4. **Phase 4: Integration and Testing**
   - Integrate all services via `SyncService`
   - Add comprehensive unit tests (90%+ coverage)
   - Perform end-to-end testing with actual file operations

5. **Phase 5: Distribution**
   - Configure PyInstaller for executable creation
   - Test executable on target Linux environments
   - Create deployment documentation

### Testing Strategy

- **Unit Tests**: Mock external dependencies, test business logic isolation
- **Integration Tests**: Test service interactions with real file system
- **End-to-end Tests**: Full CLI workflow tests with temporary directories
- **Error Case Testing**: Comprehensive error scenario coverage

### Logging Strategy

```python
import logging

logger = logging.getLogger(__name__)

# Usage examples:
logger.info("Starting backup operation with %s files", file_count)
logger.warning("Source file does not exist: %s", source_path)
logger.error("Failed to connect to remote server: %s", error_message)
```

## Deployment

### PyInstaller Configuration
- **Single Executable**: Bundle all dependencies into one file
- **Cross-platform**: Target Linux x64 systems
- **Dependency Management**: Include all required Python packages
- **Entry Point**: `sync-ai-config` command

### Distribution Requirements
- **Python 3.8+**: Minimum Python version requirement
- **rsync**: Must be available on target Linux systems
- **SSH Access**: Configured SSH key-based authentication to remote server

## Security Considerations

- **SSH Key Authentication**: No password handling in application
- **Path Validation**: Prevent path traversal attacks
- **File Permissions**: Preserve original file permissions during sync
- **Error Information**: Avoid exposing sensitive paths in error messages

## Future Enhancements

- **Configuration Profiles**: Save frequently used remote server configurations
- **Incremental Backup**: Track and sync only changed files
- **Encryption**: Optional file encryption during transfer
- **GUI Interface**: Desktop application wrapper for CLI tool
- **Cloud Storage**: Support for cloud storage backends (AWS S3, Google Drive)