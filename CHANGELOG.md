# Changelog

## [0.3.0] - 2025-06-09

### Added

- Added bot dm functionality:
    - `!add "game name" n` - would add n seconds to the specified game 
        - This is useful if you played a game offline
    - `!start "game name"` - manually start playing a game
        - This is useful for platforms without Discord integration (Nintendo Switch...)
    - `!stop` - stops the manually playing game
    - `!remove id` - removes session with id
        - ID can be seen in recent activity on your profile page for now
    - `!merge 1 2` - merges game with id 1 into id 2 for your user
        - This is useful if you play a game with many names, or you typo when starting a manual session

    

## [0.2.0] - 2025-04-23

### Added

- Parse game names out of activity details reported by "Discord Status" Decky plugin on Steam Deck

## [0.1.0] - 2025-01-18

- Initial release
