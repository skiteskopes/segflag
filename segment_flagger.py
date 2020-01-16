from tkinter import *
import ffmpy
import cv2
import numpy as np
import os
import numpy as np
from tkinter import filedialog
import math
import gc
from tkinter import messagebox
import tifffile as tiff
import shutil
import subprocess

global flag_dict
flag_dict= {}
class segment_flagger(Frame):
    def __init__(self,master):
        self.master = master
        master.title("FLIR_SEGMENT_FLAGGER")
        master.iconbitmap('flam.ico')
        master.geometry("675x150")

        self.menu_label = Label(master,text="Segment Flagging Windows Tool").place(x=15,y=10)

        self.select_button = Button(master, text = "Select Video", command =
        self.select_video, bg = 'navy blue', fg = 'white')
        self.select_button.place(x=50,y=50)

        self.start_button = Button(master, text = "Start", command =
        self.segment_main, bg = 'navy blue', fg = 'white')
        self.start_button.place(x=300,y=90)

        self.label = Label(master, text = 'Dummy', fg = 'green')
    def segment_main(self):
        window1 = Tk()
        w = self.filewidth/2 # width for the Tk root
        h = self.fileheight/2 # height for the Tk root
        ws = window1.winfo_screenwidth() # width of the screen
        hs = window1.winfo_screenheight() # height of the screen
        xx = (ws/2) - (w/2)
        yy = (hs/2) - (h/2)
        window1.geometry('%dx%d+%d+%d' % (w, h,xx,yy))
        image_viewer = segment_main_page(window1,self.filename,self.file,self.dirname,self.filehead,self.fileheight,self.filewidth,self.cwd)
        window1.mainloop()
    def select_video(self):
        self.filename = filedialog.askopenfilename()
        self.label.config(text = self.filename,fg='green')
        self.label.place(x=150,y=50)
        self.file = os.path.basename(self.filename)
        self.dirname = os.path.dirname(self.filename)
        self.filehead = self.file[:-4]
        self.cwd = os.getcwd()
        os.chdir(self.dirname)
        self.fileheight=int(subprocess.check_output("ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=nw=1:nokey=1 "+self.file,shell=True))
        self.filewidth=int(subprocess.check_output("ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=nw=1:nokey=1 "+self.file,shell=True))
class segment_main_page:
        def __init__(self,master,filename,file,dirname,filehead,fileheight,filewidth,cwd):
            self.master = master
            self.filename = filename
            self.file = file
            self.dirname = dirname
            self.filehead = filehead
            self.cwd = cwd
            self.fileheight = fileheight
            self.filewidth = filewidth
            self.index = 1
            self.index2 = 1
            self.framecount = 4
            self.framestart = 0
            self.frameend= 0

            self.filelength=float(subprocess.check_output("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "+self.file,shell=True))
            os.chdir(self.cwd)
            master.title("FLIR_SEGMENT_FLAGGER")
            master.iconbitmap('flam.ico')
            #os.chdir(self.dirname)
            #subprocess.call("ffmpeg -i "+self.file+" -ss 00:00 -r 30 -t "+str(self.filelength)+" "+self.filehead+"_%03d.jpg",shell=True)
            #self.play_button = Button(master, text = "Play", command = self.Play, bg = 'navy blue', fg = 'white')
            #self.play_button.place(x=0,y=0)
            self.canvas = Canvas(master, width = self.filewidth, height = self.fileheight, bg = 'navy blue' )
            self.canvas.pack()
            self.play_button = Button(self.canvas, text = "Play", command = lambda: self.Play(self.play_button,self.index,self.framecount,self.file), bg ='navy', fg='white',relief='raised')
            self.play_button.place(x=0,y=0)
            self.play_button.focus_set()
            #play_button
            self.flag_button = Button(self.canvas, text= "Flag Start", command = lambda: self.Flag(self.flag_button,self.index2,self.framestart,self.framecount), bg= 'green', fg='white')
            self.flag_button.place(x=95,y=0)
            self.canvas.bind("<space>", lambda: self.Play(self.play_button,self.index))

        def Play(self,play_button,index,framecount,file):
            self.index = index
            self.framecount = framecount
            self.play_button = play_button
            self.file = file
            if self.index:
                self.play_button.config( background='red',text='Pause')
                cap = cv2.VideoCapture(self.file)
                while(cap.isOpened()):
                    self.ret, self.frame = cap.read()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    cv2.imshow('frame',gray)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                cap.release()
                cv2.destroyAllWindows()
                    #if not cap.isOpened():
                        #raise ValueError("Unable to open video source", self.file)

            else:
                self.play_button.config(bg= 'navy blue',text='Play')
                """
                    take down the amount of seconds passed and update framecount
                    maybe now frame start / frameend will appear?
                """
            self.index = not self.index
        def Next(self,framecount,canvas):
            self.framecount+= 1
        def Back(self,framecount,canvas):
            self.framecount -= 1


        def Flag(self,flag_button,index2,framestart,framecount):
            self.index2 = index2
            self.framecount = framecount
            self.framestart = framestart
            self.flag_button = flag_button
            if self.index2:
                self.flag_button.config( background='red',text='Flag End')
                self.framestart = self.framecount
                print(self.framestart)

            else:
                self.flag_button.config(bg= 'green',text='Flag Start')
                self.frameend = self.framecount
                #
            self.index2 = not self.index2

if __name__ == '__main__':
    root = Tk()
    my_gui = segment_flagger(root)
    w = 675 # width for the Tk root
    h = 150 # height for the Tk root
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    # set the dimensions of the screen
    # and where it is placed
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    root.mainloop()
