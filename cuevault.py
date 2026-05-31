#!/usr/bin/env python3
"""CueVault - YouTube transcript library CLI."""
import argparse as ap
import json as j
import math as m
import re
import shutil as sh
import subprocess as su
import sys
import textwrap as tw
from collections import Counter as Ct
from datetime import datetime as dt
from pathlib import Path as Pt
DBF=Pt.home()/".cuevault"/"library.json"
CCH=Pt.home()/".cuevault"/"cache"
ANS={"red":"\033[91m","green":"\033[92m","yellow":"\033[93m","cyan":"\033[96m",
     "bold":"\033[1m","dim":"\033[2m","reset":"\033[0m"}
VTP=re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})\s+-->\s+"
               r"(\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})")
TAG=re.compile(r"<[^>]+>")
SWD=frozenset("the a an is it in of to and or but for on at by be as we".split())
SWD|=frozenset("i that this are was were do did has have with from not so if you".split())
def c(tx,*sy):
    cd="".join(ANS.get(s,"")for s in sy)
    return f"{cd}{tx}{ANS['reset']}"if sys.stdout.isatty()else tx
def stm(w):
    for sx in("ing","tion","ness","ment","able","ies","ly","ed","es","s"):
        if len(w)>len(sx)+3 and w.endswith(sx):
            return w[:-len(sx)]
    return w
def ldb():
    op=Pt.home()/".pilyt"
    if not DBF.exists()and(op/"library.json").exists():
        sh.copytree(op,DBF.parent,dirs_exist_ok=True)
    DBF.parent.mkdir(parents=True,exist_ok=True)
    CCH.mkdir(parents=True,exist_ok=True)
    if DBF.exists():
        try:
            with open(DBF,encoding="utf-8")as f:
                return j.load(f)
        except(j.JSONDecodeError,OSError):
            print(c("  ! Corrupt library reset to empty.","yellow"))
    return{"videos":{},"meta":{"created":dt.now().isoformat(),"count":0,
            "app":"CueVault"}}
def sav(lb):
    lb["meta"]["count"]=len(lb["videos"])
    lb["meta"]["updated"]=dt.now().isoformat()
    lb["meta"]["app"]="CueVault"
    tp=DBF.with_suffix(".tmp")
    with open(tp,"w",encoding="utf-8")as f:
        j.dump(lb,f,indent=2,ensure_ascii=False)
    tp.replace(DBF)
def gid(u):
    mx=re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",u)
    return mx.group(1)if mx else None
def rid(i,lb):
    vi=i if len(i)==11 else gid(i)
    if vi and vi in lb["videos"]:
        return vi
    qy=i.lower()
    for ky,rc in lb["videos"].items():
        if qy in rc["title"].lower():
            return ky
    return None
def ytd():
    if sh.which("yt-dlp")is None:
        print(c("  X yt-dlp not found. pip install yt-dlp","red"))
        sys.exit(1)
def fmd(u):
    rs=su.run(["yt-dlp","--dump-json","--no-playlist","--quiet",u],
              capture_output=True,text=True,check=False)
    if rs.returncode!=0:
        raise RuntimeError(rs.stderr.strip()or"yt-dlp failed")
    return j.loads(rs.stdout)
def fsb(u,vi,ln="en",fw=False):
    cd=CCH/f"{vi}.{ln}.vtt"
    if cd.exists()and not fw:
        return cd
    ot=str(CCH/f"{vi}.%(ext)s")
    for sf in["--write-auto-subs","--write-subs"]:
        su.run(["yt-dlp",sf,"--sub-lang",ln,"--sub-format","vtt",
                "--skip-download","--quiet","--output",ot,u],
               capture_output=True,check=False)
        if cd.exists():
            return cd
    return None
def pvt(ph):
    tx=ph.read_text(encoding="utf-8",errors="ignore")
    dd=[]
    for bl in re.split(r"\n{2,}",tx.strip()):
        mx=VTP.search(bl)
        if not mx:
            continue
        ln=bl[mx.end():].strip().splitlines()
        rw=" ".join(TAG.sub("",x).strip() for x in ln if x.strip())
        rw=re.sub(r"\s+"," ",rw).strip()
        if rw and not rw.upper().startswith("WEBVTT"):
            cu={"start":mx.group(1),"end":mx.group(2),"text":rw}
            if not dd or cu["text"]!=dd[-1]["text"]:
                dd.append(cu)
    return dd
def gsm(cq,mx=80):
    if not cq:
        return"No transcript available."
    at=" ".join(x["text"]for x in cq)
    sn=[s.strip()for s in re.split(r"(?<=[.!?])\s+",at)if len(s.split())>=5]
    if not sn:
        return tw.shorten(at,300)
    wf=Ct(stm(w)for s in sn for w in s.lower().split()if w not in SWD and len(w)>3)
    def ss(i):
        ws=[stm(w)for w in sn[i].lower().split()if w not in SWD and len(w)>3]
        return sum(wf.get(w,0)for w in ws)/max(len(ws),1)
    ix=sorted(sorted(range(len(sn)),key=ss,reverse=True)[:6])
    rs,wd=[],0
    for i in ix:
        w=len(sn[i].split())
        if wd+w>mx:
            break
        rs.append(sn[i]);wd+=w
    return(" ".join(rs)or tw.shorten(at,300))+(" ..."if len(sn)>len(rs)else"")
def cad(ar):
    ytd();u,vi=ar.url,gid(ar.url)
    if not vi:
        print(c("  X Invalid URL — need YouTube video ID.","red"));sys.exit(1)
    lb=ldb()
    if vi in lb["videos"]and not ar.force:
        print(c(f"  i Already in library: {vi} (--force)","yellow"));return
    try:
        mt=fmd(u)
    except(RuntimeError,j.JSONDecodeError)as e:
        print(c(f"  X {e}","red"));sys.exit(1)
    ln=ar.lang or"en";vt=fsb(u,vi,ln,ar.force);cq=pvt(vt)if vt else[]
    rc={"id":vi,"url":f"https://www.youtube.com/watch?v={vi}",
        "title":mt.get("title","Unknown"),"channel":mt.get("uploader",""),
        "duration":mt.get("duration",0),"uploaded":mt.get("upload_date",""),
        "tags":mt.get("tags",[])[:10],"added":dt.now().isoformat(),"lang":ln,
        "summary":gsm(cq),"cues":cq}
    lb["videos"][vi]=rc;sav(lb)
    mn,sc=divmod(rc["duration"],60)
    print(c("  + Added: ","green")+c(rc["title"],"bold")+
          c(f"\n    {rc['channel']}  •  {mn}m{sc:02d}s  •  {len(cq)} cues","dim"))
