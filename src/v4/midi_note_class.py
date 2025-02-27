import mido


class MIDINote:
    def __init__(self, midi_channel, midi_note, velocity=0, pitch_bend=0, vibrato=0, modulation=0):
        self.midi_channel = midi_channel
        self.midi_note = midi_note
        self.velocity = velocity
        self.pitch_bend = pitch_bend
        self.vibrato = vibrato
        self.modulation = modulation
        self.output_port = None

    def open_midi_port(self, port_name="Python MIDI Out"):
        """Opens the MIDI output port to send messages."""
        self.output_port = mido.open_output(port_name)

    def send_note_on(self):
        """Sends a Note On message."""
        if self.output_port:
            msg = mido.Message('note_on', channel=self.midi_channel,
                               note=self.midi_note, velocity=self.velocity)
            self.output_port.send(msg)

    def set_velocity(self, velocity):
        """Sets the velocity of the note, adjusted based on blob size."""
        self.velocity = max(0, min(127, velocity))

    def set_pitch_bend(self, amount):
        """Sets the pitch bend amount."""
        self.pitch_bend = amount

    def set_vibrato(self, amount):
        """Sets the vibrato amount."""
        self.vibrato = amount

    def set_modulation(self, amount):
        """Sets the modulation amount."""
        self.modulation = amount

    def __str__(self):
        return (f"MIDINote(channel={self.midi_channel}, note={self.midi_note}, "
                f"velocity={self.velocity}, pitch_bend={self.pitch_bend}, "
                f"vibrato={self.vibrato}, modulation={self.modulation})")
