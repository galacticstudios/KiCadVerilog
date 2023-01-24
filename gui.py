# MIT license
# 
# Copyright (C) 2023 by Bob Alexander
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import wx

import webbrowser

from KiCadVerilog import main

class GUI:
    def __init__(self, root):
        self.root = root
        #setting title
        root.title("KiCadVerilog")
        #setting window size
        width=808
        height=376
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.geometry(alignstr)
        root.resizable(width=False, height=False)

        self.inputFileNameField=tk.Entry(root)
        self.inputFileNameField["borderwidth"] = "1px"
        ft = tkFont.Font(family='Times',size=10)
        self.inputFileNameField["font"] = ft
        self.inputFileNameField["fg"] = "#333333"
        self.inputFileNameField["justify"] = "left"
        self.inputFileNameField["text"] = ""
        self.inputFileNameField.place(x=130,y=20,width=536,height=30)

        GLabel_409=tk.Label(root)
        ft = tkFont.Font(family='Times',size=10)
        GLabel_409["font"] = ft
        GLabel_409["fg"] = "#333333"
        GLabel_409["justify"] = "left"
        GLabel_409["text"] = "Input Netlist file:"
        GLabel_409.place(x=10,y=20,width=113,height=30)

        inputFileBrowseButton=tk.Button(root)
        inputFileBrowseButton["bg"] = "#e9e9ed"
        ft = tkFont.Font(family='Times',size=10)
        inputFileBrowseButton["font"] = ft
        inputFileBrowseButton["fg"] = "#000000"
        inputFileBrowseButton["justify"] = "center"
        inputFileBrowseButton["text"] = "Browse..."
        inputFileBrowseButton.place(x=720,y=20,width=70,height=25)
        inputFileBrowseButton["command"] = self.InputFileBrowse

        GLabel_80=tk.Label(root)
        ft = tkFont.Font(family='Times',size=10)
        GLabel_80["font"] = ft
        GLabel_80["fg"] = "#333333"
        GLabel_80["justify"] = "left"
        GLabel_80["text"] = "Output Verilog File:"
        GLabel_80.place(x=10,y=80,width=119,height=30)

        self.outputFileNameField=tk.Entry(root)
        self.outputFileNameField["borderwidth"] = "1px"
        ft = tkFont.Font(family='Times',size=10)
        self.outputFileNameField["font"] = ft
        self.outputFileNameField["fg"] = "#333333"
        self.outputFileNameField["justify"] = "left"
        self.outputFileNameField["text"] = ""
        self.outputFileNameField.place(x=130,y=80,width=536,height=30)

        outputFileBrowseButton=tk.Button(root)
        outputFileBrowseButton["bg"] = "#e9e9ed"
        ft = tkFont.Font(family='Times',size=10)
        outputFileBrowseButton["font"] = ft
        outputFileBrowseButton["fg"] = "#000000"
        outputFileBrowseButton["justify"] = "center"
        outputFileBrowseButton["text"] = "Browse..."
        outputFileBrowseButton.place(x=720,y=80,width=70,height=25)
        outputFileBrowseButton["command"] = self.OutputFileBrowse

        GLabel_629=tk.Label(root)
        ft = tkFont.Font(family='Times',size=10)
        GLabel_629["font"] = ft
        GLabel_629["fg"] = "#333333"
        GLabel_629["justify"] = "left"
        GLabel_629["text"] = "Results:"
        GLabel_629.place(x=10,y=170,width=70,height=25)

        GenerateButton=tk.Button(root)
        GenerateButton["bg"] = "#e9e9ed"
        ft = tkFont.Font(family='Times',size=10)
        GenerateButton["font"] = ft
        GenerateButton["fg"] = "#000000"
        GenerateButton["justify"] = "center"
        GenerateButton["text"] = "Generate Verilog"
        GenerateButton.place(x=10,y=130,width=121,height=30)
        GenerateButton["command"] = self.Generate

        self.CancelButton=tk.Button(root)
        self.CancelButton["bg"] = "#e9e9ed"
        ft = tkFont.Font(family='Times',size=10)
        self.CancelButton["font"] = ft
        self.CancelButton["fg"] = "#000000"
        self.CancelButton["justify"] = "center"
        self.CancelButton["text"] = "Cancel"
        self.CancelButton.place(x=160,y=130,width=122,height=30)
        self.CancelButton["command"] = self.Cancel

        HelpButton=tk.Button(root)
        HelpButton["bg"] = "#e9e9ed"
        ft = tkFont.Font(family='Times',size=10)
        HelpButton["font"] = ft
        HelpButton["fg"] = "#000000"
        HelpButton["justify"] = "center"
        HelpButton["text"] = "Help"
        HelpButton.place(x=310,y=130,width=123,height=30)
        HelpButton["command"] = self.Help

        self.ResultsList=tk.Listbox(root)
        self.ResultsList["borderwidth"] = "1px"
        ft = tkFont.Font(family='Times',size=10)
        self.ResultsList["font"] = ft
        self.ResultsList["fg"] = "#333333"
        self.ResultsList["justify"] = "left"
        self.ResultsList.place(x=10,y=200,width=783,height=152)

    def InputFileBrowse(self):
        browse = filedialog.askopenfilename(filetypes=[('Netlist files', '*.net')])
        self.inputFileNameField.delete(0, tk.END)
        self.inputFileNameField.insert(0, browse)

    def OutputFileBrowse(self):
        browse = filedialog.asksaveasfilename(filetypes=[('Verilog files', '*.v')])
        self.outputFileNameField.delete(0, tk.END)
        self.outputFileNameField.insert(0, browse)

    def Generate(self):
        self.root.config(cursor="wait")
        self.ResultsList.delete(0, tk.END)
        log = main(['-i', self.inputFileNameField.get(), '-o', self.outputFileNameField.get()])
        for message in log:
            self.ResultsList.insert(tk.END, message)
        self.CancelButton['text'] = 'Close'
        self.root.config(cursor="")

    def Cancel(self):
        self.root.quit()

    def Help(self):
        webbrowser.open('https://github.com')

def launch():
    app = wx.App()
    frame = GUI()
    frame.Show()
    app.MainLoop()

