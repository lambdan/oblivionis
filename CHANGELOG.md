# Changelog

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
