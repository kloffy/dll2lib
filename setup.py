from distutils.core import setup

import py2exe

'''
manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity version="0.64.1.0" processorArchitecture="amd64" name="Controls" type="x86"/>
<description>Dll2Lib</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="x86" publicKeyToken="6595b64144ccf1df" language="*"/>
    </dependentAssembly>
</dependency>
</assembly>
"""
'''

setup(
    windows = [
        {
            "script": "main.pyw",
            "dest_base": "Dll2Lib",
            "icon_resources": [(1, "gear.ico")]
            #"other_resources": [(24,1,manifest)],
        }
    ],
    options = {
        "py2exe": {
            "includes":['anydbm', 'dbhash'],
            #"skip_archive": 1,
        },
    },
    zipfile = "data/library.zip",
    #data_files=["gear.ico"]
)