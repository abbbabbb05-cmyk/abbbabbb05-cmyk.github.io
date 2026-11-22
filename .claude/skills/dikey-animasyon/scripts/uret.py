#!/usr/bin/env python3
"""Senaryo JSON'undan dikey (1080x1920) seslendirmeli animasyon videosu üretir.

Kullanım:
  python3 uret.py senaryo.json cikti_klasoru            # tam video
  python3 uret.py senaryo.json cikti_klasoru --onizleme # sadece birkaç PNG kare (hızlı kontrol)
  python3 uret.py senaryo.json cikti_klasoru --sessiz   # ElevenLabs kullanmadan (karakter harcamaz)
"""
import base64, hashlib, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30

SESLER = {  # ElevenLabs hazır sesleri (ücretsiz planda API ile çalışanlar)
    'chris': 'iP95p4xoKVk53GoZ742B', 'jessica': 'cgSgspJ2msm6clMCkdW9', 'liam': 'TX3LPaxmHKxFdv7VOQHJ',
    'sarah': 'EXAVITQu4vr4xnSDxMaL', 'laura': 'FGY2WhTYpPnrIDTdsKH5', 'charlie': 'IKne3meq5aSn9XLyUdCD',
    'george': 'JBFqnCBsd6RMkjVDRZzb', 'callum': 'N2lVS1w4EtoT3dr4eOWO', 'river': 'SAz9YHcvj6GT2YYXdXww',
    'harry': 'SOYHLrjzK2X1ezoPC6cr', 'alice': 'Xb7hH8MSUJpSbSDYk0k2', 'matilda': 'XrExE9yKIg1WjnnlVkGX',
    'will': 'bIHbv24MWmeRgasZH58o', 'eric': 'cjVigY5qzO86Huf0OWal', 'bella': 'hpp4J3VqNfWAUOO0d1Us',
    'brian': 'nPczCjzI2devNBz1zQrb', 'daniel': 'onwK4e9ZLuTAKqWW03F9', 'lily': 'pFZP5JQG7iQjIQuC4Bku',
    'adam': 'pNInz6obpgDQGcFmaJgB', 'bill': 'pqHfZKP75CvOlQylNhV4', 'roger': 'CwhRBWXzGAHq8TQ4Fs17',
}

HAZIR = {  # karakter kalıpları; senaryoda istenen alan ezilebilir
    'danisman': dict(ad='Danışman', ten='#f1c27d', sac='yana', sac_renk='#2b1b10', giysi='takim', giysi_renk='#1f3a93', kravat='#e63946', pantolon='#1c2541', ses='chris'),
    'musteri': dict(ad='Müşteri', ten='#e0ac69', sac='kisa', sac_renk='#4a3020', giysi='kapusonlu', giysi_renk='#2a9d8f', pantolon='#3d405b', ses='liam'),
    'musteri_kadin': dict(ad='Müşteri', ten='#f3cfa5', sac='uzun', sac_renk='#6b3e26', giysi='tisort', giysi_renk='#e76f51', pantolon='#264653', ses='jessica'),
    'patron': dict(ad='Patron', ten='#d8a47f', sac='kel', sac_renk='#555', giysi='takim', giysi_renk='#2d2d2d', kravat='#f4a261', pantolon='#1d1d1d', biyik=True, ses='brian'),
    'stajyer': dict(ad='Stajyer', ten='#f6d5b0', sac='kivircik', sac_renk='#1b1b1b', giysi='tisort', giysi_renk='#ffb703', pantolon='#4361ee', gozluk=True, ses='will'),
    'oyuncu': dict(ad='Oyuncu', ten='#e8b88a', sac='kisa', sac_renk='#222', giysi='kapusonlu', giysi_renk='#7209b7', pantolon='#14213d', gozluk=True, ses='liam'),
}
DEF_CHAR = dict(ten='#f1c27d', sac='kisa', sac_renk='#3b2a1a', giysi='tisort', giysi_renk='#4361ee', pantolon='#2b2d42', kravat=None, gozluk=False, biyik=False, ses='chris')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'Komut hatası: {" ".join(cmd[:4])}...\n{r.stderr[-1500:]}')
    return r.stdout


