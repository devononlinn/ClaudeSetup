"""Pick each channel's 2 most-viewed long-form videos (>3 min, not #shorts) via the YouTube Data API.
Usage: YT_API_KEY=... python pick_videos.py @handle1 @handle2 ... > picks.json"""
import json, os, re, sys, urllib.request, urllib.parse, urllib.error
API="https://www.googleapis.com/youtube/v3/"
def get(ep, **p):
    if os.environ.get("YT_API_KEY"): p["key"] = os.environ["YT_API_KEY"]
    with urllib.request.urlopen(API+ep+"?"+urllib.parse.urlencode(p)) as r: return json.load(r)
def secs(d):
    m=re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",d); dd,h,mi,s=(int(x or 0) for x in m.groups()); return dd*86400+h*3600+mi*60+s
handles=sys.argv[1:]; out=[]
for h in handles:
    ch=get("channels",part="contentDetails,statistics,snippet",forHandle=h)
    if not ch.get("items"): out.append({"handle":h,"error":"not found"}); continue
    c=ch["items"][0]; up=c["contentDetails"]["relatedPlaylists"]["uploads"]
    ids=[]; tok=None
    src="uploads"
    try:
      while True:
        kw=dict(part="contentDetails",playlistId=up,maxResults=50)
        if tok: kw["pageToken"]=tok
        r=get("playlistItems",**kw); ids+= [i["contentDetails"]["videoId"] for i in r["items"]]
        tok=r.get("nextPageToken")
        if not tok: break
    except urllib.error.HTTPError:
        src="search"; ids=[]; tok=None
        while True:
            kw=dict(part="id",channelId=c["id"],type="video",order="viewCount",maxResults=50)
            if tok: kw["pageToken"]=tok
            r=get("search",**kw); ids+=[i["id"]["videoId"] for i in r["items"]]
            tok=r.get("nextPageToken")
            if not tok or len(ids)>=200: break
    vids=[]
    for i in range(0,len(ids),50):
        r=get("videos",part="snippet,contentDetails,statistics",id=",".join(ids[i:i+50]))
        for v in r["items"]:
            d=secs(v["contentDetails"]["duration"]); t=v["snippet"]["title"]
            vids.append({"id":v["id"],"title":t,"dur":d,"views":int(v["statistics"].get("viewCount",0)),
                         "published":v["snippet"]["publishedAt"][:10],"captions":v["contentDetails"].get("caption")})
    lf=[v for v in vids if v["dur"]>180 and "#short" not in v["title"].lower()]
    lf.sort(key=lambda v:-v["views"])
    out.append({"handle":h,"channel":c["snippet"]["title"],"subs":c["statistics"].get("subscriberCount"),
                "channel_views":c["statistics"].get("viewCount"),"src":src,"n_uploads":len(vids),"n_longform":len(lf),"top2":lf[:2]})
print(json.dumps(out,indent=1))
