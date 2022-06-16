from PIL import Image
import subprocess
import soundfile
import chardet
import shutil
import glob
import sys
import os
import re

#[!]なにもかも解析途中です これをそのまま他作品に使い回さないでください

same_hierarchy = (os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
#same_hierarchy = os.path.join(same_hierarchy,'SBridge')#debug

#grpo_exは不要
DIR_1 = os.path.join(same_hierarchy,'1')
DIR_BGM = os.path.join(same_hierarchy,'bgm')
DIR_GRPE = os.path.join(same_hierarchy,'grpe')
DIR_GRPO = os.path.join(same_hierarchy,'grpo')
DIR_GRPO_BU = os.path.join(same_hierarchy,'grpo_bu')
DIR_GRPS = os.path.join(same_hierarchy,'grps')
DIR_SCR = os.path.join(same_hierarchy,'scr')
DIR_VOICE = os.path.join(same_hierarchy,'voice')
DIR_WAV = os.path.join(same_hierarchy,'wav')

DIR_SCR_DEC = os.path.join(same_hierarchy,'scr_dec')
DEFAULT_TXT = os.path.join(same_hierarchy,'default.txt')
EXE_GSC = os.path.join(same_hierarchy,'gscScriptCompAndDecompiler.exe')


effect_startnum=10
effect_list=[]

sp_reverse = 50


def effect_edit(t,f):
	global effect_list

	list_num=0
	if re.fullmatch(r'[0-9]+',t):#timeが数字のみ＝本処理

		for i, e in enumerate(effect_list,effect_startnum+1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			effect_list.append([t,f])
			list_num = len(effect_list)+effect_startnum

	return str(list_num)


def music_cnv():
	d1 = glob.glob(os.path.join(DIR_WAV, '*.*'))
	d2 = glob.glob(os.path.join(DIR_BGM, '*.*'))
	d3 = glob.glob(os.path.join(DIR_VOICE, '*.*'))
	d4 = glob.glob(os.path.join(DIR_1, '*.*'))
	for i in (d1+d2+d3+d4):
		dd = (os.path.dirname(i) + '_dec')
		dp = (os.path.join(dd, os.path.splitext(os.path.basename(i))[0] + '.wav'))
		os.makedirs(dd, exist_ok=True)
		soundfile.write(dp, soundfile.read(i)[0], soundfile.read(i)[1])


def image_cnv():
	for p in glob.glob(os.path.join(DIR_GRPO, '*.png')):
		n = (os.path.splitext(os.path.basename(p))[0])

		if (int(n) >= 9000) and (int(n) < 9100):
			result = (os.path.join(os.path.dirname(p), n + '_' + os.path.splitext(p)[1]))
			p2 = (os.path.join(os.path.dirname(p), str(int(n)+100)+os.path.splitext(p)[1]))#名前に+100
			
			im_p = Image.open(p)
			im_p2 = Image.open(p2)
			
			im = Image.new('RGBA', (im_p.width*3, im_p.height))
			im.paste(im_p, (0, 0))
			im.paste(im_p2, (im_p.width, 0))
			im.paste(im_p2, (im_p.width*2, 0))

			im.save(result)


def text_cnv():
	with open(DEFAULT_TXT) as f:
		txt = f.read()

	for p in glob.glob(os.path.join(DIR_SCR_DEC, '*.txt')):
		line_mode = False
		
		with open(p, 'rb') as f:
			char_code = chardet.detect(f.read())['encoding']

		with open(p, encoding=char_code, errors='ignore') as f:

			name = os.path.splitext(os.path.basename(p))[0]
			txt += '\n;--------------- '+ name +' ---------------\n*'+ name.replace('.', '_') +'\n\n'

			for line in f:
				line_def = line
				line_hash = re.search(r'#([A-z0-9]+?)\n', line)
				line_snr = re.search(r'(\^g[0-9]{3})(.+?)\n', line)

				JUMP_var1 = re.search(r'\@([A-z0-9]+)', line)
				
				if re.search('^\n', line):#空行
					pass#そのまま放置

				elif line_hash:
					line = r';' + line

					if line_mode == 'scenario':
						line = '\\\n' + line
					
					line_mode = line_hash[1]
					
				elif JUMP_var1:
					line = '*JUMP_'+name.replace('.', '_')+'_'+JUMP_var1[1]+'\n'

					if line_mode == 'scenario':
						line = '\\\n' + line

					line_mode = False

				elif line_snr:
					line = 'name_img "gf'+line_snr[1][2:]+'"\n'+line_snr[2]+'\n'
					line_mode = 'scenario'

				else:#どれにも当てはまらない、よく分からない場合
					if line_mode == 'scenario':
						pass

					else:
						JUMP_var2 = re.search(r'\[([A-z0-9]+?)\]', line)

						if (line_mode == 'JUMP') and JUMP_var2:
							line = 'goto *JUMP_'+name.replace('.', '_')+'_'+JUMP_var2[1]+'\n'

						elif line_mode == 'MESSAGE':#メッセージ
							MESS_var1 = re.search(r'\[0, ([0-9]+?), 0, 0, -1, -1, (1|0)\]', line)

							if MESS_var1[1] == '0':
								line = ';voice ""\n'
							else:
								MESS_b = bool(int(MESS_var1[1]) > 10000)
								MESS = MESS_var1[1][1:] if MESS_b else MESS_var1[1]
								line = 'voice "'+MESS+'.wav",'+str(int(MESS_b))+'\n'

						elif line_mode == '66':#メッセージ2
							MESS_var2 = re.search(r'\[([0-9]+?), 0, 0, 0\]', line)

							if MESS_var2:
								MESS_b = bool(int(MESS_var2[1]) > 10000)
								MESS = MESS_var2[1][1:] if MESS_b else MESS_var2[1]
								line = 'voice "'+MESS+'.wav",'+str(int(MESS_b))+'\n'

						elif line_mode == '60':#BGM
							BGM_var = re.search(r'\[([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)
							line = 'bgm "bgm_dec\\Track'+(BGM_var[1]).zfill(2)+'.wav"\n'

						elif line_mode == 'IMAGE_DEF':#スプライト
							DEF_var = re.search(r'\[([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)
							line = 'tati '+str(sp_reverse-int(DEF_var[1]))+','+DEF_var[2]+','+DEF_var[3]+','+DEF_var[4]+'\n'

						elif line_mode == '36':#スプライト除去
							SP_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)
							line = 'vsp '+str(sp_reverse-int(SP_var[1]))+','+SP_var[2]+'\n'

						elif line_mode == 'PAUSE':#ウェイト
							PAUSE_var = re.search(r'\[([0-9]+?)\]', line)
							line = 'wait '+PAUSE_var[1]+'00\n'

						elif line_mode == '6144':#背景だよ 501が背景名/502がエフェクト/503で開始？
							BG_var = re.search(r'\[([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)

							if BG_var[2] == '501':
								line = 'mov $51,"grpe\\'+(BG_var[3]).zfill(4)+'.png"\n'

							elif BG_var[2] == '502':
								line = 'mov %52,'+effect_edit('500', BG_var[3])+':bg_change\n'

						elif line_mode == '62':#効果音だよ
							SE_var = re.search(r'\[([0-9]+?)\]', line)
							line = 'dwave 1,"wav_dec\\'+(SE_var[1]).zfill(4)+'.wav"\n'

						elif line_mode == '61':#BGMのフェードアウト ホントはSEにもやったほうがいいけど面倒なので放置
							FADE_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)
							line = 'bgmfadeout_def '+(FADE_var[2])+'\n'

						elif line_mode == '24':# flush [x100ミリ秒,X]
							FL_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)
							line = 'flush '+(FL_var[1])+'00\n'

						elif line_mode == '23':# quake [x100ミリ秒,強さ(0有るので+1推奨),X,X]
							QU_var = re.search(r'\[([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)
							line = 'quake '+str((int(QU_var[2])+1)*2)+','+(QU_var[1])+'00\n'

						elif line_mode == '43':
							ES_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)

							if ES_var[1] != '0':#画像素材の関係で仕方なくコメントアウトしてます
								line = ';lsp 52,"grps\\es'+ES_var[1].zfill(3)+'.png",0,0:print 10\n'
							else:
								line = ';csp 52:print 10\n'

						elif line_mode == '64':
							line = 'csp 11:print 1\n'

						elif line_mode == 'IMAGE_GET':
							BG_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)
							line = 'bg "grpe\\'+BG_var[1].zfill(4)+'.png",10\n'

						elif line_mode == 'IMAGE_SET':
							line = 'csp_all\n'

						elif line_mode == '15':#gosub的な?
							BG_var = re.search(r'\[([0-9]+?), -1, ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)
							if(int(BG_var[1]) > 1000):
								line = 'gosub *'+BG_var[1]+'_gsc\n'


						if line_def == line:
							line = r';' + line#エラー防止の為コメントアウト
						
						line_mode = False

				txt += line

			txt += '\nbgmstop:dwavestop 0:dwavestop 1:csp -1\nreturn\n'

	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換

		if (int(e[1]) >= 24) or (int(e[1]) <= 11):#efXX.pngは11~24なのでそれ以外の指定はとりあえずフェードにしてごまかす
			add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'

		else:
			add0txt_effect +='effect '+str(i)+',18,'+e[0]+',"grps\\ef'+e[1]+'.png"\n'

	#-----ガ バ ガ バ 修 正-----
	# 第一章
	txt = txt.replace(r';モーガンの言', r'name_img "gf003":select "モーガンの言いなりにはならない！",*JUMP_2011_gsc_9,"いちかばちか、やってみる！",*JUMP_2011_gsc_11;')
	txt = txt.replace('\n*JUMP_2011_gsc_16', '\ngoto *GAMEOVER01\n*JUMP_2011_gsc_16')
	txt = txt.replace(r';青', r'name_img "gf003":select "黄色いマスコン",*JUMP_2011_gsc_16,"青いマスコン",*JUMP_2011_gsc_18,"緑のマスコン",*JUMP_2011_gsc_19;')
	txt = txt.replace(r';先端', r'name_img "gf003":select "先端",*JUMP_2011_gsc_25,"中央",*JUMP_2011_gsc_27,"根元",*JUMP_2011_gsc_28;')
	txt = txt.replace('\ntati 25,2001,0,0', '\ntati 11,2001,0,0')#これやんないと一部の雪が降る場面で唐突にモーガン出てくるの草
	txt = txt.replace(r';とにかく進', r'name_img "gf003":select "とにかく進む",*JUMP_2011_gsc_34,"進めるもんか",*JUMP_2011_gsc_36;')
	txt = txt.replace('\n*JUMP_2011_gsc_36', '\ngoto *GAMEOVER01\n*JUMP_2011_gsc_36')
	txt = txt.replace('tati 21,1946,0,0', '')
	txt = txt.replace('\nまた会える？', 'csp 21:print 1\nまた会える？')
	# 第二章
	txt = txt.replace('呟いたチ', 'csp 21:print 1\n呟いたチ')
	txt = txt.replace('\n謎めいた魔', '\ncsp_all\n謎めいた魔')
	txt = txt.replace('tati 19,2001,65186,0', 'tati 24,2001,65186,0')
	txt = txt.replace('で掴んだ。\n', 'で掴んだ。\\\nname_img "gf003":select "黄色いマスコンを、奥へ倒す",*JUMP_2037_gsc_3,"黄色いマスコンを、手前に引く",*JUMP_2037_gsc_5;')
	txt = txt.replace('\n*JUMP_2037_gsc_5', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_5')
	txt = txt.replace('ねえな？\n', 'ねえな？\\\nname_img "gf003":select "黄色いマスコンを、奥へ倒す",*JUMP_2037_gsc_8,"黄色いマスコンを、手前に引く",*JUMP_2037_gsc_10;')
	txt = txt.replace('\n*JUMP_2037_gsc_11', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_11')
	txt = txt.replace(';チョト・チェルパンに', 'name_img "gf003":select "チョト・チェルパンに同化する",*JUMP_2037_gsc_15,"チョグルに同化する",*JUMP_2037_gsc_17,"世界樹の根に同化する",*JUMP_2037_gsc_18;')
	txt = txt.replace('\n*JUMP_2037_gsc_17', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_17')
	txt = txt.replace('\n*JUMP_2037_gsc_19', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_19')
	txt = txt.replace(';チョグルを', 'name_img "gf003":select "チョグルを止める",*JUMP_2037_gsc_22,"チョグルに任せる",*JUMP_2037_gsc_24;')
	txt = txt.replace('\n*JUMP_2037_gsc_25', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_25')
	txt = txt.replace(';モ', 'name_img "gf003":select "モーガンに呼びかける",*JUMP_2037_gsc_28,"自分にできることをする",*JUMP_2037_gsc_30;')
	txt = txt.replace('\n*JUMP_2037_gsc_30', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_30')
	# 第三章
	txt = txt.replace(';白いマスコンの力を敵', 'name_img "gf003":select "白いマスコンの力を敵へ向ける",*JUMP_2060_gsc_3,"白いマスコンの力を自分に使う",*JUMP_2060_gsc_5;')
	txt = txt.replace('\n*JUMP_2060_gsc_5', '\ngoto *GAMEOVER03\n*JUMP_2060_gsc_5')
	txt = txt.replace(';ジェーンの心', 'name_img "gf003":select "ジェーンの心を読む",*JUMP_2060_gsc_8,"ジェーンの出方を考える",*JUMP_2060_gsc_10')
	txt = txt.replace('\n*JUMP_2060_gsc_10', '\ngoto *GAMEOVER03\n*JUMP_2060_gsc_10')
	# 第五章
	txt = txt.replace(';[15044, 999, 0, 0]', 'csp 10:print 1')
	# 第六章
	txt = txt.replace('tati 20,3152,0,0\n;#60', ';')
	txt = txt.replace('頬をくすぐり', 'tati 20,3152,0,0\n頬をくすぐり')
	txt = txt.replace('お幸せに！\n\\', 'お幸せに！\\\nname_img "gf003"\n')

	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)

	open(os.path.join(same_hierarchy,'0.txt'), 'w', errors='ignore').write(txt)
	

def file_check():
	c = True
	for p in [DIR_1, DIR_BGM, DIR_GRPE, DIR_GRPO, DIR_GRPO_BU,DIR_GRPS, DIR_SCR, DIR_VOICE, DIR_WAV, DEFAULT_TXT, EXE_GSC]:
		if not os.path.exists(p):
			print(p+ ' is not found!')
			c = False
	
	return c


def text_dec():
	os.makedirs(DIR_SCR_DEC, exist_ok=True)

	for p in glob.glob(os.path.join(DIR_SCR, '*.gsc')):
		n = (os.path.splitext(os.path.basename(p))[0])
		if int(n) >= 2000:
			subprocess.run([EXE_GSC, '-m', 'decompile', '-i', p], shell=True, cwd=DIR_SCR)

	for p in glob.glob(os.path.join(DIR_SCR, '*.txt')):
		shutil.move(p, DIR_SCR_DEC)


def junk_del():
	for d in [DIR_1, DIR_BGM, DIR_SCR, DIR_SCR_DEC, DIR_VOICE, DIR_WAV]:
		shutil.rmtree(d)
	

#-----本処理-----
if file_check():
	music_cnv()
	image_cnv()
	text_dec()
	text_cnv()
	junk_del()
