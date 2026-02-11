import PyInstaller.__main__
PyInstaller.__main__.run([
    'tray_app.py',
    '--name=MailAgentNew',
    '--onefile',
    '--noconsole',
    '--add-data=config;config',
    '--add-data=src;src',
    '--hidden-import=pystray._win32',
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=telegram',
    '--hidden-import=imap_tools',
    '--hidden-import=yaml',
    '--hidden-import=requests',
    '--icon=mail_agent.ico',
    '--noconfirm'
])
