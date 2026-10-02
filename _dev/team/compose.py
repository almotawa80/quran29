import cv2,glob,numpy as np,sys
from PIL import Image,ImageDraw,ImageFilter
N=512
def bg():
    y,x=np.mgrid[0:N,0:N];d=np.sqrt((x-N*.5)**2+(y-N*.38)**2)/(N*.75);d=np.clip(d,0,1)
    c1=np.array([22,112,84]);c2=np.array([9,58,44])
    return Image.fromarray((c1*(1-d[...,None])+c2*d[...,None]).astype(np.uint8),"RGB").convert("RGBA")
cc=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
out=[]
for f in sorted(glob.glob("*-cut.png")):
    a=np.array(Image.open(f).convert("RGBA")).astype(np.float32)
    al=a[...,3]
    er=cv2.erode((al>0).astype(np.uint8),np.ones((3,3),np.uint8),iterations=2)
    edge=(al<250)|(er==0)
    g=(a[...,0]*.299+a[...,1]*.587+a[...,2]*.114)
    for k in range(3):a[...,k]=np.where(edge,np.maximum(g,a[...,k]*0+g),a[...,k])
    if f.startswith("1291111d"):a[...,3]=cv2.erode(al.astype(np.uint8),np.ones((3,3),np.uint8),iterations=1)
    cut=Image.fromarray(a.clip(0,255).astype(np.uint8),"RGBA")
    src=cv2.imread(f.replace("-cut.png","-image.jpg"))
    if f.startswith("1291111d"): src=src[230:770,150:650]
    fx,fy,fw,fh=max(cc.detectMultiScale(cv2.cvtColor(src,cv2.COLOR_BGR2GRAY),1.1,5,minSize=(40,40)),key=lambda r:r[2])
    s=0.34*N/fw;ys=np.where(a[...,3].max(1)>20)[0];bot=ys.max();cx,cy=fx+fw/2,fy+fh/2
    if (bot-cy)*s+0.42*N<N: s=(N-0.42*N)/(bot-cy)*1.02
    im=cut.resize((round(cut.width*s),round(cut.height*s)),Image.LANCZOS)
    im.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(0.7)))
    B=bg();B.alpha_composite(im,(round(N/2-cx*s),round(0.42*N-cy*s)))
    o=f.replace("-cut.png","-final.jpg");B.convert("RGB").save(o,quality=86);out.append(o)
W=Image.new("RGB",(N*4+30,N),"white")
for i,o in enumerate(out):
    m=Image.new("L",(N,N),0);ImageDraw.Draw(m).ellipse((0,0,N-1,N-1),fill=255);W.paste(Image.open(o),(i*(N+10),0),m)
W.save("/tmp/team.png");print(out)
