import random
import mido
from enum import IntEnum
import time

#### ENUMS ####

class Note_Vals(IntEnum):
    C = 60
    C_sharp = 61
    D_flat = 61
    D = 62
    D_sharp = 63
    E_flat = 63
    E = 64
    F = 65
    F_sharp = 66
    G_flat = 66
    G = 67
    G_sharp = 68
    A_flat = 68
    A = 69
    A_sharp = 70
    B_flat = 70
    B = 71

    Octave = 12

class Deg(IntEnum):
    _1 = 0
    b2 = 1
    b9 = 1
    _2 = 2
    _9 = 2
    b3 = 3
    _3 = 4
    _4 = 5
    _11 = 5
    Tritone = 6
    _11_sharp = 6 
    _5 = 7
    b6 = 8
    b13 = 8
    _6 = 9
    _13 = 9
    b7 = 10
    _7 = 11

class Chord_Type(IntEnum):
    Maj = 0
    min = 1
    Dom7 = 2
    halfdim = 3
    dim = 4
    min7 = 5
    Maj7 = 6

#### Note ####

class Note:
    notes_str_dict = {0: "C", 1: "Db", 2: "D", 3: "Eb", 4: "E", 5: "F", 
                     6: "F#", 7: "G", 8: "Ab", 9: "A", 10: "Bb", 11: "B"}

    def __init__(self, note_val):
        self.note_val = note_val
        self.make()
    
    def num_to_str(self):
        note_num = (self.note_val - 60) % 12
        octave_num = 1 + self.note_val // 12
        note_str = self.notes_str_dict[note_num]
        return note_str + str(octave_num)
    
    def make(self):
        mido.Message("note_on", note = self.note_val)
    
    def add_int(self, num):
        return Note(self.note_val + num)

    def __sub__(self, other):
        return abs(self.note_val - other.note_val)

    def __eq__(self, other):
        return self.note_val == other.note_val
    
    def play(self, track, time):
        track.append(mido.Message('note_on', note=self.note_val, velocity=64, time=time))
    
    def stop(self, track, time):
        track.append(mido.Message('note_off', note=self.note_val, velocity=64, time=time))

#### Chords ####

