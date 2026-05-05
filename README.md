# Chore Tracker for Home Assistant

Track household chores with color-coded urgency, per-user check-offs, and undo. **One install — the Lovelace card is included automatically.**

## Features

- Color-coded status: green (on time), yellow (overdue), red (way overdue — past 2× frequency)
- Completions recorded as the currently logged-in HA user
- Undo any accidental check-off
- Add and delete chores directly from the card
- Data stored in HA's own storage — survives restarts, included in backups

## Installation via HACS

1. HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/somethingp/chore-tracker-integration`, category: **Integration**
3. Download **Chore Tracker** and restart HA
4. Settings → Devices & Services → + Add Integration → search **Chore Tracker**

The card resource is registered automatically. No separate card install needed.

## Manual installation

1. Copy `custom_components/chore_tracker/` into your HA `config/custom_components/` folder
2. Restart HA
3. Settings → Devices & Services → + Add Integration → search **Chore Tracker**

## Adding the card to a dashboard

Edit any dashboard → + Add Card → Manual, then paste:

```yaml
type: custom:chore-tracker-card
title: Chores
```

## How it works

The integration registers WebSocket commands (`chore_tracker/get_chores`, `add_chore`, `delete_chore`, `complete_chore`, `undo_chore`) that the card calls via `hass.connection.sendMessagePromise()` — the same mechanism HA's own frontend uses. No HTTP ports, no CORS, no auth issues. Data is stored in `.storage/chore_tracker_data`.

## License

MIT
