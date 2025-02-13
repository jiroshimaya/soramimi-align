# soramimi-align
〇〇で歌ってみたシリーズの元歌詞と空耳歌詞をalignmentするプログラムです。
# 使い方

```sh
# 各コマンドの詳細はpyproject.tomlを参照
# ドラフト作成
uv run task make_draft_sample
# モウラのアライン
uv run task align_mora_sample
# 単語のアライン
uv run task align_word_sample
```

## 入出力例

最終的にほしい出力はaling_mora.pyやalign_word.pyの出力ですが、読みや文節位置などの推定失敗を修正しやすいように、make_draft.pyの出力を途中に挟みます。

- 替え歌歌詞元ファイル

```sample_lyric.txt
宇佐美 小石博孝
うさぎ追いしかの山

小塚 辻勇夫 河
こぶな釣りしかの川

シューメーカー 熊野輝光
夢は 今もめぐりて

夏目隆司 古田 荘
わすれがたきふるさと

選手一覧
宇佐美一夫
小石博孝
小塚弘司
辻勇夫(辻功)
河文雄
マット・シューメーカー
熊野輝光
夏目隆司
古田敦也
荘勝雄
```

- make_draft.pyの出力

```:sample_draft.txt
宇佐美 小石博孝
ウサミ コイシヒロタカ
うさぎ 追い しか の 山
ウサギ/p オイ/p シカ ノ ヤマ/p

小塚 辻勇夫 河
コヅカ ツジイサオ カワ
コブナ 釣り しか の 川
コブナ/p ツリ/p シカ ノ カワ/p

シューメーカー 熊野輝光
シューメーカー クマノヒロミツ
夢 は 今 も めぐり て
ユメ/p ワ イマ/p モ メグリ/p テ

夏目隆司 古田 荘
ナツメタカシ フルタ ソウ
忘れ がたき ふるさと
ワスレ/p ガタキ フルサト/p
```

- align_mora.pyの出力

