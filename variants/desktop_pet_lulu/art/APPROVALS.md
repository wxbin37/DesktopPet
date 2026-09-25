# Lulu art approvals

- Character approved on 2026-09-20: original round candidate v2, stored as `lulu-approved.png`; the taller v3 was rejected by the user.
- Eight-frame walking preview approved on 2026-09-20: “可以的继续”. Stored as `walking_sprite_sheet_alpha.png`.
- Other poses and typing scenes generated after these approvals using built-in image_gen.
- User-supplied reference screenshots are not included in this repository. Only generated art is tracked here.
- Sprite extraction uses the existing connected-alpha analysis, shared scale and foot-anchor pipeline. Walking leg shapes are independently drawn poses, not whole-image scaling or wobble.

- 2026-09-21 walking fix requested by user: preserve approved pose sheet and all limb shapes; register output frames horizontally to the head, without per-frame scale changes. Runtime stops at boundaries instead of bouncing.

- 2026-09-25: user explicitly requested additional actions derived from all six uploaded reference pictures, beyond the original repository states. Added clasping/rubbing hands, laughing, pullups, belly-down loaf, upward gaze and tongue-out animations using the previously approved character. No replacement character or walking cycle was generated.
