#!/usr/bin/env python3
"""One-shot, research-only source MP4 evidence. No source video is published.

Accepts an already downloaded MP4; independent ffprobe frame index,
unscaled per-frame luminance pixel diffs, and 20 ms decoded audio statistics.
For third-party video this does NOT authorize reuse, training, or reposting.
"""
import argparse, hashlib, json, statistics, subprocess
from fractions import Fraction
from pathlib import Path

def sh(*args):
    return subprocess.check_output(args, stderr=subprocess.PIPE)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for piece in iter(lambda:f.read(1<<20),b''):
            h.update(piece)
    return h.hexdigest()

def exact(stream, n):
    out=bytearray()
    while len(out)<n:
        part=stream.read(n-len(out))
        if not part: break
        out.extend(part)
    return bytes(out)

def analyze(path, out_dir, video_id):
    import numpy as np
    src=Path(path)
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    identity=sha(src)
    metadata=json.loads(sh('ffprobe','-v','error','-show_streams','-show_format',
                            '-of','json',str(src)))
    vs=next((v for v in metadata['streams'] if v.get('codec_type')=='video'),None)
    if vs is None:raise RuntimeError('No video stream')
    width,height=int(vs['width']),int(vs['height'])
    duration=float(metadata['format'].get('duration',0))
    if not 0<duration<=180 or not 0<src.stat().st_size<=90_000_000:
        raise RuntimeError('Media exceeds safety limits')
    base=Fraction(vs['time_base'])
    data=json.loads(sh('ffprobe','-v','error','-select_streams','v:0','-show_frames',
                      '-show_entries','frame=best_effort_timestamp,pts,key_frame,pict_type',
                      '-of','json',str(src)))
    pts=[int(f.get('best_effort_timestamp', f.get('pts'))) for f in data['frames']]
    if not pts or any(b<=a for a,b in zip(pts,pts[1:])):
        raise RuntimeError('Frame PTS are absent or non-increasing')
    cmd=['ffmpeg','-nostdin','-v','error','-noautorotate','-i',str(src),
         '-map','0:v:0','-an','-sn','-dn','-fps_mode','passthrough',
         '-f','rawvideo','-pix_fmt','gray','-']
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    prev=None
    n=width*height
    max_change=0.0
    changes=[]
    try:
        with (out/'frames.jsonl').open('w') as frames, (out/'features.jsonl').open('w') as features:
            for i,pt in enumerate(pts):
                block=exact(proc.stdout,n)
                if len(block)!=n:raise RuntimeError(f'Only {i} raw decoded frames available')
                arr=np.frombuffer(block,dtype=np.uint8).reshape(height,width)
                mean=float(np.mean(arr))/255.
                std=float(np.std(arr))/255.
                change=None if prev is None else float(np.mean(np.abs(arr.astype(np.int16)-prev.astype(np.int16))))/255.
                if change is not None:changes.append((i,change));max_change=max(max_change,change)
                ptime=float(Fraction(pt)*base)
                frames.write(json.dumps({'frame':i,'pts':pt,'pts_s':ptime,'pts_exact':str(Fraction(pt)*base),
                    'key_frame':data['frames'][i].get('key_frame')==1,
                    'pict_type':data['frames'][i].get('pict_type')})+'\n')
                features.write(json.dumps({'frame':i,'pts':pt,'pts_s':ptime,'luma_mean':round(mean,6),
                    'luma_std':round(std,6),'pixel_change_mae':None if change is None else round(change,6),
                    'frame_shape':[height,width],'sampling':'every_source_frame',
                    'pixel_measurement':'full_source_resolution'})+'\n')
                prev=arr.copy()
            if exact(proc.stdout,1):raise RuntimeError('More decoded frames than ffprobe indexed')
        if proc.wait()!=0:raise RuntimeError('ffmpeg decode failed: '+proc.stderr.read().decode(errors='replace')[-250:])
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        proc.stdout.close();proc.stderr.close()
    check=json.loads(sh('ffprobe','-v','error','-select_streams','v:0',
        '-count_frames','-show_entries','stream=nb_read_frames','-of','json',str(src)))
    independent=int(check['streams'][0]['nb_read_frames'])
    if independent!=len(pts):raise RuntimeError(f'Independent decoder count mismatch {independent}/{len(pts)}')
    # Decode audio once to 16 kHz/mono, process 20ms windows.
    has_audio=any(s.get('codec_type')=='audio' for s in metadata['streams'])
    audios=0
    if has_audio:
        samples=sh('ffmpeg','-nostdin','-v','error','-i',str(src),'-map','0:a:0',
                   '-vn','-ar','16000','-ac','1','-f','s16le','-')
        signal=np.frombuffer(samples[:len(samples)//2*2],dtype='<i2')
        with (out/'audio_20ms.jsonl').open('w') as f:
            for i in range(0,len(signal),320):
                chunk=signal[i:i+320].astype(np.float64)/32768.
                if len(chunk)==0:continue
                f.write(json.dumps({'t_s':round(i/16000,6),'rms':round(float(np.sqrt(np.mean(chunk**2))),6),
                    'peak':round(float(np.max(np.abs(chunk))),6),
                    'zero_crossing':round(float(np.mean(chunk[:-1]*chunk[1:]<0)),6) if len(chunk)>1 else 0})+'\n')
                audios+=1
    diffs=[float(Fraction(b-a)*base) for a,b in zip(pts,pts[1:])]
    top=sorted(changes,key=lambda t:t[1],reverse=True)[:20]
    result={'video_id':video_id,'media_sha256':identity,'media_bytes':src.stat().st_size,
            'duration_seconds':duration,'width':width,'height':height,
            'codec':vs.get('codec_name'),'avg_frame_rate':vs.get('avg_frame_rate'),
            'time_base':str(base),'frame_count':len(pts),'ffprobe_count_frames':independent,
            'first_pts':pts[0],'last_pts':pts[-1],
            'frame_interval_median_s':statistics.median(diffs) if diffs else None,
            'frame_interval_min_s':min(diffs) if diffs else None,
            'frame_interval_max_s':max(diffs) if diffs else None,
            'is_vfr_observed':max(diffs)-min(diffs)>1e-5 if diffs else None,
            'pixel_change_max':max_change,
            'top_visual_change_candidates':[{'frame':i,'pts_s':float(Fraction(pts[i])*base),'change_mae':round(d,6)} for i,d in top],
            'audio_20ms_windows':audios,'frame_sampling':'none','analysis_only':True,
            'source_url':'https://www.youtube.com/shorts/'+video_id,
            'youtube_source_original_identity_verified':False,
            'license_to_repost_verified':False,'training_eligible':False}
    (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'status':'success','frame_count':len(pts),'original_fps':vs.get('avg_frame_rate'),
           'sha256':identity,'bytes':src.stat().st_size,'audio_windows':audios}))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--video',required=True);p.add_argument('--out',required=True)
    p.add_argument('--video-id',default='BaE0Meum0oc')
    a=p.parse_args(); analyze(a.video,a.out,a.video_id)
