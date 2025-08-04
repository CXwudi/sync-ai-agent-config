# AI Agent Config Sync Tool - Design Document

## Overview

A CLI tool for syncing Claude Code and Gemini CLI configurations between local environments (Linux/Windows) and remote servers. The tool provides backup and restore functionality with built-in file protection and cross-environment support.

## Requirements

### Functional Requirements
- **CLI-only configuration**: All parameters via command-line arguments, no config files
- **Two subcommands**: `backup` (upload) and `restore` (download)  
- **Cross-platform support**: Linux and Windows environments via `/mnt/c/`
- **File protection**: Use rsync's `--update` flag by default, `--force` to override
- **Source validation**: Check file existence, warn and skip if missing
- **Environment selection**: Choose between Linux/Windows versions of CLAUDE.md and GEMINI.md
- **Executable packaging**: Deploy via PyInstaller

### Non-Functional Requirements
- **Performance**: Leverage rsync for efficient file transfers
- **Reliability**: Comprehensive error handling and validation
- **Usability**: Clear CLI interface with verbose output options
- **Maintainability**: Clean architecture with dependency injection

## CLI Interface

### Main Command Structure
```bash
sync-ai-config <subcommand> [options]
```

### Backup Subcommand
```bash
sync-ai-config backup [options]
```

**Required Arguments:**
- `--remote-host <user@host>` - Remote server (e.g., `cxwudi@5.78.95.153`)
- `--remote-path <path>` - Remote directory path (e.g., `~/sync-files/ai-agents-related/`)

**Optional Flags:**
- `--include-windows` - Also backup Windows configs from `/mnt/c/`
- `--windows-user <username>` - Windows username (required if `--include-windows` used)
- `--claude-env <linux|windows>` - Which CLAUDE.md to use as primary (default: current env)
- `--gemini-env <linux|windows>` - Which GEMINI.md to use as primary (default: current env)
- `--force` - Disable rsync `--update` mode, overwrite newer remote files
- `--dry-run` - Show what would be synced without actually doing it
- `--verbose` - Show detailed rsync output

### Restore Subcommand
```bash
sync-ai-config restore [options]
```

**Required Arguments:**
- `--remote-host <user@host>` - Remote server
- `--remote-path <path>` - Remote directory path

**Optional Flags:**
- `--include-windows` - Also restore Windows configs to `/mnt/c/`
- `--windows-user <username>` - Windows username (required if `--include-windows` used)
- `--force` - Disable rsync `--update` mode, overwrite newer local files
- `--dry-run` - Show what would be restored without actually doing it
- `--verbose` - Show detailed rsync output

## File Handling Specification

### Path Mappings

#### Linux Environment
- **Claude JSON**: `~/.claude.json` ’ `remote:.claude.linux.json`
- **Claude MD**: `~/.claude/CLAUDE.md` ’ `remote:CLAUDE.md`
- **Gemini Settings**: `~/.gemini/settings.json` ’ `remote:gemini.settings.wsl.json`
- **Gemini MD**: `~/.gemini/GEMINI.md` ’ `remote:GEMINI.md`

#### Windows Environment (when `--include-windows`)
- **Claude JSON**: `/mnt/c/Users/{username}/.claude.json` ’ `remote:.claude.window.json`
- **Claude MD**: `/mnt/c/Users/{username}/.claude/CLAUDE.md`
- **Gemini Settings**: `/mnt/c/Users/{username}/.gemini/settings.json` ’ `remote:gemini.settings.window.json`
- **Gemini MD**: `/mnt/c/Users/{username}/.gemini/GEMINI.md`

### Environment Selection Logic

When backing up with `--include-windows`:
1. **CLAUDE.md**: Use `--claude-env` flag to select primary version, copy to other environment
2. **GEMINI.md**: Use `--gemini-env` flag to select primary version, copy to other environment
3. **JSON files**: Backup both environments independently

### Rsync Configuration

#### Default Mode (File Protection)
```bash
rsync -avz --update <source> <dest>
```
- `--archive`: Preserve permissions, timestamps, symlinks
- `--verbose`: Show transfer progress (when `--verbose` flag used)
- `--compress`: Compress during transfer
- `--update`: Skip files newer at destination

#### Force Mode
```bash
rsync -avz <source> <dest>
```
- Remove `--update` flag to allow overwriting newer files

## Class Architecture

### Service Classes

#### SyncService (Main Orchestrator)
- **Dependencies**: `CliParser`, `ConfigRepository`, `BackupService`, `RestoreService`
- **Responsibilities**:
  - Parse CLI arguments via `CliParser`
  - Configure `ConfigRepository` with parsed settings
  - Delegate to appropriate service based on subcommand
  - Handle top-level error scenarios

