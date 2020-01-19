
# import external libraries
import vlc
import sys
import subprocess
import ffmpy
import re
import gc
import cv2
import json
global flag_list
if sys.version_info[0] < 3:
    import Tkinter as Tk
    from Tkinter import ttk
    from Tkinter.filedialog import askopenfilename
else:
    import tkinter as Tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename

# import standard libraries
import os
import pathlib
from threading import Timer,Thread,Event
import time
import platform
flag_list = []
class frameflagger(Tk.Frame):
    def __init__(self,master,frameref,max,dirname,filename,originaldir):
        Tk.Frame.__init__(self, master)
        print(frameref,max,dirname,filename,originaldir)
        self.frameref = frameref
        master.iconbitmap('flam.ico')
        master.title("FLIR_SEGMENT_FLAGGER")
        self.videopane2 = ttk.Frame(self.master)
        self.canvas1 = Tk.Canvas(self.videopane2,bg='navy').pack(fill=Tk.BOTH,expand=1)
        self.index = 1
        if self.frameref > max:
            self.frameref = max
        self.flag_button = Button(self.canvas1, text= "Flag Start", command = lambda: self.Flag(self.flag_button,self.index), bg= 'green', fg='white')
        self.next_button = Button(self.canvas1, text = "Next", command = self.Next, bg ='navy', fg='white')
        self.back_button = Button(self.canvas1, text="Back", command = self.Back, bg= 'navy', fg='white')
    def Next(self):
        self.frameref += 1
        if self.frameref >= max:
            self.frameref = max
    def Back(self):
        self.frameref -= 1
        if self.frameref < 1:
            self.frameref = 1
    def Flag(self,flag_button,index):
        print('flag')
        print(index)
        if self.index:
            self.flag_button.config( background='red',text='Flag End')

        else:
            self.flag_button.config(bg= 'green',text='Flag Start')

        self.index = not self.index


class ttkTimer(Thread):
    """a class serving same function as wxTimer... but there may be better ways to do this
    """
    def __init__(self, callback, tick):
        Thread.__init__(self)
        self.callback = callback
        #print("callback= ", callback())
        self.stopFlag = Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        while not self.stopFlag.wait(self.tick):
            self.iters += 1
            self.callback()
            #print("ttkTimer start")
    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters

# def doit():
#    print("hey dude")

# code to demo ttkTimer
#t = ttkTimer(doit, 1.0)
#t.start()
#time.sleep(5)
#print("t.get= ", t.get())
#t.stop()
#print("timer should be stopped now")


