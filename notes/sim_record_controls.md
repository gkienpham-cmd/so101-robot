# gym-hil sim recording — quick reference

Launch (needs mjpython on macOS, Terminal must have Accessibility + Input Monitoring):

```bash
cd ~/robotics/lerobot && source .venv/bin/activate
mjpython -m lerobot.rl.gym_manipulator --config_path ~/Documents/so101-robot/configs/gym_hil_record.json
```

## Keyboard controls

| Key | Action |
|---|---|
| Arrow keys | Move gripper in X-Y plane |
| Left Shift | Move down (Z) |
| Right Shift | Move up (Z) |
| Left Ctrl | Close gripper |
| Right Ctrl | Open gripper |
| Enter | End episode as SUCCESS (saves) |
| Backspace | End episode as FAILURE (discards) |
| Space | Start/stop intervention (HIL-RL only) |
| Esc | Quit |

Notes:
- Click the MuJoCo window first so it has keyboard focus.
- The viewer window's look (wireframe toggles etc.) doesn't affect recording — data comes from offscreen 128×128 `front`/`wrist` cameras.
- Episode count/target lives in `configs/gym_hil_record.json` (`num_episodes_to_record`); bump it to record more. Recording again to the same repo_id appends locally — delete `~/.cache/huggingface/lerobot/gkienpham/sim_practice_dataset` first if you want a fresh start.