#### CliParser (Command Line Processing)
- **Dependencies**: None
- **Responsibilities**:
  - Define argument parser with subcommands and options
  - Validate required argument combinations
  - Return `ParsedConfig` data model
  - Handle CLI-specific error reporting

#### ConfigRepository (Stateful Configuration)
- **Dependencies**: None (receives `ParsedConfig` via setter)
- **Responsibilities**:
  - Store runtime configuration state
  - Generate path mappings for backup/restore operations
  - Resolve Windows user paths when enabled
  - Provide configuration queries to service classes

#### BackupService (Upload Operations)
- **Dependencies**: `ConfigRepository`, `ExecService`, `PathValidator`
- **Responsibilities**:
  - Execute Linux config backup operations
  - Execute Windows config backup operations (when enabled)
  - Handle CLAUDE.md/GEMINI.md environment selection and copying
  - Coordinate with `ExecService` for actual file transfers

#### RestoreService (Download Operations)
- **Dependencies**: `ConfigRepository`, `ExecService`, `PathValidator`
- **Responsibilities**:
  - Execute Linux config restore operations
  - Execute Windows config restore operations (when enabled)
  - Coordinate with `ExecService` for actual file transfers

### Utility Classes

#### ExecService (File Operations)
- **Dependencies**: None
- **Responsibilities**:
  - Execute rsync commands with proper options
  - Handle dry-run mode simulation
  - Copy files between environments (for MD file selection)
  - Check file existence
  - Log missing file warnings

#### PathValidator (Validation)
- **Dependencies**: None
- **Responsibilities**:
  - Validate source file existence
  - Validate remote connection accessibility
  - Generate appropriate warning messages
  - Skip operations for missing files

### Data Models

#### ParsedConfig
- Command line arguments in structured format
- Validation flags and user preferences

#### BackupPaths / RestorePaths
- Resolved file path mappings
- Environment-specific path configurations

#### RsyncOptions / RsyncResult
- Rsync command configuration and execution results

## Development Phases - Detailed Per-Class Implementation

### Phase 1: Core Infrastructure and Foundation

#### 1.1 Data Models and Configuration (Week 1)
**Classes to implement**: `ParsedConfig`, `BackupPaths`, `RestorePaths`, `RsyncOptions`, `RsyncResult`

**Implementation order**:
1. **ParsedConfig** - Define all CLI argument fields with proper typing
   - Required: `subcommand`, `remote_host`, `remote_path`
   - Optional: `include_windows`, `windows_user`, `claude_env`, `gemini_env`, `force`, `dry_run`, `verbose`
   - Add validation methods for argument combinations
   
2. **RsyncOptions** - Define rsync command configuration
   - Boolean flags: `archive`, `verbose`, `compress`, `update`, `dry_run`
   - Method to generate rsync command arguments list
   
3. **RsyncResult** - Define command execution results
   - Fields: `success`, `output`, `error`, `return_code`
   - Helper methods for success/failure checking
   
4. **BackupPaths** - Define backup path mappings
   - Linux paths: `linux_claude_json`, `linux_claude_md`, `linux_gemini_settings`, `linux_gemini_md`
   - Windows paths: `windows_claude_json`, `windows_claude_md`, `windows_gemini_settings`, `windows_gemini_md` (Optional)
   - Remote base path: `remote_base`
   
5. **RestorePaths** - Define restore path mappings  
   - Remote paths: `remote_claude_linux`, `remote_claude_md`, `remote_gemini_linux`, `remote_gemini_md`
   - Windows remote paths: `remote_claude_windows`, `remote_gemini_windows` (Optional)
   - Local base path: `local_base`

**Testing**: Unit tests for data model validation and path resolution

#### 1.2 Dependency Injection Setup (Week 1)
**Classes to implement**: `DIModule`, main function setup

**Implementation order**:
1. **DIModule** - Implement all provider methods
   - `@provider` methods for each service class
   - Proper dependency wiring according to architecture
   - No business logic, only object creation and wiring
   
2. **Main function** - Entry point setup
   - Initialize injector with `DIModule`
   - Get `SyncService` instance from injector
   - Pass command line arguments to service
   - Handle top-level exceptions

**Testing**: Integration tests for DI container setup and object creation

### Phase 2: Core Services Implementation

#### 2.1 CLI Parser Implementation (Week 2)
**Classes to implement**: `CliParser`

**Implementation order**:
1. **Argument Parser Setup**
   - Create main parser with subcommands
   - Add backup subcommand with all required/optional arguments
   - Add restore subcommand with all required/optional arguments
   
