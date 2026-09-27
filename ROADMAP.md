# FeastPick roadmap

Features land here first, run **locally** for family testing, then ship in a versioned release when you say go.

## Shipped in 1.2.0

### Event colour themes
Per-event palettes so the board matches the occasion.

| Theme | Id |
|-------|-----|
| Classic feast | `classic` |
| Christmas | `christmas` |
| Halloween | `halloween` |
| Easter | `easter` |
| Thanksgiving | `thanksgiving` |
| New Year | `newyear` |
| Valentine | `valentine` |
| Summer picnic | `summer` |

- Choose theme when creating a feast only (locked after create)
- Christmas demo defaults to the Christmas theme

### Print + share
- **Print**: selections, votes, who chose, who brings what
- **Share**: copy board link + toast

### Create UX
- Random title + Shuffle
- Default date: today

## Ideas (not started)

- Edit dietary badges after an item is added
- Vote deadline / lock board
- Optional PIN or simple rate limits for public hosts
- Custom theme colours (beyond presets)
- Export CSV of bring list

## Release policy

1. Build and run with Docker Compose on LAN
2. You try the board and give **go**
3. Only then: bump `VERSION`, `CHANGELOG`, tag, GitHub Release + GHCR
