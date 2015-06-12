import collections
import os, os.path
import platform
import _winreg as winreg

VS = collections.namedtuple("VS", ["name", "version", "setup"])

VS_PROTOTYPES = [
    VS(name='Visual Studio 2005', version='8.0', setup=None),
    VS(name='Visual Studio 2008', version='9.0', setup=None),
    VS(name='Visual Studio 2010', version='10.0', setup=None),
    VS(name='Visual Studio 2012', version='11.0', setup=None),
    VS(name='Visual Studio 2013', version='12.0', setup=None),
]

def find_first(items, predicate):
    return next(item for item in items if predicate(item))

def is_os_64bit():
    return platform.machine().endswith('64')

def RegistryVSRoot():
    '''
    Registry Keys:
    SOFTWARE\Microsoft\VisualStudio\<version>\Setup\VS\<edition>
    SOFTWARE\Wow6432Node\Microsoft\VisualStudio\<version>\Setup\VS\<edition>
    '''
    if not is_os_64bit():
        return r"SOFTWARE\Microsoft\VisualStudio"
    else:
        return r"SOFTWARE\Wow6432Node\Microsoft\VisualStudio"

REGISTRY_VS_ROOT = RegistryVSRoot()
REGISTRY_VS_SETUP = r"Setup\VS"

VS_COMMON_DIR = 'VS7CommonDir'
VS_COMMON_BIN_DIR = 'VS7CommonBinDir'

VS_VARS = 'vsvars32.bat'

def VarsPath(vs):
    return os.path.join(vs.setup[VS_COMMON_DIR], r"Tools", VS_VARS)
    
def SetupVS(aSetupKey):
    result = dict()
    try:
        count = 0
        while True:
            name, value, _ = winreg.EnumValue(aSetupKey, count)
            result[name] = value
            count += 1
    except WindowsError: pass
    return result

def DetectVS():
    aReg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    try:
        aKey = winreg.OpenKey(aReg, REGISTRY_VS_ROOT)
        count = 0
        while True:
            aSubKeyName = winreg.EnumKey(aKey, count)
            try:
                vs_prototype = find_first(VS_PROTOTYPES, lambda vs: vs.version == aSubKeyName)
                aSubKey = winreg.OpenKey(aKey, aSubKeyName)
                try:
                    aSetupKey = winreg.OpenKey(aSubKey, REGISTRY_VS_SETUP)
                    yield VS(name=vs_prototype.name, version=vs_prototype.version, setup=SetupVS(aSetupKey))
                    winreg.CloseKey(aSetupKey)
                except WindowsError: pass
                winreg.CloseKey(aSubKey)
            except StopIteration: pass
            count += 1
        winreg.CloseKey(aKey)
    except WindowsError: pass
    winreg.CloseKey(aReg)