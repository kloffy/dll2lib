import os, os.path
import re
import shelve
import subprocess, _subprocess
import wx

import vsconfig

DLL_EXT, TMP_EXT, DEF_EXT, LIB_EXT = 'dll', 'tmp', 'def', 'lib'

def StripLibraryNamingConvention(file, extension=LIB_EXT):
    name, _ = os.path.splitext(file)
    
    regex = re.compile(r'lib(.*)-\d+')
    match = regex.match(name)
    if match: name = match.group(1)
    
    return name + '.' + extension

class CommandPrompt(object):
    def __init__(self):
        #startupinfo = subprocess.STARTUPINFO()
        #startupinfo.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        #startupinfo.wShowWindow = _subprocess.SW_HIDE
        
        self.proc = subprocess.Popen('cmd.exe /k', cwd=cwd, shell=True, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    def push(self, command):
        self.proc.stdin.write(command + '\n')
    def execute(self):
        return self.proc.communicate()

class Dll2Lib(object):
    DefaultTitle = 'Dll2Lib'
    DefaultPosition = wx.DefaultPosition
    DefaultSize = wx.Size(800, 600)
    DefaultLabelSize = wx.Size(80,-1)
    DefaultStyle = wx.DEFAULT_FRAME_STYLE
    DetectedVS = list(vsconfig.DetectVS())
    SelectedVS = None
    SelectedMachine = None
    
    def __init__(self, config):
        self.config = config
        self.config.setdefault('path', '')
    
        self.InitUI()
    
    def CreateNotebookPanelWithTextCtrl(self, notebook):
        panel = wx.Panel(notebook)
        sizer = wx.BoxSizer()
        
        text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        text.SetFont(self.font)
        
        sizer.Add(text, 1, wx.EXPAND)
        
        panel.SetSizer(sizer)
        
        return panel, text
    
    def InitUI(self):
        self.frame = wx.Frame(None, title=Dll2Lib.DefaultTitle, pos=Dll2Lib.DefaultPosition, size=Dll2Lib.DefaultSize, style=Dll2Lib.DefaultStyle)
        
        self.InitIcon()
        
        self.frame.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.font = wx.Font(8, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL) 
        
        self.InitMenuBar()
        self.InitStatusBar()
        self.InitAboutDialog()
        
        panel = wx.Panel(self.frame)
        
        self.InitToolset(panel)
        self.InitInformation(panel)
        
        self.btnRun = wx.Button(panel, label='Run', size=wx.Size(100, 20))
        self.btnRun.Enable(False)
        
        self.frame.Bind(wx.EVT_BUTTON, self.OnClick)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        self.dirBrowser = wx.GenericDirCtrl(panel, size=wx.Size(200, 0))
        self.dirBrowser.SetFilter('*.' + DLL_EXT)
        
        tree = self.dirBrowser.GetTreeCtrl()
        self.frame.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemSelected, tree)
        self.frame.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelectionChanged, tree)
        
        self.dirBrowser.SetPath(self.config['path'])
        self.OnItemSelected(None)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        nb = wx.Notebook(panel)
        
        pnlOut, self.txtOut = self.CreateNotebookPanelWithTextCtrl(nb)
        pnlTmp, self.txtTmp = self.CreateNotebookPanelWithTextCtrl(nb)
        pnlDef, self.txtDef = self.CreateNotebookPanelWithTextCtrl(nb)
        
        nb.AddPage(pnlOut, "Console")
        nb.AddPage(pnlTmp, "Temporary")
        nb.AddPage(pnlDef, "Definition")
        
        vbox.Add(self.sbsToolset, 0, wx.EXPAND)
        vbox.Add(self.sbsInformation, 0, wx.EXPAND)
        vbox.Add(nb, 1, wx.EXPAND)
        vbox.Add(self.btnRun, 0, wx.ALIGN_CENTER_HORIZONTAL)
        
        hbox.Add(self.dirBrowser, 0, wx.EXPAND)
        hbox.Add(vbox, 1, wx.EXPAND)
        
        panel.SetSizer(hbox)
        
        self.frame.Centre()
        self.frame.Show(True)
    
    def InitIcon(self):
        try:
            import win32api
            exeName = win32api.GetModuleFileName(win32api.GetModuleHandle(None))
            icon = wx.Icon(exeName, wx.BITMAP_TYPE_ICO)
            self.frame.SetIcon(icon)
        except ImportError: pass
    
    def InitToolset(self, panel):
        sb = wx.StaticBox(panel, label="Toolset")
        sbs = wx.StaticBoxSizer(sb, wx.VERTICAL)
        gbs = wx.GridBagSizer(2, 2)
        
        lblVS = wx.StaticText(panel, label="IDE", size=Dll2Lib.DefaultLabelSize)
        self.cbxVS = wx.ComboBox(panel, style=wx.CB_READONLY, size=wx.Size(150,-1))
        
        lblMachine = wx.StaticText(panel, label="Architecture", size=Dll2Lib.DefaultLabelSize)
        self.cbxMachine = wx.ComboBox(panel, style=wx.CB_READONLY, size=wx.Size(150,-1))
        
        self.frame.Bind(wx.EVT_COMBOBOX, self.OnSelect)
        
        for vs in reversed(Dll2Lib.DetectedVS): self.cbxVS.Append(vs.name, vs)
        
        self.cbxVS.SetSelection(0)
        self.OnSelect(None)
        
        for machine in ['x86','x64']: self.cbxMachine.Append(machine)
        
        self.cbxMachine.SetSelection(0)
        self.OnSelect(None)
        
        # Proper way?
        #evt = wx.CommandEvent(wx.wxEVT_COMMAND_COMBOBOX_SELECTED, self.cbxVS.GetId())
        #wx.PostEvent(self.cbxVS, evt)
        
        gbs.Add(lblVS, pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, border=10)
        gbs.Add(self.cbxVS, pos=(0,1), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        gbs.Add(lblMachine, pos=(1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, border=10)
        gbs.Add(self.cbxMachine, pos=(1,1), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        #gbs.AddGrowableRow(0)
        #gbs.AddGrowableCol(1)
        
        sbs.Add(gbs, 1, wx.EXPAND|wx.ALL)
        
        self.sbsToolset = sbs
    
    def InitInformation(self, panel):
        sb = wx.StaticBox(panel, label="Information")
        sbs = wx.StaticBoxSizer(sb, wx.VERTICAL)
        gbs = wx.GridBagSizer(2, 2)
        
        lblDllFile = wx.StaticText(panel, label="Input", size=Dll2Lib.DefaultLabelSize)
        self.txtDllFile = wx.TextCtrl(panel)
        self.txtDllFile.Enable(False)
        
        gbs.Add(lblDllFile, pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, border=10)
        gbs.Add(self.txtDllFile, pos=(0, 1), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        lblLibFile = wx.StaticText(panel, label="Output", size=Dll2Lib.DefaultLabelSize)
        self.txtLibFile = wx.TextCtrl(panel)
        self.txtLibFile.Enable(True)
        
        gbs.Add(lblLibFile, pos=(1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, border=10)
        gbs.Add(self.txtLibFile, pos=(1, 1), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)

        #gbs.AddGrowableRow(0)
        gbs.AddGrowableCol(1)
        
        sbs.Add(gbs, 1, wx.EXPAND|wx.ALL)
        
        self.sbsInformation = sbs
    
    def InitMenuBar(self):
        menubar = wx.MenuBar()
        
        # File
        fileMenu = wx.Menu()
        #openItem = fileMenu.Append(wx.ID_OPEN, 'Open...', 'Open Project')
        quitItem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit Application')
        
        # Help
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT, 'About', 'About Application')
        
        #self.frame.Bind(wx.EVT_MENU, self.OnOpen, openItem)
        self.frame.Bind(wx.EVT_MENU, self.OnQuit, quitItem)
        self.frame.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)
        
        menubar.Append(fileMenu, '&File')
        menubar.Append(helpMenu, '&Help')
        
        self.frame.SetMenuBar(menubar)
        
    #def OnOpen(self, event): pass
    
    def InitStatusBar(self):
        self.statusBar = wx.StatusBar(self.frame)
        self.statusBar.SetFieldsCount(1)
        
        self.frame.SetStatusBar(self.statusBar)
    
    def InitAboutDialog(self):
        self.about = wx.Dialog(self.frame, wx.ID_ANY, "About Dll2Lib")
        
        lblAbout = wx.StaticText(self.about, wx.ID_ANY, "Dll2Lib is a GUI for generating '.lib' files from '.dll' files.\nIt invokes Visual Studio command line tools.\nIcon courtesy of PixelMixer.", style=wx.ALIGN_CENTRE)
        
        wikiUrl = 'http://pixel-mixer.com'
        wikiHyperlink = wx.HyperlinkCtrl(self.about, wx.ID_ANY, wikiUrl, wikiUrl)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(lblAbout, 1, flag = wx.EXPAND | wx.ALL, border = 10)
        sizer.Add(wikiHyperlink, 0, flag = wx.EXPAND | (wx.ALL & ~(wx.TOP)), border = 10)
        
        button = wx.Button(self.about, wx.ID_OK)
        button.SetDefault()
        
        sizer.Add(button, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)

        self.about.SetSizer(sizer)
        self.about.Fit()
        
    def Execute(self, command, cwd=None):
        vsvars = vsconfig.VarsPath(Dll2Lib.SelectedVS)
        
        commands = CommandPrompt()
        commands.push('"' + vsvars + '"')
        commands.push(command)
        
        return commands.execute()
    
    def CreateTmp(self, dllDirectory, dllFile, tmpFile):
        command = 'dumpbin /exports /out:%s %s' % (tmpFile, dllFile)
        
        out, err = self.Execute(command, cwd=dllDirectory)
        
        self.txtOut.AppendText(out)
    
    def CreateDef(self, tmpDirectory, tmpFile, defFile):
        dec = r'\d+'
        hex = r'[0-9a-fA-F]+'
        id = r'[\w\d_]+'
        regex = re.compile(r'\s+(' + dec + ')\s+(' + hex + ')\s+(' + hex + ')\s+(' + id + ')')
    
        with open(os.path.join(tmpDirectory, defFile), 'w') as _def:
            _def.write('EXPORTS\n')
            
            with open(os.path.join(tmpDirectory, tmpFile), 'r') as _tmp:
                while True:
                    line = _tmp.readline()
                    if not line: break
                    match = regex.match(line)
                    
                    if match: _def.write(match.group(4) + '\n')
    
    def CreateLib(self, defDirectory, defFile, libFile):
        command = 'lib /NOLOGO /def:%s /out:%s /machine:%s' % (defFile, libFile, Dll2Lib.SelectedMachine)
        
        out, err = self.Execute(command, cwd=defDirectory)
        
        self.txtOut.AppendText(out)
    
    def OnAbout(self, event):
        self.about.CenterOnParent(wx.BOTH)
        self.about.ShowModal()
    
    def OnClick(self, event):
        dllPath = self.txtDllFile.GetValue()
        libPath = self.txtLibFile.GetValue()
        
        if not dllPath:
            wx.MessageBox('Please specify a valid input file.', "Question", wx.ICON_QUESTION)
            return
            
        if not libPath:
            wx.MessageBox('Please specify a valid output file.', "Question", wx.ICON_QUESTION)
            return
        
        if not (Dll2Lib.SelectedVS and Dll2Lib.SelectedMachine):
            wx.MessageBox('Problem with Toolset Configuration.\n(Could not find Visual Studio?)', "Error", wx.ICON_ERROR)
            return
        
        vsvars = vsconfig.VarsPath(Dll2Lib.SelectedVS)
        
        if not os.path.isfile(vsvars):
            wx.MessageBox('Problem with Toolset Configuration.\n(Could not find "%s")' % vsconfig.VS_VARS, "Error", wx.ICON_ERROR)
            return
        
        self.statusBar.SetStatusText("Generating Lib...")
        
        dllDirectory, dllFile = os.path.dirname(dllPath), os.path.basename(dllPath)
        libDirectory, libFile = os.path.dirname(libPath), os.path.basename(libPath)
        
        if not os.path.exists(libDirectory): os.makedirs(libDirectory)
        
        dllFile = os.path.relpath(dllPath, libDirectory)
        
        name, extension = os.path.splitext(libFile)
        
        tmpFile = name + '.' + TMP_EXT
        defFile = name + '.' + DEF_EXT 
        
        tmpPath = os.path.join(libDirectory, tmpFile)
        defPath = os.path.join(libDirectory, defFile)
        
        self.txtOut.SetValue('')
        
        self.CreateTmp(libDirectory, dllFile, tmpFile)
        self.txtOut.AppendText('\n')
        
        tmpContent = None
        with open(tmpPath, 'r') as _tmp: tmpContent = _tmp.read()
        self.txtTmp.SetValue(tmpContent)
        
        self.CreateDef(libDirectory, tmpFile, defFile)
        
        defContent = None
        with open(defPath, 'r') as _def: defContent = _def.read()
        self.txtDef.SetValue(defContent)
        
        self.CreateLib(libDirectory, defFile, libFile)
        self.txtOut.AppendText('\n')
        
        os.remove(tmpPath)
        os.remove(defPath)
        
        self.statusBar.SetStatusText("Done")
        
    def OnQuit(self, event):
        self.frame.Close()
        
    def OnSelect(self, event):
        Dll2Lib.SelectedVS = self.cbxVS.GetClientData(self.cbxVS.GetSelection())
        Dll2Lib.SelectedMachine = self.cbxMachine.GetValue()
        
    def OnItemSelected(self, event):
        path = self.dirBrowser.GetPath()
        
        self.config['path'] = path
        self.config.sync()
    
        path = self.dirBrowser.GetFilePath()

        if path:
            directory, file = os.path.dirname(path), os.path.basename(path)
            
            dllFile = file
            dllPath = os.path.join(directory, dllFile)
            libFile = StripLibraryNamingConvention(file, LIB_EXT)
            libPath = os.path.join(directory, libFile)
            
            self.txtDllFile.SetValue(dllPath)
            self.txtLibFile.SetValue(libPath)
            
            self.btnRun.Enable(True)
        else:
            if event: event.Skip()
        
    def OnSelectionChanged(self, event):
        #print "Selection Changed"
        event.Skip()
    
    def ConfirmClose(self):
        '''
        dlg = wx.MessageDialog(self.frame, "Do you really want to close the application?", "Confirm Close", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        return result
        '''
        return wx.ID_OK
        
    def OnClose(self, event):
        if self.ConfirmClose() == wx.ID_OK: self.frame.Destroy()
        
def main():
    config = shelve.open('config.db')
    
    try:
        app = wx.App()
        
        Dll2Lib(config)
        
        app.MainLoop()
    except:
        import sys, traceback
        xc = traceback.format_exception(*sys.exc_info())
        wx.MessageBox(''.join(xc))
    
    config.close()

if __name__ == '__main__': main()