import cv2


class MIDINoteGrid:
    def __init__(self):
        # Define standard tuning for a guitar (E A D G B e)
        self.standard_tuning = [40, 45, 50, 55, 59, 64]
        self.tuning = self.standard_tuning[:]
        self.columns = 13
        self.octave_shift = 0  # Track octave transposition
        self.semitone_shift = 0  # Track semitone transposition
        self.scale_modes = ["Major", "Minor",
                            "Minor Pentatonic", "Major Pentatonic", "Chromatic"]
        self.current_scale_index = None  # None means no scale mode is applied
        self.grid = self.generate_grid()

    def generate_grid(self):
        """Generates a 6x13 grid of MIDI notes based on the current tuning."""
        grid = []
        for i, string_note in enumerate(self.tuning):
            # Adjust the root for transposition settings
            adjusted_root = string_note + self.octave_shift * 12 + self.semitone_shift
            if self.current_scale_index is None:
                row = [adjusted_root + fret for fret in range(self.columns)]
            else:
                row = self.generate_scale_row(
                    adjusted_root, self.scale_modes[self.current_scale_index])
            grid.append(row)
        # Reverse grid so lower-pitched strings are at the bottom
        return grid[::-1]

    def generate_scale_row(self, root_note, scale_type):
        """Generates a row of notes in a specific scale starting from a root note."""
        scales = {
            "Major": [0, 2, 4, 5, 7, 9, 11],
            "Minor": [0, 2, 3, 5, 7, 8, 10],
            "Minor Pentatonic": [0, 3, 5, 7, 10],
            "Major Pentatonic": [0, 2, 4, 7, 9],
            "Chromatic": list(range(12))
        }
        intervals = scales[scale_type]
        row = [(root_note + intervals[i % len(intervals)] + (i // len(intervals)) * 12)
               for i in range(self.columns)]
        return row

    def midi_to_note_name(self, midi_number, include_octave=True):
        """Converts a MIDI note number to a note name."""
        note_names = ['C ', 'C#', 'D ', 'D#', 'E ',
                      'F ', 'F#', 'G ', 'G#', 'A ', 'A#', 'B ']
        note = note_names[midi_number % 12]
        if include_octave:
            octave = (midi_number // 12) - 1
            return f"{note}{octave}"
        return note

    def transpose_octave(self, direction):
        """Transposes all notes up or down by one octave."""
        self.octave_shift += 1 if direction == 'up' else -1
        self.grid = self.generate_grid()

    def transpose_semitone(self, direction):
        """Transposes all notes up or down by one semitone."""
        self.semitone_shift += 1 if direction == 'up' else -1
        self.grid = self.generate_grid()

    def set_drop_d_tuning(self):
        """Sets the tuning to drop D (D A D G B e)."""
        self.tuning = [38, 45, 50, 55, 59, 64]
        self.grid = self.generate_grid()

    def set_perfect_fourths_tuning(self):
        """Sets the tuning to all perfect fourths (E A D G C F)."""
        self.tuning = [40, 45, 50, 55, 60, 65]
        self.grid = self.generate_grid()

    def set_standard_tuning(self):
        """Resets to standard guitar tuning, ignoring all adjustments."""
        self.tuning = self.standard_tuning[:]
        self.current_scale_index = None  # Clear scale mode
        self.octave_shift = 0
        self.semitone_shift = 0
        self.grid = self.generate_grid()

    def cycle_scale_mode(self):
        """Cycles through available scale modes."""
        if self.current_scale_index is None:
            self.current_scale_index = 0
        else:
            self.current_scale_index = (
                self.current_scale_index + 1) % len(self.scale_modes)
        self.grid = self.generate_grid()

    def tuning_name(self):
        """Returns the name of the current tuning and its note names without octave numbers."""
        if self.tuning == self.standard_tuning:
            tuning_name = "Standard Tuning"
        elif self.tuning == [38, 45, 50, 55, 59, 64]:
            tuning_name = "Drop D Tuning"
        elif self.tuning == [40, 45, 50, 55, 60, 65]:
            tuning_name = "Perfect Fourths Tuning"
        else:
            tuning_name = "Custom Tuning"
        tuning_notes = [self.midi_to_note_name(
            note, include_octave=False) for note in self.tuning]
        return f"{tuning_name} ({', '.join(tuning_notes)})"

    def current_state(self):
        """Returns a string of the current tuning, octave, transpose, scale mode, and root note."""
        scale_mode = self.scale_modes[self.current_scale_index] if self.current_scale_index is not None else "None"
        root_note = self.midi_to_note_name(
            self.tuning[0] + self.octave_shift * 12 + self.semitone_shift, include_octave=False)
        return (f"\nTuning: {self.tuning_name()}\n"
                f"Octave: {self.octave_shift}\t"
                f"Semitone: {self.semitone_shift}\n"
                f"Scale: {scale_mode}\t"
                f"Root Note: {root_note}")

    def get_note_at_position(self, row, col):
        """Returns the MIDI note at a specific row and column in the grid."""
        if 0 <= row < len(self.grid) and 0 <= col < self.columns:
            return self.grid[row][col]
        else:
            raise IndexError("Row or column out of range")

    def __str__(self):
        """Returns a string representation of the note grid with note names for debugging."""
        grid_str = "\n".join(
            ["\t".join(self.midi_to_note_name(note) for note in row)
             for row in self.grid]
        )
        return f"{self.current_state()}\n\n{grid_str}"


# For testing purposes
if __name__ == "__main__":
    note_grid = MIDINoteGrid()
    print(f"\n\nInitial MIDI Note Grid in Standard Tuning:")

    # Initialize OpenCV window to listen for key inputs
    cv2.namedWindow("MIDI Note Grid")
    while True:
        # Display the note grid in the console
        print(note_grid)

        # Wait for a key press
        key = cv2.waitKey(0) & 0xFF

        # Handle key press for different functionalities
        if key == ord('z'):       # Lower by one octave
            note_grid.transpose_octave('down')
        elif key == ord('x'):     # Raise by one octave
            note_grid.transpose_octave('up')
        elif key == ord('c'):     # Lower by one semitone
            note_grid.transpose_semitone('down')
        elif key == ord('v'):     # Raise by one semitone
            note_grid.transpose_semitone('up')
        elif key == ord('d'):     # Drop D tuning
            note_grid.set_drop_d_tuning()
        elif key == ord('f'):     # Perfect fourths tuning
            note_grid.set_perfect_fourths_tuning()
        elif key == ord('s'):     # Cycle through scale modes
            note_grid.cycle_scale_mode()
        elif key == ord('a'):     # Standard tuning as reference point
            note_grid.set_standard_tuning()
        elif key == ord('q'):     # Quit program
            break
        else:
            print(
                "Invalid key. Use 'z', 'x', 'c', 'v', 'd', 'f', 's', 'a', or 'q' to quit.")

        # Clear the console for a cleaner view each time
        print("\033[H\033[J")  # ANSI escape code to clear terminal screen

    # Close OpenCV window
    cv2.destroyAllWindows()