class Player(Tk.Frame):
    """The main window has to deal with events.
    """
    def __init__(self, parent, title=None):
        Tk.Frame.__init__(self, parent)

        self.parent = parent

        if title == None:
            title = "FLIR_SEGMENT_FLAGGER"

        self.parent.title(title)

        self.parent.iconbitmap('flam.ico')

        # Menu Bar
        #   File Menu
        menubar = Tk.Menu(self.parent)
        self.parent.config(menu=menubar)

        fileMenu = Tk.Menu(menubar)
        fileMenu.add_command(label="Open", underline=0, command=self.OnOpen)
        fileMenu.add_command(label="Exit", underline=1, command=_quit)
        menubar.add_cascade(label="File", menu=fileMenu)

        # The second panel holds controls
        self.player = None
        self.videopanel = ttk.Frame(self.parent)
        self.canvas = Tk.Canvas(self.videopanel).pack(fill=Tk.BOTH,expand=1)
        self.videopanel.pack(fill=Tk.BOTH,expand=1)

        ctrlpanel = ttk.Frame(self.parent)
        pause  = ttk.Button(ctrlpanel, text="Pause", command=self.OnPause)
        flag = ttk.Button(ctrlpanel, text="Flag", command= lambda: [f() for f in [self.OnPause, self.OnFlag]])
        play   = ttk.Button(ctrlpanel, text="Play", command=self.OnPlay)
        stop   = ttk.Button(ctrlpanel, text="Stop", command=self.OnStop)
        volume = ttk.Button(ctrlpanel, text="Volume", command=self.OnSetVolume)
        pause.pack(side=Tk.LEFT)
        play.pack(side=Tk.LEFT)
        stop.pack(side=Tk.LEFT)
        flag.pack(side = Tk.LEFT)
        volume.pack(side=Tk.LEFT)

        self.volume_var = Tk.IntVar()
        self.volslider = Tk.Scale(ctrlpanel, variable=self.volume_var, command=self.volume_sel,
                from_=0, to=100, orient=Tk.HORIZONTAL, length=100)
        self.volslider.pack(side=Tk.LEFT)
        ctrlpanel.pack(side=Tk.BOTTOM)

        ctrlpanel2 = ttk.Frame(self.parent)
        self.scale_var = Tk.DoubleVar()
        self.timeslider_last_val = ""
        self.timeslider = Tk.Scale(ctrlpanel2, variable=self.scale_var, command=self.scale_sel,
                from_=0, to=1000, orient=Tk.HORIZONTAL, length=500)
        self.timeslider.pack(side=Tk.BOTTOM, fill=Tk.X,expand=1)
        self.timeslider_last_update = time.time()
        ctrlpanel2.pack(side=Tk.BOTTOM,fill=Tk.X)


        # VLC player controls
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()

        # below is a test, now use the File->Open file menu
        #media = self.Instance.media_new('output.mp4')
        #self.player.set_media(media)
        #self.player.play() # hit the player button
        #self.player.video_set_deinterlace(str_to_bytes('yadif'))

        self.timer = ttkTimer(self.OnTimer, 1.0)
        self.timer.start()
        self.parent.update()

        #self.player.set_hwnd(self.GetHandle()) # for windows, OnOpen does does this


    def OnExit(self, evt):
        """Closes the window.
        """
        self.Close()
    def OnFlag(self):
        length = self.player.get_length()
        if length <=0:
            print('scoping')
        if length > 0:
            self.originaldir = os.getcwd()
            self.datalist = []
            ff = ffmpy.FFmpeg(
                inputs={self.filename: "-ss 00:00 -r 30 -t "+str(length)},
                outputs={self.filename[:-4]+'_%03d.jpg':None})
            os.chdir(self.dirname)
            ff.run()
            for image in os.listdir(os.getcwd()):
                if image.endswith('.jpg'):
                    image = re.split('_|\\.',image)
                    for i in image:
                        if not i.isnumeric():
                            image.remove(i)
                    self.datalist.append(int(image[0]))
            os.chdir(self.originaldir)
            self.max = max(self.datalist)
            gc.disable()
            Frame1 = Tk.Toplevel()
            open_images = frameflagger(Frame1,self.frameref,self.max,self.dirname,self.filename,self.originaldir)




    def OnOpen(self):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """
        # if a file is already running, then stop it.
        self.OnStop()

        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a file".
        p = pathlib.Path(os.path.expanduser("~"))
        fullname =  askopenfilename(initialdir = p, title = "choose your file",filetypes = (("all files","*.*"),("mp4 files","*.mp4")))
        if os.path.isfile(fullname):
            splt = os.path.split(fullname)
            dirname  = os.path.dirname(fullname)
            filename = os.path.basename(fullname)
            self.dirname  = os.path.dirname(fullname)
            self.filename = os.path.basename(fullname)

            # Creation
            self.Media = self.Instance.media_new(str(os.path.join(dirname, filename)))
            self.player.set_media(self.Media)
            # Report the title of the file chosen
            #title = self.player.get_title()
            #  if an error was encountred while retriving the title, then use
            #  filename
            #if title == -1:
            #    title = filename
            #self.SetTitle("%s - tkVLCplayer" % title)

            # set the window id where to render VLC's video output
            if platform.system() == 'Windows':
                self.player.set_hwnd(self.GetHandle())
            else:
                self.player.set_xwindow(self.GetHandle()) # this line messes up windows
            # FIXME: this should be made cross-platform
            self.OnPlay()

            # set the volume slider to the current volume
            #self.volslider.SetValue(self.player.audio_get_volume() / 2)
            self.volslider.set(self.player.audio_get_volume())

    def OnPlay(self):
        """Toggle the status to Play/Pause.
        If no file is loaded, open the dialog window.
        """
        # check if there is a file to play, otherwise open a
        # Tk.FileDialog to select a file
        if not self.player.get_media():
            self.OnOpen()
        else:
            # Try to launch the media, if this fails display an error message
            if self.player.play() == -1:
                self.errorDialog("Unable to play.")

    def GetHandle(self):
        return self.videopanel.winfo_id()

    #def OnPause(self, evt):
    def OnPause(self):
        """Pause the player.
        """
        self.player.pause()
        time.sleep(1)
        self.frameref = float(self.timeslider_last_val) * 30


    def OnStop(self):
        """Stop the player.
        """
        self.player.stop()
        # reset the time slider
        self.timeslider.set(0)


    def OnTimer(self):
        """Update the time slider according to the current movie time.
        """
        if self.player == None:
            return
        # since the self.player.get_length can change while playing,
        # re-set the timeslider to the correct range.
        length = self.player.get_length()
        dbl = length * 0.001
        sedbl = length * 0.001
        self.timeslider.config(to=dbl)

        # update the time on the slider
        tyme = self.player.get_time()
        if tyme == -1:
            tyme = 0
        dbl = tyme * 0.001
        self.timeslider_last_val = ("%.0f" % dbl) + ".0"
        #print(self.timeslider_last_val)
        # don't want to programatically change slider while user is messing with it.
        # wait 2 seconds after user lets go of slider
        if time.time() > (self.timeslider_last_update + 2.0):
            self.timeslider.set(dbl)

    def scale_sel(self, evt):
        if self.player == None:
            return
        nval = self.scale_var.get()
        sval = str(nval)
        if self.timeslider_last_val != sval:
            self.timeslider_last_update = time.time()
            mval = "%.0f" % (nval * 1000)
            self.player.set_time(int(mval)) # expects milliseconds


    def volume_sel(self, evt):
        if self.player == None:
            return
        volume = self.volume_var.get()
        if volume > 100:
            volume = 100
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")



    def OnToggleVolume(self, evt):
        """Mute/Unmute according to the audio button.
        """
        is_mute = self.player.audio_get_mute()

        self.player.audio_set_mute(not is_mute)
        # update the volume slider;
        # since vlc volume range is in [0, 200],
        # and our volume slider has range [0, 100], just divide by 2.
        self.volume_var.set(self.player.audio_get_volume())

    def OnSetVolume(self):
        """Set the volume according to the volume sider.
        """
        volume = self.volume_var.get()
        print("volume= ", volume)
        #volume = self.volslider.get() * 2
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if volume > 100:
            volume = 100
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def errorDialog(self, errormessage):
        """Display a simple error dialog.
        """
        edialog = Tk.tkMessageBox.showerror(self, 'Error', errormessage)

def Tk_get_root():
    if not hasattr(Tk_get_root, "root"): #(1)
        Tk_get_root.root= Tk.Tk()  #initialization call is inside the function
    return Tk_get_root.root

def _quit():
    print("_quit: bye")
    root = Tk_get_root()
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    os._exit(1)

if __name__ == "__main__":
    # Create a Tk.App(), which handles the windowing system event loop
    root = Tk_get_root()
    root.protocol("WM_DELETE_WINDOW", _quit)

    player = Player(root, title="FLIR_SEGMENT_FLAGGER")
    # show the player window centred and run the application
    root.mainloop()
