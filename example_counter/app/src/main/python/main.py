import stratum
from stratum.android.widget import LinearLayout, TextView, Button

# ── State ─────────────────────────────────────────────────────────────────────
count       = 0
best        = 0
tv_count    = None
tv_best     = None
tv_status   = None

# ── onCreate ──────────────────────────────────────────────────────────────────
def onCreate():
    global tv_count, tv_best, tv_status

    activity = stratum.getActivity()

    # Root layout — vertical
    root = stratum.create_android_widget_LinearLayout(activity)
    root.setOrientation(1)   # VERTICAL
    root.setPadding(48, 80, 48, 48)

    # ── Title ─────────────────────────────────────────────────────────────────
    tv_title = stratum.create_android_widget_TextView(activity)
    tv_title.setText("Stratum Counter")
    tv_title.setTextSize(28.0)
    tv_title.setGravity(17)          # CENTER
    root.addView(tv_title)

    # ── Spacer ────────────────────────────────────────────────────────────────
    spacer1 = stratum.create_android_widget_TextView(activity)
    spacer1.setText(" ")
    spacer1.setTextSize(12.0)
    root.addView(spacer1)

    # ── Counter display ───────────────────────────────────────────────────────
    tv_count = stratum.create_android_widget_TextView(activity)
    tv_count.setText("0")
    tv_count.setTextSize(72.0)
    tv_count.setGravity(17)          # CENTER
    root.addView(tv_count)

    # ── Best display ──────────────────────────────────────────────────────────
    tv_best = stratum.create_android_widget_TextView(activity)
    tv_best.setText("Best: 0")
    tv_best.setTextSize(16.0)
    tv_best.setGravity(17)           # CENTER
    root.addView(tv_best)

    # ── Status message ────────────────────────────────────────────────────────
    tv_status = stratum.create_android_widget_TextView(activity)
    tv_status.setText("Tap + to start counting!")
    tv_status.setTextSize(14.0)
    tv_status.setGravity(17)         # CENTER
    root.addView(tv_status)

    # ── Spacer ────────────────────────────────────────────────────────────────
    spacer2 = stratum.create_android_widget_TextView(activity)
    spacer2.setText(" ")
    spacer2.setTextSize(16.0)
    root.addView(spacer2)

    # ── Button row — horizontal ───────────────────────────────────────────────
    row = stratum.create_android_widget_LinearLayout(activity)
    row.setOrientation(0)            # HORIZONTAL
    row.setGravity(17)               # CENTER

    # ── Minus button ──────────────────────────────────────────────────────────
    btn_minus = stratum.create_android_widget_Button(activity)
    btn_minus.setText("  −  ")
    btn_minus.setTextSize(28.0)

    def on_minus(view):
        global count
        if count > 0:
            count -= 1
        _refresh()

    btn_minus.setOnClickListener(on_minus)
    row.addView(btn_minus)

    # ── Gap ───────────────────────────────────────────────────────────────────
    gap = stratum.create_android_widget_TextView(activity)
    gap.setText("   ")
    row.addView(gap)

    # ── Plus button ───────────────────────────────────────────────────────────
    btn_plus = stratum.create_android_widget_Button(activity)
    btn_plus.setText("  +  ")
    btn_plus.setTextSize(28.0)

    def on_plus(view):
        global count, best
        count += 1
        if count > best:
            best = count
        _refresh()

    btn_plus.setOnClickListener(on_plus)
    row.addView(btn_plus)

    root.addView(row)

    # ── Spacer ────────────────────────────────────────────────────────────────
    spacer3 = stratum.create_android_widget_TextView(activity)
    spacer3.setText(" ")
    spacer3.setTextSize(16.0)
    root.addView(spacer3)

    # ── Reset button ──────────────────────────────────────────────────────────
    btn_reset = stratum.create_android_widget_Button(activity)
    btn_reset.setText("Reset")
    btn_reset.setTextSize(16.0)

    def on_reset(view):
        global count
        count = 0
        _refresh(status="Counter reset.")

    btn_reset.setOnClickListener(on_reset)
    root.addView(btn_reset)

    # ── Render ────────────────────────────────────────────────────────────────
    stratum.setContentView(activity, root)
    print("Stratum: onCreate complete")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _refresh(status=None):
    """Update all display TextViews from current state."""
    if tv_count:
        tv_count.setText(str(count))
    if tv_best:
        tv_best.setText(f"Best: {best}")
    if tv_status and status:
        tv_status.setText(status)
    elif tv_status:
        if count == 0:
            tv_status.setText("Tap + to start counting!")
        elif count == best and count > 0:
            tv_status.setText(f"🎉 New best: {best}!")
        else:
            tv_status.setText(f"Keep going!")


# ── Lifecycle ─────────────────────────────────────────────────────────────────

def onResume():
    print("Stratum: onResume")

def onPause():
    print("Stratum: onPause — count paused at", count)

def onDestroy():
    print("Stratum: onDestroy — final count:", count, "best:", best)