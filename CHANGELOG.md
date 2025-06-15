# Changelog

## [0.3.0] - XXXX-XX-XX

### Added

- Added commands to the bot. DM the bot `!help` to see what is possible.
- Add platform tracking. It will be read from `activity.platform` or you can set it manually. Default will be "pc", and retroactively set.
- Added image fields for games. This will be grabbed from Discord activity if present.
- Added `steam_id` field for Games. For now it is only used to acquire images.
- Sessions shorter than 30 seconds are discarded

## [0.2.0] - 2025-04-23

### Added

- Parse game names out of activity details reported by "Discord Status" Decky plugin on Steam Deck

## [0.1.0] - 2025-01-18

- Initial release
