#!/usr/bin/env python

from Tkinter import *
import tkFileDialog, string

def openFile():
    return tkFileDialog.askopenfilename(
	defaultextension = '.mp3',
	filetypes = [ ('MP3 Audio Files', '*.mp3'), ('All Files', '*')],
	title = "Choose MP3 File")

def joy():
    print variable.get()
    root.quit()

root = Tk()

Label(root, text="Title").grid(row=0)
Label(root, text="Artist").grid(row=1)
Label(root, text="Album").grid(row=2)
Label(root, text="Year").grid(row=3)
Label(root, text="Comment").grid(row=4)
Label(root, text="Genre").grid(row=5)
title_entry = Entry(root)
artist_entry = Entry(root)
album_entry = Entry(root)
year_entry = Entry(root)
comment_entry = Entry(root)
variable = StringVar()

list = [ 'Rock', 'Big Beat', 'JPop' ]
genre_list = apply(OptionMenu, (root, variable) + tuple(list))
variable.set("Anime")

button = Button(root, text="Quit and Print", command=joy)

title_entry.grid(row=0, column=1)
artist_entry.grid(row=1, column=1)
album_entry.grid(row=2, column=1)
year_entry.grid(row=3, column=1)
comment_entry.grid(row=4, column=1)
genre_list.grid(row=5, column=1)
button.grid(row=6, column=1)
root.mainloop()
