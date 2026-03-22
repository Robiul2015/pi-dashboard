import asyncio
import datetime
import re

BUZZER_PIN = 12


class BuzzerService:
    def __init__(self):
        self._fired_today = set()
        self._last_reset_date = None
        self._interval_last_fired = {}
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUZZER_PIN, GPIO.OUT)
            self._available = True
        except Exception:
            self._available = False

    def _reset_if_new_day(self):
        today = datetime.date.today()
        if self._last_reset_date != today:
            self._fired_today.clear()
            self._last_reset_date = today

    async def beep(self, freq=1000, duration=0.2, repeat=3, gap=0.15):
        """Play a beep pattern."""
        if not self._available:
            return
        try:
            pwm = self.GPIO.PWM(BUZZER_PIN, freq)
            for i in range(repeat):
                pwm.start(50)
                await asyncio.sleep(duration)
                pwm.stop()
                if i < repeat - 1:
                    await asyncio.sleep(gap)
        except Exception:
            pass

    def _parse_interval(self, alarm_str):
        """Parse interval format like 'every 2h', 'every 30m', 'every 1h30m'.
        Returns total minutes or None if not an interval."""
        match = re.match(r'every\s+(?:(\d+)h)?(?:(\d+)m)?$', alarm_str.strip(), re.IGNORECASE)
        if not match or (not match.group(1) and not match.group(2)):
            return None
        hours = int(match.group(1) or 0)
        mins = int(match.group(2) or 0)
        return hours * 60 + mins

    async def _fire_alarm(self):
        """Two long beeps."""
        await self.beep(freq=1000, duration=1.0, repeat=1)
        await asyncio.sleep(0.5)
        await self.beep(freq=1000, duration=1.0, repeat=1)

    async def check_alarms(self, goals_with_alarms):
        """Check if any alarm should fire right now.

        Alarm format in Notion:
          - Fixed time: '08:30', '14:00'
          - Interval: 'every 2h', 'every 30m', 'every 1h30m'
        """
        self._reset_if_new_day()
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")

        for goal in goals_with_alarms:
            alarm_str = goal.get("alarm", "")
            name = goal.get("name", "")

            interval = self._parse_interval(alarm_str)

            if interval:
                # Interval-based alarm
                last = self._interval_last_fired.get(name)
                if last is None or (now - last).total_seconds() >= interval * 60:
                    self._interval_last_fired[name] = now
                    if last is not None:
                        await self._fire_alarm()
            else:
                # Fixed time alarm
                key = f"{name}@{alarm_str}"
                if alarm_str == current_time and key not in self._fired_today:
                    self._fired_today.add(key)
                    await self._fire_alarm()

    def cleanup(self):
        if self._available:
            try:
                self.GPIO.cleanup(BUZZER_PIN)
            except Exception:
                pass