2. **Validation Logic**
   - Validate `--windows-user` required when `--include-windows` used
   - Validate `--claude-env` and `--gemini-env` values are 'linux' or 'windows'
   - Validate remote host format (basic regex check)
   
3. **Error Handling**
   - Clear error messages for invalid argument combinations
   - Help text formatting and examples
   - Return proper `ParsedConfig` object

**Testing**: Unit tests for all argument combinations, validation scenarios, and error cases

#### 2.2 Configuration Repository Implementation (Week 2)
**Classes to implement**: `ConfigRepository`

**Implementation order**:
1. **Configuration Storage**
   - `set_config()` method to store `ParsedConfig`
   - Internal state management
   
2. **Path Resolution Logic**
   - `get_backup_paths()` - resolve all backup source/destination paths
   - `get_restore_paths()` - resolve all restore source/destination paths
   - Windows path resolution using `windows_user` when enabled
   - Environment-specific path generation
   
3. **Configuration Queries**
   - `is_windows_backup_enabled()` - check windows backup flag
   - `get_remote_connection()` - return remote connection details
   - Path validation and normalization

**Testing**: Unit tests for path resolution with various configuration combinations

### Phase 3: Utility Services Implementation

#### 3.1 Path Validator Implementation (Week 3)
**Classes to implement**: `PathValidator`

**Implementation order**:
1. **File Existence Validation**
   - `validate_source_exists()` - check if source file exists
   - Handle both local and remote path checking
   - Proper error handling for permission issues
   
2. **Remote Connection Validation**
   - `validate_remote_connection()` - test SSH connectivity
   - Basic remote path accessibility check
   - Timeout handling for network issues
   
