#!/usr/bin/env python3
#coding=utf-8

import sys, os, subprocess


kernelPath = None
scratchPath = None
scratchKernelCmd = None

def ParseInit(cmd, out):
    for item in cmd.split(' '):
        if item.find("init=/") != -1:
            out.write(item + "\n")

def ParseCmd():
    global scratchPath, scratchKernelCmd

    if not os.path.exists(scratchKernelCmd):
        return
    with open(scratchKernelCmd) as f, open(scratchPath+"/kernelInit", "w") as out:
        cmds = f.read()
        for cmd in cmds.split('\n')[:-1]:
            ParseInit(cmd, out)


if __name__ == "__main__":
    # execute only if run as a script
    IID = sys.argv[1]
    kernelPath = f"./images/{IID}.kernel"
    scratchPath = f"scratch/{IID}"
    scratchKernelCmd = f"scratch/{IID}/kernelCmd"

    tmpstr = "strings {} | grep \"Linux version\" > {}".format(kernelPath, scratchPath+"/kernelVersion")
    print("执行的命令=> {}".format(tmpstr))
    os.system(tmpstr)

    tmpstr = "strings {} | grep \"init=/\" | sed -e 's/^\"//' -e 's/\"$//' > {}".format(kernelPath, scratchKernelCmd)
    print("执行的命令=> {}".format(tmpstr))
    os.system(tmpstr)

    ParseCmd()
