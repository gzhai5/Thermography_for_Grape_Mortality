import PySpin

system = PySpin.System.GetInstance()
camera = system.GetCameras()[0]
camera.Init()
nodemap = camera.GetNodeMap()
node_autofocus = PySpin.CCommandPtr(nodemap.GetNode('AutoFocus'))
node_autofocus.Execute()
camera.DeInit()