class Chord:

    def __init__(self, root):
        self.root = root
        self.notes = []
        self.inversions = {}
        self.voicings = []
        self.degrees = []
        self.name = ""
        self.make()

    def make(self): #maybe make it so that can also take in Note object, not just enum?
        self.notes = [Note(self.root + degree) for degree in self.degrees]
        self.find_inversions()
        self.voicings += list(self.inversions.values())
        self.current_voicing = self.voicings[0]

    def __str__(self):
        return Note.notes_str_dict[self.root%12] + self.name + str([note.num_to_str() for note in self.current_voicing.notes])
    
    def show_inversions(self):
        invs = ""
        for key in self.inversions.keys():
            invs += str(key) + ": " + str([note.num_to_str() for note in self.inversions[key]]) + "\n"
        return invs

    def find_inversions(self):
        self.inversions[0] = Voicing([Note(note.note_val) for note in self.notes], self)
        for i in range(len(self.notes)-1):
            inv_shallow = self.inversions[i].notes[1:] + [self.inversions[i].notes[0].add_int(Note_Vals.Octave)]
            inv_deep = [Note(note.note_val) for note in inv_shallow]
            self.inversions[i+1] = Voicing(inv_deep, self)
        tranpsosed_inversions = {}
        j = 0
        num_inversions = len(self.inversions.values())
        for i in range(num_inversions):
            for octave in range(-2, 2):
                if octave != 0:
                    inv_diff_octave = [Note(note.note_val + Note_Vals.Octave * octave) for note in self.inversions[i].notes]
                    tranpsosed_inversions[num_inversions -1 + j] = (Voicing(inv_diff_octave, self))
        self.inversions.update(dict(tranpsosed_inversions))
    
    def make_chord_type(root, chord_type):
        if chord_type == Chord_Type.Maj:
            return Maj(root)
        elif chord_type == Chord_Type.min:
            return Min(root)
        elif chord_type == Chord_Type.Dom7:
            return Dom7(root)
        elif chord_type == Chord_Type.halfdim:
            return Halfdim(root)
        elif chord_type == Chord_Type.dim:
            return Dim(root)
        elif chord_type == Chord_Type.Maj7:
            return Maj7(root)
        elif chord_type == Chord_Type.min7:
            return Min7(root)
        else:
            print("unknown chord type") #make error object and throw it?

    def total_distance(self, other): #voice leading needs a lot of work
        if len(self.notes) == len(other.notes):
            zipped = zip(self.notes, other.notes)
        else:
            length_diff = len(other.notes) - len(self.notes)
            if length_diff < 0:
                shorter = other
                longer = self
            else:
                shorter = self
                longer = other
            abs_diff = abs(length_diff)
            zipped = zip(shorter.notes + shorter.notes[:abs_diff], longer.notes)
        lst = [(n1-n2)//3 if (n1-n2<8) else n1-n2 for n1, n2, in zipped]
        return sum(lst)
        
    def play(self, track, time):
        for note in self.notes:
            note.play(track, time)
    
    def stop(self, track, time):
        for note in self.notes:
            note.stop(track, time)

class Voicing(Chord):

    def __init__(self, notes, parent):
        self.parent = parent
        self.notes = notes
        notes = []
        self.inversions = {}
        self.voicings = []
        self.degrees = []
        self.name = ""

    def make(self): #maybe make it so that can also take in Note object, not just enum?
        self.notes = [Note(self.root + degree) for degree in self.degrees]
        self.find_inversions()
        self.voicings += list(self.inversions.values())
        self.current_voicing = self
    
    def find_inversions(self):
        self.inversions = self.parent.inversions

#### Chord Types ####

class Maj(Chord):

    def __init__(self, root):
        self.root = root
        self.notes = []
        self.degrees = [Deg._1, Deg._3, Deg._5]
        self.inversions = {}
        self.voicings = []
        self.chord_type = Chord_Type.Maj
        self.name = "Maj"
        self.make()
    
class Min(Chord):

    def __init__(self, root):
        self.root = root
        self.notes = []
        self.degrees = [Deg._1, Deg.b3, Deg._5]
        self.inversions = {}
        self.voicings = []
        self.chord_type = Chord_Type.min
        self.name = "min"
        self.make()

class Dom7(Chord):

    def __init__(self, root):
        self.root = root
        self.notes = []
        self.degrees = [Deg._1, Deg._3, Deg._5, Deg.b7]
        self.inversions = {}
        self.voicings = []
        self.chord_type = Chord_Type.Dom7
        self.name = "Dom7"
        self.make()

class Halfdim(Chord):

    def __init__(self, root):
        self.root = root
        self.notes = []
        self.degrees = [Deg._1, Deg.b3, Deg.Tritone, Deg.b7]
        self.inversions = {}
        self.voicings = []
        self.chord_type = Chord_Type.halfdim
        self.name = "halfdim"
        self.make()

class Maj7(Chord):

    def __init__(self, root):
        self.root = root
        self.notes = []
        self.degrees = [Deg._1, Deg._3, Deg._5, Deg._7]
        self.inversions = {}
        self.voicings = []
        self.chord_type = Chord_Type.Maj7
        self.name = "Maj7"
        self.make()

class Min7(Chord):

    def __init__(self, root):
        self.root = root
        self.notes = []
        self.degrees = [Deg._1, Deg.b3, Deg._5, Deg.b7]
        self.inversions = {}
        self.voicings = []
        self.chord_type = Chord_Type.min7
        self.name = "min7"
        self.make()

class Dim(Chord):

    def __init__(self, root):
        self.root = root
        self.notes = []
        self.degrees = [Deg._1, Deg.b3, Deg.Tritone]
        self.inversions = {}
        self.voicings = []
        self.chord_type = Chord_Type.dim
        self.name = "dim"
        self.make()

#### Progressions ####

class Progression:
    Maj_key = {Deg._1: [Chord_Type.Maj, Chord_Type.Maj7], Deg._2: [Chord_Type.min, Chord_Type.min7], 
                         Deg._3: [Chord_Type.min, Chord_Type.min7], Deg._4: [Chord_Type.Maj, Chord_Type.Maj7], 
                         Deg._5: [Chord_Type.Maj, Chord_Type.Dom7], Deg._6: [Chord_Type.min, Chord_Type.min7],
                         Deg._7: [Chord_Type.halfdim, Chord_Type.dim]}

    def __init__(self, chord_degrees, tonic):
        self.tonic = tonic
        self.chord_degrees = chord_degrees
        self.make()

    def make(self): #maybe make it so that can also take in Note object, not just enum?
        self.chord_roots_types = [(self.tonic + degree, Progression.Maj_key[degree][random.randint(0, len(self.Maj_key[degree])-1)]) for degree in self.chord_degrees]
        self.chords = self.find_chords()
        self.find_voicings()
    
    def find_chords(self):
        return [Chord.make_chord_type(root, chord_type) for root, chord_type in self.chord_roots_types]
    
    def find_voicings(self):
        [self.best_voicing(chord, i) for chord, i in zip(self.chords, range(len(self.chords)))]
    
    def best_voicing(self, chord, order):
        if order == 0:
            chord.current_voicing = chord.voicings[random.randint(0, len(chord.voicings)-1)]
        else:
            #voicing_sort_func = lambda voicing: sum([voicing.total_distance(self.chords[order-(i+1)].current_voicing) for i in range(order)])
            voicing_sort_func = lambda voicing: sum([voicing.total_distance(self.chords[0].current_voicing) for i in range(order)])
            sorted_voicings = sorted(chord.voicings, key=voicing_sort_func)
            chord.current_voicing = sorted_voicings[random.randint(0,1)]
    
    def __str__(self):
        res = ""
        for chord in self.chords:
            res += str(chord) + "\n"
        return res
    
    def play(self, track, length, tempo):
        for i in range(len(self.chords)):
            self.chords[i].current_voicing.play(track, length)
            time.sleep(1.5)
            self.chords[i].current_voicing.stop(track, length)

            #self.chords[i].current_voicing.stop(track, time*(i+2))

#### Create notes / pregressions ####

CM = Maj(Note_Vals.C)
cm = Min(Note_Vals.C)
C7 = Dom7(Note_Vals.C)
print(CM, cm, C7)
print()

prog1 = Progression([Deg._1, Deg._4, Deg._6, Deg._7], Note_Vals.C)
prog2 = Progression([Deg._1, Deg._4, Deg._6, Deg._5], Note_Vals.C)
prog3 = Progression([Deg._1, Deg._4, Deg._6, Deg._5], Note_Vals.C)
prog4 = Progression([Deg._1, Deg._2, Deg._6, Deg._1], Note_Vals.C)
print(prog1)

#### Save them to a file ####

mid = mido.MidiFile()
track = mido.MidiTrack()
mid.tracks.append(track)
track.append(mido.Message('program_change', program=12, time=0))

#track.append(mido.Message('note_on', note=64, velocity=64, time=32))
#track.append(mido.Message('note_off', note=64, velocity=127, time=32))
prog1.play(track, 150, 150)
prog2.play(track, 150, 150)
prog3.play(track, 150, 150)
prog4.play(track, 150, 150)

mid.save('new_song.mid')


#outport = mido.open_output('IAC Driver pioneer')
#outport.send(msg)
