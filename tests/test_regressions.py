"""Offline regressions for delivery gates and headless-only preflight."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import shutil
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
delivery=module('check_delivery');environment=module('check_environment')
class Delivery(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        (self.root/'evidence.md').write_text('Release evidence fixture')
        (self.root/'DIRECTION.md').write_text('# Direction\nBecause the product is a model selector, the camera pushes in on the selector.\n| # | Shot |\n|---|---|\n| 1 | feature |\n')
        self.plan={'demo':False,'style':'repo','duration':5,'fps':30,'width':1920,'height':1080,'audioRequired':False,'audioExceptionReason':'User requested a silent version',
            'typography':{'language':'en','mode':'monolingual','headlineFont':'Georgia','captionFont':'Inter'},
            'shots':[{'id':'feature','start':0,'end':5,'type':'detail','headline':'Switch models, keep the conversation','claim':True,'source':['file:evidence.md'],
                'plainExplanation':'After switching models, you can keep working with the previous conversation.','description':'After switching models, the conversation is kept.','component':'src/selector.tsx','actions':[]}]}
    def errors(self):return delivery.check(self.plan,project_dir=self.root)['errors']
    def warnings(self):return delivery.check(self.plan,project_dir=self.root)['warnings']
    def test_valid_production(self):self.assertEqual(self.errors(),[])
    def test_french_monolingual_production(self):
        self.plan['typography']={'language':'fr','mode':'monolingual','headlineFont':'Georgia','captionFont':'Inter'}
        self.plan['shots'][0].update(headline='Changez de modèle, gardez la conversation',description='Après le changement de modèle, la conversation précédente est conservée.',plainExplanation='Après le changement de modèle, vous continuez avec la conversation précédente.')
        (self.root/'DIRECTION.md').write_text('# Direction\nParce que le produit est un sélecteur de modèles, la caméra se rapproche du sélecteur.\n| # | Plan |\n|---|---|\n| 1 | feature |\n')
        self.assertEqual(self.errors(),[])
        self.assertFalse(any('derive devices' in w for w in self.warnings()))
        self.plan['shots'][0]['headline']='Nouveau'
        self.assertTrue(any('meaningful headline' in e for e in self.errors()))
    def test_bilingual_requires_english_headline(self):
        self.plan['typography']={'language':'fr','mode':'bilingual','headlineFont':'Georgia','captionFont':'Inter'}
        self.assertTrue(any('headlineEn' in e for e in self.errors()))
        self.plan['shots'][0]['headlineEn']='Switch models';self.assertEqual(self.errors(),[])
    def test_legacy_chinese_typography_still_accepted(self):
        self.plan['typography']={'mode':'bilingual','zhStyle':'sans-serif','zhFont':'Noto Sans CJK','enFont':'Georgia'}
        self.plan['shots'][0].update(headlineEn='Switch models',headline='切换模型，继续对话',description='切换模型后，对话内容会保留。')
        self.assertEqual(self.errors(),[])
        self.plan['typography']['zhFont']='Georgia'
        self.assertTrue(any('separate fonts' in e for e in self.errors()))
    def test_typography_requires_language_mode_and_fonts(self):
        for broken in [{'mode':'monolingual','headlineFont':'A','captionFont':'B'},{'language':'en','mode':'dual','headlineFont':'A','captionFont':'B'},{'language':'en','mode':'monolingual','headlineFont':'A'}]:
            self.plan['typography']=broken;self.assertTrue(self.errors(),broken)
        self.plan['typography']={'exceptionReason':'User asked for a single system font'};self.assertEqual(self.errors(),[])
    def test_reading_speed_counts_words_for_latin_scripts(self):
        self.plan['shots'][0]['description']='After switching models, the conversation is kept and nothing is lost.'   # 11 words in 5 s: fine
        self.assertFalse(any('too fast' in w for w in self.warnings()))
        self.plan['shots'][0]['description']=' '.join(['word']*20)   # 20 words in 5 s: too fast
        self.assertTrue(any('too fast' in w for w in self.warnings()))
        self.plan['typography']['language']='zh';self.plan['typography']['cjkStyle']='sans-serif'
        self.plan['shots'][0]['description']='切换模型后，对话内容会保留。'   # 14 characters in 5 s: fine
        self.assertFalse(any('too fast' in w for w in self.warnings()))
    def test_all_claims_false(self):
        self.plan['shots'][0]['claim']=False;self.assertTrue(any('at least one' in x for x in self.errors()))
    def test_demo_still_allowed(self):
        self.plan['demo']=True;self.plan['shots'][0]['claim']=False;self.assertEqual(self.errors(),[])
    def test_feature_components_required(self):
        for kind in ['detail','workspace','macro']:
            for value in [None,'','   ']:
                with self.subTest(kind=kind,value=value):
                    self.plan['shots'][0].update(type=kind,component=value)
                    self.assertTrue(any('component source' in x for x in self.errors()))
    def test_audio_exception_required(self):
        for value in [None,'','   ',True]:
            self.plan['audioExceptionReason']=value
            self.assertTrue(any('audioExceptionReason' in x for x in self.errors()))
    def test_source_files_resolve(self):
        for source in ['file:missing.md','./missing.md','repo:missing.tsx']:
            self.plan['shots'][0]['source']=[source];self.assertTrue(self.errors())
        self.plan['repo']=str(self.root)
        for source in ['repo:evidence.md:2','file:evidence.md#L3','evidence.md']:
            self.plan['shots'][0]['source']=[source];self.assertEqual(self.errors(),[])
    def test_legacy_paths_search_video_then_repo(self):
        repo=self.root/'product';(repo/'src/components').mkdir(parents=True)
        (repo/'src/components/Selector.jsx').write_text('export const Selector = 1;')
        (repo/'CHANGELOG.md').write_text('Product release')
        self.plan['repo']='product'
        self.plan['shots'][0]['source']=['src/components/Selector.jsx:12','CHANGELOG.md#L2']
        self.assertEqual(self.errors(),[])
        self.assertEqual(delivery.source_file('CHANGELOG.md',self.root,'product'),repo/'CHANGELOG.md')
        (self.root/'CHANGELOG.md').write_text('Video evidence')
        self.assertEqual(delivery.source_file('CHANGELOG.md',self.root,'product'),self.root/'CHANGELOG.md')
        self.plan['shots'][0]['source']=['missing.md'];self.assertTrue(self.errors())
    def test_explicit_source_roots_do_not_fall_back(self):
        repo=self.root/'product';repo.mkdir();(repo/'release.md').write_text('Release')
        self.plan['repo']=str(repo)
        for source in ['file:release.md','./release.md','../release.md']:
            self.plan['shots'][0]['source']=[source];self.assertTrue(self.errors())
        self.plan['shots'][0]['source']=['repo:release.md'];self.assertEqual(self.errors(),[])
        self.assertEqual(delivery.source_file(str(repo/'release.md'),self.root,None),repo/'release.md')
    def test_production_requires_direction(self):
        (self.root/'DIRECTION.md').unlink()
        self.assertTrue(any('DIRECTION.md' in x for x in self.errors()))
        self.plan['demo']=True;self.assertFalse(any('DIRECTION.md' in x for x in self.errors()))
    def test_direction_without_reasons_warns(self):
        (self.root/'DIRECTION.md').write_text('| # | Shot |\n|---|---|\n| 1 | feature |\n')
        warnings=delivery.check(self.plan,project_dir=self.root)['warnings']
        self.assertTrue(any('derive devices' in w for w in warnings))
    def test_external_evidence_not_treated_as_file(self):
        self.plan['shots'][0]['source']=['https://example.org/release.md','tag:v1.0','commit:abc123'];self.assertEqual(self.errors(),[])
class Preflight(unittest.TestCase):
    def probe(self,project,launch_ok=True):
        def fake_run(args,cwd=None,timeout=30):
            out=''
            if '--version' in args:out='v22.0.0' if 'node' in args[0] else '10.0.0'
            elif '-version' in args:out='ffmpeg 8'
            elif '-filters' in args:out='volume adelay amix loudnorm afade aresample asetnsamples'
            elif '-encoders' in args:out='libx264 aac'
            elif '-e' in args:
                js=args[args.index('-e')+1]
                if 'chromium.launch' in js:
                    if not launch_ok:return {'ok':False,'stdout':'','stderr':'Permission denied','output':'Permission denied'}
                else:
                    self.assertNotIn('executablePath()',js)
                    out=json.dumps({k:{'version':'1.0','path':'/unavailable/'+k} for k in ['playwright','esbuild','react','react-dom','gsap','three']})
            return {'ok':True,'stdout':out,'stderr':'','output':out}
        with patch.object(environment,'run',side_effect=fake_run),patch.object(environment.shutil,'which',side_effect=lambda n:'/bin/'+n),patch('sys.argv',['check_environment','--project',str(project)]),contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as caught:environment.main()
        return caught.exception.code,json.loads(output.getvalue())
    def test_headless_only_and_cache_revalidation(self):
        with tempfile.TemporaryDirectory() as d:
            code,result=self.probe(Path(d));self.assertEqual(code,0);self.assertTrue(result['ready']);self.assertTrue(result['browser']['launched'])
            code,result=self.probe(Path(d));self.assertTrue(result['cached'])
            code,result=self.probe(Path(d),False);self.assertEqual(code,1);self.assertFalse(result['cached']);self.assertIn('browser-launch',result['missing'])
class Starter(unittest.TestCase):
    def test_default_repo_and_unedited_demo_promotion(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d)/'repo';repo.mkdir();project=Path(d)/'video'
            subprocess.run([sys.executable,str(ROOT/'scripts/init_project.py'),'--output',str(project),'--style','default','--repo',str(repo)],capture_output=True,check=True)
            plan=json.loads((project/'plan.json').read_text())
            self.assertEqual(plan['repo'],str(repo.resolve()))
            self.assertIn(str(repo.resolve()),(project/'BRIEF.md').read_text())
            self.assertEqual(plan['typography']['language'],'en');self.assertEqual(plan['typography']['mode'],'monolingual')
            self.assertTrue(all('headlineEn' not in s for s in plan['shots']))
            self.assertEqual(delivery.check(plan,project_dir=project)['errors'],[])
            plan['demo']=False
            self.assertTrue(any('at least one' in e for e in delivery.check(plan,project_dir=project)['errors']))
    def test_init_language_and_bilingual_flags(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d)/'repo';repo.mkdir()
            fr=Path(d)/'fr';subprocess.run([sys.executable,str(ROOT/'scripts/init_project.py'),'--output',str(fr),'--style','repo','--repo',str(repo),'--language','fr'],capture_output=True,check=True)
            plan=json.loads((fr/'plan.json').read_text());self.assertEqual(plan['typography'],{'language':'fr','mode':'monolingual','headlineFont':'Georgia','captionFont':'Inter / system-ui'})
            self.assertIn('Language: fr',(fr/'BRIEF.md').read_text())
            zh=Path(d)/'zh';subprocess.run([sys.executable,str(ROOT/'scripts/init_project.py'),'--output',str(zh),'--style','repo','--repo',str(repo),'--language','zh','--bilingual'],capture_output=True,check=True)
            plan=json.loads((zh/'plan.json').read_text());self.assertEqual(plan['typography']['mode'],'bilingual');self.assertEqual(plan['typography']['cjkStyle'],'sans-serif')
            self.assertTrue(all(s['headlineEn'] for s in plan['shots']))
            self.assertEqual(delivery.check(plan,project_dir=zh)['errors'],[])
            nar=Path(d)/'nar';subprocess.run([sys.executable,str(ROOT/'scripts/init_project.py'),'--output',str(nar),'--style','repo','--repo',str(repo),'--language','fr','--narration','openai'],capture_output=True,check=True)
            plan=json.loads((nar/'plan.json').read_text());n=plan['narration']
            self.assertEqual(n['voice']['engine'],'openai');self.assertEqual([l['shotId'] for l in n['lines']],[s['id'] for s in plan['shots']])
            self.assertEqual([l['intensity'] for l in n['lines']],['strong','normal','soft']);self.assertIn('narrate.py',(nar/'BRIEF.md').read_text())
            self.assertFalse(delivery.check(plan,project_dir=nar)['errors'])   # demo: untimed lines are only warnings
    def test_init_writes_direction_questions_not_answers(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d)/'repo';repo.mkdir();project=Path(d)/'video'
            subprocess.run([sys.executable,str(ROOT/'scripts/init_project.py'),'--output',str(project),'--style','repo','--repo',str(repo)],capture_output=True,check=True)
            text=(project/'DIRECTION.md').read_text()
            for heading in ['Reference breakdown','Product character','Three directions','Choice and rationale','Frame system','Shot list']:self.assertIn(heading,text)
            self.assertIn('do not copy',text)
            self.assertTrue((project/'src/engine.js').is_file())
    def test_sample_views_cover_plan_shots(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d)/'repo';repo.mkdir();project=Path(d)/'video'
            subprocess.run([sys.executable,str(ROOT/'scripts/init_project.py'),'--output',str(project),'--style','repo','--repo',str(repo)],capture_output=True,check=True)
            ids=[s['id'] for s in json.loads((project/'plan.json').read_text())['shots']]
            index=(project/'src/shots/index.js').read_text()
            for i in ids:self.assertIn(i+':',index)
def write_wave(path,frames,channels=1,rate=48000):
    import struct,wave
    with wave.open(str(path),'wb') as w:w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes(struct.pack('<%dh'%len(frames),*frames))
def speech_like(path,seconds,lead=0.25,tail=0.2,amp=0.3):
    """Silence, then a syllable-modulated tone, then silence: enough for onset/offset and level measurement."""
    import math
    rate=48000;frames=[]
    for i in range(int(rate*(lead+seconds+tail))):
        t=i/rate;env=amp*(0.6+0.4*math.sin(2*math.pi*5*t)) if lead<=t<lead+seconds else 0
        frames.append(int(env*32767*math.sin(2*math.pi*180*t)))
    write_wave(path,frames)
def stereo_tone(path,seconds,freq,channels=2):
    import math
    rate=48000;frames=[]
    for i in range(int(rate*seconds)):
        v=int(0.3*32767*math.sin(2*math.pi*freq*i/rate));frames+=[v]*channels
    write_wave(path,frames,channels)
class Narration(unittest.TestCase):
    def plan(self):
        return {'demo':False,'duration':7,'fps':30,'width':1920,'height':1080,'style':'repo','audioRequired':True,'sfxRequired':True,
            'typography':{'language':'fr','mode':'monolingual','headlineFont':'Georgia','captionFont':'Inter'},
            'shots':[{'id':'s1','start':0,'end':3,'type':'title','headline':'Une seule phrase','description':'d','plainExplanation':'p','claim':True,'source':['file:DIRECTION.md'],'component':None,
                      'actions':[{'id':'k1','at':0.5,'action':'click','soundRequired':True}]},
                     {'id':'s2','start':3,'end':7,'type':'end','headline':'Pour finir','description':'d','claim':False,'source':[],'component':None,'actions':[]}],
            'audio':{'ducking':{'enabled':True},'music':{'file':'assets/music.wav','gain':0.6},'cues':[{'at':0.5,'actionId':'k1','file':'assets/sfx/click.wav','gain':0.8,'role':'sfx','kind':'click'}]},
            'narration':{'enabled':True,'language':'fr','voice':{'engine':'file'},'lines':[
                {'id':'a','shotId':'s1','text':'Une première phrase courte.','file':'assets/narration/a.wav','intensity':'strong'},
                {'id':'b','shotId':'s2','text':'Une seconde phrase nettement plus longue qui déborde du plan.','file':'assets/narration/b.wav'}]}}
    def test_untimed_overlapping_and_chimes_are_reported(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'DIRECTION.md').write_text('# D\nParce que.\n| # | Plan |\n|---|---|\n| 1 | s1 |\n| 2 | s2 |\n')
            plan=self.plan()
            errors=delivery.check(plan,project_dir=root)['errors']
            self.assertTrue(any('not timed' in e for e in errors),errors)
            # line a speaks until 3.05 s in a shot that cuts at 3.0 s; line b starts speaking at 2.25 s, on top of a
            for line,start,end in zip(plan['narration']['lines'],[0.1,2.0],[2.95,2.25]):line.update(start=start,speechStart=0.25,speechEnd=end,duration=end+0.2)
            plan['narration']['file']='assets/narration.wav'
            result=delivery.check(plan,project_dir=root)
            self.assertTrue(any('overlap' in e for e in result['errors']),result['errors'])
            self.assertTrue(any('relative to the cut' in e for e in result['errors']),result['errors'])
            plan['narration']['lines'][1]['start']=3.2
            plan['audio']['cues'].append({'at':4.0,'actionId':'k1','file':'assets/sfx/success-2.wav','gain':0.7,'role':'sfx'})   # kind from the file stem, numbered variant
            self.assertTrue(any('lands on narration line b' in w for w in delivery.check(plan,project_dir=root)['warnings']))
            plan['narration']['lines'][1]['start']=2.6;plan['narration']['lines'][0]['speechEnd']=2.0   # b now starts speaking at 2.85, inside shot s1
            self.assertTrue(any('before its shot' in e for e in delivery.check(plan,project_dir=root)['errors']))
            (root/'evidence').mkdir();(root/'evidence/narration.json').write_text(json.dumps({'planSha256':'0'*64}))
            (root/'plan.json').write_text(json.dumps(plan))
            self.assertTrue(any('stale' in w for w in delivery.check(plan,project_dir=root,plan_path=root/'plan.json')['warnings']))
            (root/'evidence/audio-mix.json').write_text(json.dumps({'planSha256':'x','cues':[],'master':{'file':'m','sha256':'y'},'sfxStem':{'file':'s','sha256':'y'},'music':{'file':'a','sha256':'y'}}))
            self.assertTrue(any('no narration stem' in e for e in delivery.check(plan,project_dir=root,mix_report=root/'evidence/audio-mix.json',plan_path=root/'plan.json')['errors']))
    def test_pacing_counts_hangul_as_words_everywhere(self):
        narrate=module('narrate')
        self.assertEqual(delivery.spoken_words('새 설정 화면을 소개합니다'),4)
        for text in ['새 설정 화면을 소개합니다','新しい設定画面を紹介します','Open 設定 and pick a theme']:self.assertEqual(narrate.spoken_words(text),delivery.spoken_words(text))
        self.assertAlmostEqual(delivery.spoken_words('切换模型后，对话内容会保留。'),12/2.2,places=3)   # 12 han characters, punctuation ignored
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg needed')
    def test_measurement_edge_cases(self):
        narrate=module('narrate')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);import math
            speech_like(root/'quiet.wav',1.0,amp=0.002)
            with self.assertRaises(ValueError):narrate.measure(root/'quiet.wav')
            # a 5 ms click, 0.6 s of silence, then speech: the click must not count as the onset
            rate=48000;frames=[int(0.9*32767*math.sin(2*math.pi*2000*i/rate)) for i in range(int(rate*0.005))]+[0]*int(rate*0.6)
            frames+=[int(0.3*(0.6+0.4*math.sin(2*math.pi*5*i/rate))*32767*math.sin(2*math.pi*180*i/rate)) for i in range(int(rate*1.5))]
            write_wave(root/'click.wav',frames)
            self.assertAlmostEqual(narrate.measure(root/'click.wav')['speechStart'],0.605,delta=0.03)
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg needed')
    def test_long_preroll_two_lines_per_shot_and_cue_shift(self):
        narrate=module('narrate')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'assets/narration').mkdir(parents=True)
            speech_like(root/'assets/narration/a.wav',1.0,lead=0.8)          # more pre-roll than lead
            speech_like(root/'assets/narration/a2.wav',1.0,lead=0.1)
            speech_like(root/'assets/narration/b.wav',1.0,lead=0.2)
            plan=self.plan();plan['narration']['lines']=[
                {'id':'a','shotId':'s1','text':'Première.','file':'assets/narration/a.wav'},
                {'id':'a2','shotId':'s1','text':'Seconde, même plan.','file':'assets/narration/a2.wav'},
                {'id':'b','shotId':'s2','text':'Dernière.','file':'assets/narration/b.wav'}]
            plan['shots'][1]['actions']=[{'id':'k2','at':0.5,'action':'ding','soundRequired':True}]
            plan['audio']['cues'].append({'at':3.5,'actionId':'k2','file':'assets/sfx/click.wav','gain':0.8,'role':'sfx','kind':'click'})
            (root/'plan.json').write_text(json.dumps(plan))
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):narrate.narrate(root/'plan.json',fit=True)
            plan=json.loads((root/'plan.json').read_text());a,a2,b=plan['narration']['lines'];s1,s2=plan['shots']
            self.assertAlmostEqual(a['start']+a['speechStart'],0.35,delta=0.03);self.assertLess(a['start'],0)     # placed by its first word, not by file start
            self.assertAlmostEqual(a2['start']+a2['speechStart'],(a['start']+a['speechEnd'])+0.3,delta=0.03)     # second line after the gap
            self.assertGreaterEqual(s1['end']-(a2['start']+a2['speechEnd']),0.59);self.assertEqual(s2['start'],s1['end'])
            self.assertAlmostEqual(plan['audio']['cues'][1]['at'],3.5+(s2['start']-3),places=3)                 # cue moved with its shot
            self.assertAlmostEqual(plan['duration'],s2['end'],places=3)
            stem=narrate.measure(root/'assets/narration.wav')
            self.assertAlmostEqual(stem['speechStart'],0.35,delta=0.06)                                           # the stem really starts speaking on time
    def test_synthesized_lines_persist_when_fitting_fails_and_engine_override_sticks(self):
        narrate=module('narrate')
        calls=[]
        def stub(text,out,voice,language,intensity='normal'):
            calls.append(text);speech_like(out,3.5);return {'voice':'stub'}
        with tempfile.TemporaryDirectory() as d, patch.dict(narrate.ENGINES,{'say':(stub,'stub')}):
            root=Path(d);plan=self.plan();plan['narration']['voice']={'engine':'file'}
            for line in plan['narration']['lines']:line.pop('file')
            (root/'plan.json').write_text(json.dumps(plan))
            if not shutil.which('ffmpeg'):self.skipTest('FFmpeg needed')
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(ValueError):narrate.narrate(root/'plan.json',engine_override='say')   # 3.5 s lines do not fit 3 s / 4 s shots
                self.assertEqual(len(calls),2)
                saved=json.loads((root/'plan.json').read_text())
                self.assertEqual(saved['narration']['voice']['engine'],'say');self.assertTrue(all(l.get('file') and l.get('textSha256') for l in saved['narration']['lines']))
                narrate.narrate(root/'plan.json',fit=True)                                                       # no override needed, nothing re-synthesized
            self.assertEqual(len(calls),2)
    def test_engine_commands_and_requests(self):
        narrate=module('narrate')
        captured={}
        def fake_run(args,**kw):
            captured['args']=args;captured['kw']=kw
            if args[0]=='ffmpeg':return subprocess.CompletedProcess(args,0,'','')
            for a in args:
                if a.startswith('--write-media=') or a.startswith('--output_file') or a=='-o':pass
            return subprocess.CompletedProcess(args,0,'','')
        with tempfile.TemporaryDirectory() as d, patch.object(narrate,'run',side_effect=fake_run), patch.object(narrate,'to_wav',lambda s,o:None), patch.object(narrate.shutil,'which',lambda n:'/bin/'+n):
            out=Path(d)/'l.wav'
            narrate.engine_edge('Changez de modèle.',out,{'speed':0.9},'fr')
            self.assertIn('--rate=-10%',captured['args']);self.assertTrue(any(a.startswith('--file=') for a in captured['args']));self.assertNotIn('--rate',captured['args'])
            narrate.engine_piper('Hallo',out,{'id':'de.onnx','speed':1.25},'de')
            self.assertEqual(captured['args'][1:4],['--model','de.onnx','--length_scale']);self.assertEqual(captured['args'][4],'0.8');self.assertEqual(captured['kw']['input'],'Hallo')
            narrate.engine_say('-dash start',out,{'id':'Thomas'},'fr')
            self.assertEqual(captured['args'][-2:],['--','-dash start'])
        requests=[]
        def fake_post(url,body,headers,timeout=120):requests.append((url,body,headers));return b'RIFF'
        with tempfile.TemporaryDirectory() as d, patch.object(narrate,'http_post',side_effect=fake_post), patch.object(narrate,'to_wav',lambda s,o:None), \
             patch.dict(narrate.os.environ,{'OPENAI_API_KEY':'k1','ELEVENLABS_API_KEY':'k2'}):
            out=Path(d)/'l.wav'
            narrate.engine_openai('Bonjour',out,{'id':'alloy','style':'Lively'},'fr','strong')
            url,body,headers=requests[-1]
            self.assertEqual(url,'https://api.openai.com/v1/audio/speech');self.assertEqual(headers['Authorization'],'Bearer k1')
            self.assertEqual((body['model'],body['voice'],body['input'],body['response_format']),('gpt-4o-mini-tts','alloy','Bonjour','wav'))
            self.assertIn('Lively',body['instructions']);self.assertIn('Confident',body['instructions'])
            narrate.engine_openai('Bonjour',out,{'model':'tts-1'},'fr')
            self.assertNotIn('instructions',requests[-1][1])                                                   # tts-1 takes no instructions
            narrate.engine_elevenlabs('Hola',out,{'id':'v9','speed':1.6},'es','soft')
            url,body,headers=requests[-1]
            self.assertEqual(url,'https://api.elevenlabs.io/v1/text-to-speech/v9?output_format=mp3_44100_128');self.assertEqual(headers['xi-api-key'],'k2')
            self.assertEqual(body['voice_settings']['speed'],1.2);self.assertEqual(body['voice_settings']['stability'],0.7);self.assertEqual(body['model_id'],'eleven_multilingual_v2')
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg needed')
    def test_measure_place_fit_level_match_and_mix(self):
        narrate=module('narrate');mixer=module('mix_audio')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'assets/narration').mkdir(parents=True);(root/'assets/sfx').mkdir()
            (root/'DIRECTION.md').write_text('# D\nParce que.\n| # | Plan |\n|---|---|\n| 1 | s1 |\n| 2 | s2 |\n')
            speech_like(root/'assets/narration/a.wav',2.0,amp=0.3);speech_like(root/'assets/narration/b.wav',4.0,amp=0.08)   # b: quiet, and too long for a 4 s shot
            stereo_tone(root/'assets/sfx/click.wav',0.3,880,1)
            m=narrate.measure(root/'assets/narration/a.wav')
            self.assertAlmostEqual(m['speechStart'],0.25,delta=0.03);self.assertAlmostEqual(m['speechEnd'],2.25,delta=0.03)
            (root/'plan.json').write_text(json.dumps(self.plan()))
            quiet=lambda:contextlib.ExitStack()
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(ValueError):narrate.narrate(root/'plan.json')               # does not fit without --fit-shots
                report=narrate.narrate(root/'plan.json',fit=True)
            plan=json.loads((root/'plan.json').read_text());a,b=plan['narration']['lines'];s2=plan['shots'][1]
            self.assertAlmostEqual(a['start']+a['speechStart'],0.35,delta=0.03)                     # first word lands lead seconds into the shot
            self.assertGreaterEqual(s2['end']-(b['start']+b['speechEnd']),0.59)                     # air before the cut
            self.assertGreater(plan['duration'],7);self.assertAlmostEqual(plan['duration'],s2['end'],delta=1e-6)
            self.assertEqual(plan['audio']['cues'][0]['at'],0.5)                                    # cue in an unmoved shot stays put
            gains={r['id']:r['gainDb'] for r in report['lines']}
            self.assertGreater(gains['b']-gains['a'],8)                                            # the quiet line is lifted to the same spoken level
            self.assertTrue((root/'assets/narration.wav').is_file() and (root/'evidence/narration.json').is_file())
            stereo_tone(root/'assets/music.wav',plan['duration']+0.5,220)
            with contextlib.redirect_stdout(io.StringIO()):mixer.mix(root/'plan.json')
            mix=json.loads((root/'evidence/audio-mix.json').read_text())
            self.assertEqual([l['id'] for l in mix['narration']['lines']],['a','b'])
            self.assertTrue(any(w['kind']=='narration' and w['db']==9 for w in mix['ducking']['windows']))
            out=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(root/'assets/master.wav')],capture_output=True,text=True).stdout
            self.assertAlmostEqual(float(out),plan['duration'],delta=0.05)
            result=delivery.check(plan,project_dir=root,mix_report=root/'evidence/audio-mix.json',plan_path=root/'plan.json')
            self.assertEqual(result['errors'],[])
            plan['shots'][1]['end']=round(plan['shots'][1]['end']-1,3);plan['duration']=plan['shots'][1]['end']
            self.assertTrue(any('narrate.py --fit-shots' in e for e in delivery.check(plan,project_dir=root,plan_path=root/'plan.json')['errors']))
            (root/'plan.json').write_text(json.dumps(plan))
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError):narrate.narrate(root/'plan.json',dry=True)   # dry run reports the misfit through its exit code
            self.assertEqual(json.loads((root/'plan.json').read_text())['shots'][1]['end'],plan['shots'][1]['end'])   # ...and changes nothing
class FirstFrame(unittest.TestCase):
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg needed')
    def test_blank_opening_fails_production(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            blank=root/'blank.mp4';busy=root/'busy.mp4'
            for src,out in [('color=c=0xfafaf9:s=640x360:r=30:d=1',blank),('testsrc2=s=640x360:r=30:d=1',busy)]:
                subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',src,'-pix_fmt','yuv420p',str(out)],check=True)
            self.assertTrue(all(r<0.004 for r in delivery.first_frame_metrics(blank)['inkRatio']))
            self.assertTrue(all(r>0.004 for r in delivery.first_frame_metrics(busy)['inkRatio']))
class Mix(unittest.TestCase):
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg needed')
    def test_outputs_are_capped_to_film_duration(self):
        import math,struct,wave
        mixer=module('mix_audio')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'assets/sfx').mkdir(parents=True)
            def tone(path,seconds,freq,channels=2):
                rate=48000;frames=[]
                for i in range(int(rate*seconds)):
                    v=int(0.3*32767*math.sin(2*math.pi*freq*i/rate));frames+= [v]*channels
                with wave.open(str(path),'wb') as w:w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes(struct.pack('<%dh'%len(frames),*frames))
            tone(root/'assets/music.wav',3.2,220);tone(root/'assets/sfx/a.wav',0.4,880);tone(root/'assets/sfx/b.wav',1.5,660,1)
            actions=[{'id':f'k{i}','at':0.2+i*0.3,'action':'key','soundRequired':True} for i in range(8)]
            cues=[{'at':a['at'],'actionId':a['id'],'file':'assets/sfx/'+('a' if i%2 else 'b')+'.wav','gain':0.8,'role':'sfx','kind':'click'} for i,a in enumerate(actions)]
            plan={'duration':3,'fps':30,'shots':[{'id':'s','start':0,'end':3,'actions':actions}],'audio':{'music':{'file':'assets/music.wav','gain':0.6},'cues':cues,'ducking':{'enabled':True}}}
            (root/'plan.json').write_text(json.dumps(plan))
            with contextlib.redirect_stdout(io.StringIO()):mixer.mix(root/'plan.json')
            for name in ['sfx-stem.wav','music-ducked.wav','master.wav']:
                out=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(root/'assets'/name)],capture_output=True,text=True).stdout
                self.assertAlmostEqual(float(out),3.0,delta=0.05,msg=name)
class Landmarks(unittest.TestCase):
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg needed')
    def test_onset_and_peak(self):
        import math,struct,wave
        landmarks=module('sfx_landmarks').landmarks
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'hit.wav';rate=48000;data=[]
            for i in range(rate):
                t=i/rate;amp=0 if t<0.25 else (0.4 if t<0.5 else 0.9*math.exp(-(t-0.5)*8))
                data.append(int(amp*32767*math.sin(2*math.pi*440*t)))
            with wave.open(str(f),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(struct.pack('<%dh'%len(data),*data))
            r=landmarks(f)
            self.assertAlmostEqual(r['onset'],0.25,delta=0.01)
            self.assertAlmostEqual(r['peak'],0.5,delta=0.01)
            self.assertAlmostEqual(r['peakDbfs'],-0.9,delta=0.3)

if __name__=='__main__':unittest.main()
