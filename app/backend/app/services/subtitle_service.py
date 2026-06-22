"""Subtitle service — SRT formatting and storyboard-to-subtitle extraction (P2.2)."""
from app.models.video_generation_model import Storyboard, Subtitle, SubtitleEntry


class SubtitleService:
    """Generates and formats subtitles for video."""

    @staticmethod
    def from_storyboard(storyboard: Storyboard, language: str = "zh") -> Subtitle:
        """Extract subtitle entries from storyboard shots that have dialogue.

        Calculates cumulative timing based on shot durations.

        Args:
            storyboard: Storyboard with shots containing optional dialogue.
            language: Subtitle language code (default: "zh").

        Returns:
            Subtitle with entries for each shot that has non-empty dialogue.
        """
        entries = []
        cumulative_time = 0.0

        for shot in storyboard.shots:
            if shot.dialogue.strip():
                start = cumulative_time
                end = cumulative_time + shot.duration
                entries.append(SubtitleEntry(
                    start_time=start,
                    end_time=end,
                    text=shot.dialogue,
                ))
            cumulative_time += shot.duration

        return Subtitle(language=language, entries=entries)

    @staticmethod
    def to_srt(subtitle: Subtitle) -> str:
        """Convert a Subtitle to SRT file format.

        Args:
            subtitle: Subtitle with entries.

        Returns:
            SRT-formatted string.
        """
        lines = []
        for i, entry in enumerate(subtitle.entries, 1):
            lines.append(str(i))
            lines.append(
                f"{SubtitleService._format_time(entry.start_time)} --> "
                f"{SubtitleService._format_time(entry.end_time)}"
            )
            lines.append(entry.text)
            lines.append("")  # blank line separator
        return "\n".join(lines)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds to SRT timestamp: HH:MM:SS,mmm.

        Args:
            seconds: Time in seconds.

        Returns:
            SRT-compatible timestamp string.
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
