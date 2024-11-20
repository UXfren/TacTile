# midi_note_grid.py

class MIDINoteGrid:
    def __init__(self):
        # Define the MIDI note numbers for the open strings of a standard guitar tuning (E A D G B e)
        # Corresponds to E2, A2, D3, G3, B3, E4 in MIDI
        self.tuning = [40, 45, 50, 55, 59, 64]
        self.columns = 13  # Number of notes per string
        self.grid = self.generate_grid()

    def generate_grid(self):
        """Generates a 6x13 grid of MIDI notes based on guitar tuning."""
        grid = []
        for string_note in self.tuning:
            row = [string_note + fret for fret in range(self.columns)]
            grid.append(row)
        return grid

    def get_note_at_position(self, row, col):
        """Returns the MIDI note at a specific row and column in the grid."""
        if 0 <= row < len(self.grid) and 0 <= col < self.columns:
            return self.grid[row][col]
        else:
            raise IndexError("Row or column out of range")

    def __str__(self):
        """Returns a string representation of the note grid for debugging."""
        return "\n".join(["\t".join(map(str, row)) for row in self.grid])


# For testing purposes
if __name__ == "__main__":
    note_grid = MIDINoteGrid()
    print("MIDI Note Grid:")
    print(note_grid)