3. **Warning and Logging**
   - `warn_if_missing()` - generate appropriate warning messages
   - Integration with logging system
   - Graceful handling of missing files (skip, don't fail)

**Testing**: Unit tests for file validation, mock remote connections, error scenarios

#### 3.2 Execution Service Implementation (Week 3-4)
**Classes to implement**: `ExecService`

**Implementation order**:
1. **Rsync Command Building**
   - `build_rsync_command()` - private method to construct rsync arguments
   - Handle all rsync options based on `RsyncOptions`
   - Proper argument escaping and path handling
   
2. **Command Execution**
   - `execute_rsync()` - execute rsync with proper error handling
   - Capture stdout, stderr, and return codes
   - Return structured `RsyncResult` object
   - Handle dry-run mode simulation
   
3. **File Operations**
   - `copy_file()` - local file copying for environment selection
   - `check_file_exists()` - file existence checking
   - Error handling and logging integration
   
4. **Missing File Handling**
   - `log_missing_file_warning()` - warn about missing files
   - Skip operations gracefully without failing entire process

**Testing**: Integration tests with actual rsync commands, mock file systems, dry-run validation

### Phase 4: Business Logic Services Implementation

#### 4.1 Backup Service Implementation (Week 4-5)
**Classes to implement**: `BackupService`

**Implementation order**:
1. **Linux Config Backup**
   - `backup_linux_configs()` - backup all Linux configuration files
   - Handle Claude JSON, Claude MD, Gemini settings, Gemini MD
   - Use `PathValidator` to check source existence
   - Use `ExecService` for actual rsync operations
   
2. **Windows Config Backup** 
   - `backup_windows_configs()` - backup Windows configurations when enabled
   - Handle path resolution with Windows username
   - Same file types as Linux but from `/mnt/c/` paths
   
3. **Environment Selection Logic**
   - `handle_claude_md_selection()` - implement CLAUDE.md environment selection
   - `handle_gemini_md_selection()` - implement GEMINI.md environment selection
   - Copy selected MD file to other environment before backup
   - Handle cases where source environment file doesn't exist
   
4. **Main Backup Coordination**
   - `backup_configs()` - main entry point using `ConfigRepository`
   - Orchestrate Linux and Windows backup operations
   - Handle environment selection when Windows backup enabled
   - Proper error handling and operation reporting

**Testing**: Integration tests with mock file systems, various configuration scenarios

#### 4.2 Restore Service Implementation (Week 5)
**Classes to implement**: `RestoreService`

**Implementation order**:
1. **Linux Config Restore**
   - `restore_linux_configs()` - restore all Linux configuration files
   - Handle Claude JSON, Claude MD, Gemini settings, Gemini MD
   - Use `PathValidator` to check remote source existence
   - Use `ExecService` for actual rsync operations
   
2. **Windows Config Restore**
   - `restore_windows_configs()` - restore Windows configurations when enabled
   - Handle path resolution with Windows username
   - Restore to `/mnt/c/` paths
   
3. **Main Restore Coordination**
   - `restore_configs()` - main entry point using `ConfigRepository`
   - Orchestrate Linux and Windows restore operations
   - Proper error handling and operation reporting

**Testing**: Integration tests with mock remote systems, various configuration scenarios

### Phase 5: Main Service Integration and Testing

#### 5.1 Sync Service Implementation (Week 6)
**Classes to implement**: `SyncService`

**Implementation order**:
1. **CLI Processing Integration**
   - `run()` method - main entry point taking command line arguments
   - Use `CliParser` to parse arguments
   - Configure `ConfigRepository` with parsed configuration
   
2. **Service Delegation**
   - `execute_backup()` - delegate to `BackupService`
   - `execute_restore()` - delegate to `RestoreService`
   - Proper subcommand routing based on parsed configuration
   
3. **Error Handling and Logging**
   - Top-level exception handling
   - User-friendly error reporting
   - Integration with logging system
   - Exit code management

**Testing**: End-to-end integration tests, CLI testing with various argument combinations

#### 5.2 System Integration Testing (Week 6-7)
**Testing focus**:
1. **Full CLI Integration**
   - Test all CLI argument combinations
   - Test error scenarios and edge cases
   - Test dry-run functionality
   
2. **File System Integration**  
   - Test with real file systems (with proper mocking for CI)
   - Test Windows path handling on Linux systems
   - Test rsync integration with various scenarios
   
3. **Cross-Environment Testing**
   - Test Linux-only scenarios
   - Test Linux + Windows scenarios
   - Test environment selection logic
   
4. **Performance and Reliability**
   - Test with large configuration files
   - Test network timeout scenarios
   - Test partial failure scenarios

### Phase 6: Deployment and Documentation

#### 6.1 PyInstaller Packaging (Week 7)
**Implementation tasks**:
1. **Build Configuration**
   - Create PyInstaller spec file
   - Handle dependency packaging
   - Test executable on target Linux environments
   
2. **Distribution Preparation**
   - Create installation scripts
   - Document system requirements
   - Test deployment procedures

#### 6.2 Documentation and Final Testing (Week 7-8)
**Documentation tasks**:
1. **User Documentation**
   - CLI usage examples
   - Configuration scenarios
   - Troubleshooting guide
   
2. **Developer Documentation**
   - Architecture overview
   - Contributing guidelines
   - Testing procedures

**Final testing**:
1. **Regression Testing**
   - Full test suite execution
   - Performance benchmarking
   - Security review
   
2. **User Acceptance Testing**
   - End-user scenario testing
   - Documentation validation
   - Deployment verification

## Error Handling Strategy

### File System Errors
- **Missing source files**: Log warning, skip operation, continue with remaining files
- **Permission errors**: Log error, fail operation with clear message
- **Disk space issues**: Detect and fail early with helpful message

### Network Errors
- **Connection failures**: Retry logic with exponential backoff
- **Timeout handling**: Configurable timeout values
- **SSH key issues**: Clear error messages with troubleshooting steps

### Configuration Errors
- **Invalid arguments**: Immediate failure with usage help
- **Conflicting options**: Clear error messages explaining conflicts
- **Missing required args**: Help text showing required parameters

## Security Considerations

### SSH Key Management
- Rely on user's existing SSH configuration
- No storage of credentials within the application
- Support for SSH agent and key-based authentication

### File Permissions
- Preserve original file permissions during transfers
- Validate write permissions before operations
- Handle permission errors gracefully

### Input Validation
- Sanitize remote host and path inputs
- Validate file paths to prevent directory traversal
- Limit rsync options to safe subset

## Testing Strategy

### Unit Tests
- All service classes with mocked dependencies
- Data model validation and edge cases
- Path resolution logic with various inputs
- CLI argument parsing and validation

### Integration Tests
- File system operations with temporary directories
- Rsync command execution with mock servers
- Cross-service interactions
- Error scenario handling

### End-to-End Tests
- Full CLI workflows with test environments
- Real rsync operations with test servers
- Performance testing with large files
- Cross-platform compatibility testing

## Deployment

### PyInstaller Configuration
```python
# sync-ai-config.spec
a = Analysis(['src/syncer/main.py'],
             binaries=[],
             datas=[],
             excludes=[],
             noarchive=False)
```

### Distribution
- Single executable for Linux x64
- Installation via package managers (future)
- Docker container option (future)

### System Requirements
- Linux environment with WSL (for Windows support)
- Python 3.8+ (for PyInstaller build)
- rsync installed on system
- SSH client for remote connections

---

*This design document provides comprehensive guidance for implementing the AI Agent Config Sync Tool with clean architecture, robust error handling, and thorough testing coverage.*