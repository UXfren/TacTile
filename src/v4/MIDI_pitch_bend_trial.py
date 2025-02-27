import mido

# Open a MIDI port
midi_port = mido.open_output("IAC Driver TacTile")

# Send a pitch bend message
midi_port.send(mido.Message('pitchwheel', channel=0, pitch=8191))
print("Sent max pitch bend up")

# Send a pitch bend down
midi_port.send(mido.Message('pitchwheel', channel=0, pitch=-8192))
print("Sent max pitch bend down")