def tts(text, voice, out_dir, ayar, sessiz):
    """(mp3_yolu | None, kelimeler[{w,s,e}], süre)"""
    vid = SESLER.get(voice, voice)
    words_raw = text.split()
    if not sessiz:
        key = hashlib.sha1(json.dumps([vid, text, ayar], sort_keys=True).encode()).hexdigest()[:16]
        cdir = os.path.join(out_dir, '.ses'); os.makedirs(cdir, exist_ok=True)
        mp3, js = os.path.join(cdir, key + '.mp3'), os.path.join(cdir, key + '.json')
        if not os.path.exists(js):
            body = json.dumps({'text': text, 'model_id': 'eleven_multilingual_v2', 'voice_settings': {
                'stability': ayar.get('stability', 0.4), 'similarity_boost': 0.8, 'style': ayar.get('style', 0.35),
                'use_speaker_boost': True, 'speed': ayar.get('hiz', 1.0)}})
            r = subprocess.run(['curl', '-s', '-X', 'POST', f'https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps',
                                '-H', 'xi-api-key: ' + os.environ.get('ELEVENLABS_API_KEY', 'proxy'), '-H', 'Content-Type: application/json',
                                '-d', '@-'], input=body, capture_output=True, text=True)
            try:
                d = json.loads(r.stdout)
                open(mp3, 'wb').write(base64.b64decode(d['audio_base64']))
                json.dump(d['alignment'], open(js, 'w'))
            except Exception:
                print(f'  ! ElevenLabs hatası ({voice}): {r.stdout[:300]} -> bu satır sessiz geçiyor', file=sys.stderr)
                return tts(text, voice, out_dir, ayar, True)
        al = json.load(open(js))
        dur = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3]).strip())
        words, cur = [], None
        for ch, s, e in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
            if ch.isspace():
                if cur: words.append(cur); cur = None
                continue
            if cur is None: cur = {'w': ch, 's': s, 'e': e}
            else: cur['w'] += ch; cur['e'] = e
        if cur: words.append(cur)
        return mp3, words, dur
    # sessiz: kelime başına tahmini süre
    t, words = 0.0, []
    for w in words_raw:
        d = 0.18 + 0.055 * len(w) + (0.25 if re.search(r'[.!?,]$', w) else 0)
        words.append({'w': w, 's': t, 'e': t + d}); t += d
    return None, words, t


def chunks(words):
    out, a = [], 0
    while a < len(words):
        b, ln = a, 0
        while b < len(words) and (b - a) < 3 and ln + len(words[b]['w']) <= 18:
            ln += len(words[b]['w']) + 1; b += 1
            if re.search(r'[.!?,:;…]$', words[b - 1]['w']): break
        if b == a: b = a + 1
        out.append({'a': a, 'b': b, 's': words[a]['s']}); a = b
    for i, c in enumerate(out):
        c['e'] = out[i + 1]['s'] if i + 1 < len(out) else words[-1]['e'] + 0.5
    return out


def norm(s): return re.sub(r'[^\wçğıöşü]', '', s.lower().replace('İ', 'i').replace('I', 'ı'))


def sfx(out_dir):
    d = os.path.join(out_dir, '.sfx'); os.makedirs(d, exist_ok=True)
    spec = {
        'pop': ['-f', 'lavfi', '-i', "aevalsrc='0.55*sin(2*PI*(380+2200*t)*t)*exp(-28*t)':s=44100:d=0.2"],
        'whoosh': ['-f', 'lavfi', '-i', 'anoisesrc=d=0.45:c=pink:a=0.7:r=44100', '-af', 'bandpass=f=1400:width_type=h:w=1500,afade=t=in:d=0.22,afade=t=out:st=0.22:d=0.23'],
        'ding': ['-f', 'lavfi', '-i', "aevalsrc='0.35*(sin(2*PI*988*t)+0.6*sin(2*PI*1480*t))*exp(-4*t)':s=44100:d=1.0"],
    }
    for k, a in spec.items():
        p = os.path.join(d, k + '.wav')
        if not os.path.exists(p): run(['ffmpeg', '-y', '-loglevel', 'error'] + a + [p])
    return {k: os.path.join(d, k + '.wav') for k in spec}