```:sample_mora.csv
parody_mora,is_parody_word_start,is_parody_word_end,original_mora,is_original_phrase_start,is_original_phrase_end,is_original_word_start,is_original_word_end,line_id,input_file_path,parody_vowel,original_vowel,parody_consonant,original_consonant,parody_word_surface,original_word_surface
ウ,True,False,ウ,True,False,True,False,0,data/output/sample_draft.txt,u,u,,,宇佐美,うさぎ
サ,False,False,サ,False,False,False,False,0,data/output/sample_draft.txt,a,a,s,s,,
ミ,False,True,ギ,False,True,False,True,0,data/output/sample_draft.txt,i,i,mj,gj,,
コ,True,False,オ,True,False,True,False,0,data/output/sample_draft.txt,o,o,k,,小石博孝,追い
イ,False,False,イ,False,False,False,True,0,data/output/sample_draft.txt,i,i,,,,
シ,False,False,シ,False,False,True,False,0,data/output/sample_draft.txt,i,i,ɕ,ɕ,,しか
ヒ,False,False,カ,False,False,False,True,0,data/output/sample_draft.txt,i,a,ç,k,,
ロ,False,False,ノ,False,True,True,True,0,data/output/sample_draft.txt,o,o,r,n,,の
タ,False,False,ヤ,True,False,True,False,0,data/output/sample_draft.txt,a,a,t,j,,山
カ,False,True,マ,False,True,False,True,0,data/output/sample_draft.txt,a,a,k,m,,
コ,True,False,コ,True,False,True,False,1,data/output/sample_draft.txt,o,o,k,k,小塚,コブナ
ヅ,False,False,ブ,False,False,False,False,1,data/output/sample_draft.txt,u,u,z,b,,
カ,False,True,ナ,False,True,False,True,1,data/output/sample_draft.txt,a,a,k,n,,
ツ,True,False,ツ,True,False,True,False,1,data/output/sample_draft.txt,u,u,ts,ts,辻勇夫,釣り
ジ,False,False,リ,False,False,False,True,1,data/output/sample_draft.txt,i,i,ʒ,rj,,
イ,False,False,シ,False,False,True,False,1,data/output/sample_draft.txt,i,i,,ɕ,,しか
サ,False,False,カ,False,False,False,True,1,data/output/sample_draft.txt,a,a,s,k,,
オ,False,True,ノ,False,True,True,True,1,data/output/sample_draft.txt,o,o,,n,,の
カ,True,False,カ,True,False,True,False,1,data/output/sample_draft.txt,a,a,k,k,河,川
ワ,False,True,ワ,False,True,False,True,1,data/output/sample_draft.txt,a,a,w,w,,
シュ,True,False,ユ,True,False,True,False,2,data/output/sample_draft.txt,u,u,ɕ,j,シューメーカー,夢
ー,False,False,,False,False,False,False,2,data/output/sample_draft.txt,:,,,,,
メ,False,False,メ,False,False,False,True,2,data/output/sample_draft.txt,e,e,m,m,,
ー,False,False,,False,False,True,True,2,data/output/sample_draft.txt,:,,,,,
カ,False,False,ワ,False,True,True,True,2,data/output/sample_draft.txt,a,a,k,w,,は
ー,False,True,イ,True,False,True,False,2,data/output/sample_draft.txt,:,i,,,,今
ク,True,False,,False,False,False,False,2,data/output/sample_draft.txt,u,,k,,熊野輝光,
マ,False,False,マ,False,False,False,True,2,data/output/sample_draft.txt,a,a,m,m,,
ノ,False,False,モ,False,True,True,True,2,data/output/sample_draft.txt,o,o,n,m,,も
ヒ,False,False,メ,True,False,True,False,2,data/output/sample_draft.txt,i,e,ç,m,,めぐり
ロ,False,False,グ,False,False,False,False,2,data/output/sample_draft.txt,o,u,r,g,,
ミ,False,False,リ,False,False,False,True,2,data/output/sample_draft.txt,i,i,mj,rj,,
ツ,False,True,テ,False,True,True,True,2,data/output/sample_draft.txt,u,e,ts,t,,て
ナ,True,False,ワ,True,False,True,False,3,data/output/sample_draft.txt,a,a,n,w,夏目隆司,忘れ
ツ,False,False,ス,False,False,False,False,3,data/output/sample_draft.txt,u,u,ts,s,,
メ,False,False,レ,False,False,False,True,3,data/output/sample_draft.txt,e,e,m,r,,
タ,False,False,ガ,False,False,True,False,3,data/output/sample_draft.txt,a,a,t,g,,がたき
カ,False,False,タ,False,False,False,False,3,data/output/sample_draft.txt,a,a,k,t,,
シ,False,True,キ,False,True,False,True,3,data/output/sample_draft.txt,i,i,ɕ,kj,,
フ,True,False,フ,True,False,True,False,3,data/output/sample_draft.txt,u,u,ɸ,ɸ,古田,ふるさと
ル,False,False,ル,False,False,False,False,3,data/output/sample_draft.txt,u,u,r,r,,
タ,False,True,サ,False,False,False,False,3,data/output/sample_draft.txt,a,a,t,s,,
ソ,True,False,ト,False,True,False,True,3,data/output/sample_draft.txt,o,o,s,t,荘,
ウ,False,True,,False,True,False,True,3,data/output/sample_draft.txt,u,,,,,
```

- align_word.pyの出力（シューメーカー、クマノヒロミツの対応付けは少しミスっている）

```:sample_word.py
parody_mora,is_parody_word_start,is_parody_word_end,original_mora,is_original_phrase_start,is_original_phrase_end,is_original_word_start,is_original_word_end,line_id,input_file_path,parody_vowel,original_vowel,parody_consonant,original_consonant,parody_word_surface,original_word_surface
ウサミ,True,True,ウサギ,True,True,True,True,0,data/output/sample_draft.txt,,,,,宇佐美,うさぎ
コイシヒロタカ,True,True,オイシカノヤマ,True,True,True,True,0,data/output/sample_draft.txt,,,,,小石博孝,追いしかの山
コヅカ,True,True,コブナ,True,True,True,True,1,data/output/sample_draft.txt,,,,,小塚,コブナ
ツジイサオ,True,True,ツリシカノ,True,True,True,True,1,data/output/sample_draft.txt,,,,,辻勇夫,釣りしかの
カワ,True,True,カワ,True,True,True,True,1,data/output/sample_draft.txt,,,,,河,川
シューメーカー,True,True,ユメワイ,True,False,True,False,2,data/output/sample_draft.txt,,,,,シューメーカー,夢は今
クマノヒロミツ,True,True,マモメグリテ,False,True,False,True,2,data/output/sample_draft.txt,,,,,熊野輝光,今もめぐりて
ナツメタカシ,True,True,ワスレガタキ,True,True,True,True,3,data/output/sample_draft.txt,,,,,夏目隆司,忘れがたき
フルタ,True,True,フルサ,True,False,True,False,3,data/output/sample_draft.txt,,,,,古田,ふるさと
ソウ,True,True,ト,False,True,False,True,3,data/output/sample_draft.txt,,,,,荘,ふるさと
```


# 開発者向け

```
uv run test
```