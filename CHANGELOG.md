# Changelog

## [0.3.4] - 2025-06-10

### Added

- Added `!last` command
- `!add` can now take duration in a variety of formats, and an optional timestamp

## [0.3.3] - 2025-06-10

### Added

- Added `!moddate` command. Lets you retroactively change date of a session.

### Bug Fixes

- Timestamp functionality restored to 0.3.1, but with bug fixed.

## [0.3.2] - 2025-06-10

### Added

- Read platform from `activity.platform` if possible

### Bug Fixes

- Timestamp of session was not being updated. Reverted behavior

## [0.3.1] - 2025-06-09

### Added

- Added batch mode for set platform command


## [0.3.0] - 2025-06-09

### Added

- Added platform tracking
    - Default will be "pc", and retroactively set
- Sessions shorter than 60 seconds are discarded
- Added bot dm functionality. DM the bot `!help` to see details.
    - `!help`
    - `!add "Game Name" n`
    - `!start "Game Name"`
    - `!stop`
    - `!merge <game_id1> <game_id2>`
    - `!remove <session_id>`
    - `!platform`
    - `!platform <name>`
    - `!listplatforms` 
    - `!setplatform <session_id> <platform>` 
    

## [0.2.0] - 2025-04-23

### Added

- Parse game names out of activity details reported by "Discord Status" Decky plugin on Steam Deck

## [0.1.0] - 2025-01-18

- Initial release