def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    src, out_dir = sys.argv[1], sys.argv[2]
    onizleme, sessiz = '--onizleme' in sys.argv, '--sessiz' in sys.argv
    S = json.load(open(src)); base = os.path.dirname(os.path.abspath(src))
    os.makedirs(out_dir, exist_ok=True); out_dir = os.path.abspath(out_dir)
    adir = os.path.join(out_dir, 'gorseller'); os.makedirs(adir, exist_ok=True)

    def asset(p):
        ap = p if os.path.isabs(p) else os.path.join(base, p)
        if not os.path.exists(ap): sys.exit(f'Görsel bulunamadı: {ap}')
        dst = os.path.join(adir, os.path.basename(ap)); shutil.copy(ap, dst)
        return 'gorseller/' + os.path.basename(ap)

    chars = {}
    for i, (cid, c) in enumerate((S.get('karakterler') or {}).items()):
        d = dict(DEF_CHAR); d.update(HAZIR.get(c.get('tip', cid), {})); d.update(c)
        d.setdefault('ad', cid.capitalize()); d['seed'] = i * 1.37
        chars[cid] = d
    anlatici = S.get('anlatici_ses', 'liam')
    ayar = S.get('ses_ayar', {})
    vurgu = S.get('vurgu', '#FFD93D')

    t, prev_cast, audio, scenes = 0.0, [], [], []
    for n, sc in enumerate(S['sahneler']):
        sc = dict(sc); tip = sc.get('tip', 'dialog'); sc['tip'] = tip
        sc['audioOffset'] = 0.3 if n else 0.15
        if tip == 'dialog':
            sc.setdefault('sahnede', [sc['konusan']])
            sc.setdefault('arkaplan', S.get('arkaplan', 'ofis'))
            sc['giris'] = [c for c in sc['sahnede'] if c not in prev_cast]; prev_cast = sc['sahnede']
            voice = chars.get(sc['konusan'], {}).get('ses', 'chris')
        else:
            sc.setdefault('arkaplan', {'baslik': 'patlama', 'kapanis': 'patlama'}.get(tip, 'duz'))
            sc.setdefault('renk', S.get('renk', '#6c5ce7'))
            voice = sc.get('ses', anlatici)
        if tip == 'oyun':
            g = sc.get('gorseller') or ([sc['gorsel']] if sc.get('gorsel') else [])
            sc['gorseller'] = [asset(x) for x in g]
        if tip == 'kapanis' and sc.get('gorsel'): sc['gorsel'] = asset(sc['gorsel'])
        soz = (sc.get('soz') or '').strip()
        if soz:
            mp3, words, adur = tts(soz, voice, out_dir, ayar, sessiz)
            sc['words'], sc['chunks'] = words, chunks(words)
        else:
            mp3, adur = None, 0.0; sc['words'], sc['chunks'] = [], []
        minimum = {'baslik': 2.0, 'kapanis': 3.0, 'liste': 1.5 + 1.0 * len(sc.get('maddeler', [])), 'oyun': 3.0}.get(tip, 1.5)
        sc['dur'] = round(max(sc.get('sure', 0), minimum, sc['audioOffset'] + adur + 0.35), 3)
        sc['start'] = round(t, 3)
        if tip == 'liste':  # maddeler söylendiği anda gelsin
            ws, idx, zam = [norm(w['w']) for w in sc['words']], 0, []
            m = sc.get('maddeler', [])
            for k, it in enumerate(m):
                first = norm(it.split()[0]) if it.split() else ''
                found = next((j for j in range(idx, len(ws)) if first and ws[j].startswith(first[:5])), None)
                if found is not None: zam.append(sc['audioOffset'] + sc['words'][found]['s'] - 0.1); idx = found + 1
                else: zam.append(None)
            for k in range(len(m)):
                if zam[k] is None: zam[k] = 0.6 + (sc['dur'] - 1.2) * k / max(1, len(m))
            sc['madde_zaman'] = zam
            for z in zam: audio.append(('pop', t + z, 0.7))
        if mp3: audio.append((mp3, t + sc['audioOffset'], 1.0))
        if n: audio.append(('whoosh', t, 0.45))
        if tip == 'kapanis': audio.append(('ding', t + 0.7, 0.6))
        if tip in ('baslik', 'oyun') and (sc.get('emoji') or sc.get('etiket')): audio.append(('pop', t + 0.45, 0.6))
        if tip == 'dialog' and sc.get('emoji'): audio.append(('pop', t + 0.35, 0.5))
        scenes.append(sc); t += sc['dur']
        print(f'  sahne {n + 1:2d} {tip:8s} {sc["dur"]:5.2f}s  {soz[:60]}')
    total = round(t, 3)
    TL = {'sahneler': scenes, 'karakterler': chars, 'toplam': total, 'vurgu': vurgu,
          'kanal': S.get('kanal'), 'ilerleme': S.get('ilerleme', True)}
    html = open(os.path.join(HERE, 'sahne.html')).read().replace('__TIMELINE__', json.dumps(TL, ensure_ascii=False))
    page = os.path.join(out_dir, 'sahne.html'); open(page, 'w').write(html)
    print(f'Toplam süre: {total:.1f} sn')

    if onizleme:
        ks = ','.join(f'{s["start"] + min(s["dur"] - 0.05, max(0.9, s["dur"] * 0.6)):.2f}' for s in scenes)
        subprocess.run(['node', os.path.join(HERE, 'kaydet.js'), page, '-', '-', out_dir, '--kareler', ks], check=True)
        return

    vid = os.path.join(out_dir, '_video.mp4')
    subprocess.run(['node', os.path.join(HERE, 'kaydet.js'), page, str(total), str(FPS), vid], check=True)

    fx = sfx(out_dir)
    ins, flt, labels = ['-f', 'lavfi', '-t', str(total), '-i', 'anullsrc=r=44100:cl=stereo'], [], ['[0:a]']
    for i, (p, at, vol) in enumerate(audio, start=1):
        ins += ['-i', fx.get(p, p)]
        ms = int(at * 1000)
        flt.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume={vol}[a{i}]'); labels.append(f'[a{i}]')
    k = len(audio) + 1
    if S.get('muzik'):
        mp = S['muzik'] if os.path.isabs(S['muzik']) else os.path.join(base, S['muzik'])
        ins += ['-stream_loop', '-1', '-i', mp]
        flt.append(f'[{k}:a]aresample=44100,aformat=channel_layouts=stereo,volume={S.get("muzik_ses", 0.12)},atrim=0:{total},afade=t=out:st={max(0, total - 1.5)}:d=1.5[m]'); labels.append('[m]')
    flt.append(f'{"".join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[out]')
    aud = os.path.join(out_dir, '_ses.m4a')
    run(['ffmpeg', '-y', '-loglevel', 'error'] + ins + ['-filter_complex', ';'.join(flt), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', aud])

    name = re.sub(r'[^\w-]+', '_', S.get('baslik', 'video')).strip('_')[:50] or 'video'
    final = os.path.join(out_dir, name + '.mp4')
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vid, '-i', aud, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy', '-movflags', '+faststart', '-shortest', final])
    kapak = os.path.join(out_dir, name + '_kapak.jpg')
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(min(1.2, total / 2)), '-i', final, '-frames:v', '1', '-q:v', '2', kapak])
    for f in (vid, aud): os.remove(f)
    print('VIDEO:', final); print('KAPAK:', kapak)


if __name__ == '__main__':
    main()
