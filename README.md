# Robotics AI Research News Site

毎朝5時（日本時間）に、**機械・ロボット研究で使いやすいAIニュース / 論文情報**を最大20件集め、個人用の静的Webサイトとして更新するGitHub Pagesベースの仕組みです。

メール送信をやめたため、メールアドレス、SMTPユーザー名、SMTPパスワード、アプリパスワードは不要です。

## 仕組み

- arXiv Robotics、arXiv AI / ML / CV、IEEE Spectrum Robotics、MIT Robotics、ScienceDaily RoboticsなどのRSSを取得します。
- ロボット・機械系キーワードを強く優先し、研究・論文・大学・データセット・ベンチマークなどのキーワードも加点します。
- 株価、決算、IPO、広告、芸能、暗号資産など、研究用途から遠い話題は減点します。
- `public/index.html` に個人用ニュースページを生成します。
- GitHub Actionsが生成結果をGitHub Pagesへデプロイします。
- `.github/workflows/ai-news-digest.yml` のcronで毎日05:00 JSTに実行します。

## あなたが行う設定手順

### 1. GitHub Pagesを有効化する

リポジトリの **Settings > Pages** を開き、Build and deployment の Source を **GitHub Actions** に設定します。

**リスク**

- GitHub Pagesで公開すると、リポジトリやプランの設定によってはページがインターネット上に公開されます。
- ページにはあなたのメールアドレスは出ませんが、ロボットAIに関心があることや、追っている研究分野は推測される可能性があります。
- 完全に非公開にしたい場合は、GitHub Pagesではなくローカル生成やアクセス制限付きホスティングを検討してください。

### 2. 手動実行でサイトを作る

GitHubの **Actions > Robotics AI news site > Run workflow** から手動実行します。成功するとGitHub Pagesに `index.html` がデプロイされます。

**リスク**

- 外部RSSサイトの一時障害で、記事数が少なくなることがあります。
- GitHub Pagesの初回反映には数分かかる場合があります。
- 公開URLを共有すると、他の人も同じページを閲覧できます。

### 3. GitHub PagesのURLを確認する

手動実行が成功したら、**Settings > Pages** に表示されるURLを開きます。ページタイトルは「ロボットAI研究ニュース」です。

**リスク**

- ページが見つからない場合、Pages設定がGitHub Actionsになっていない可能性があります。
- ブラウザやGitHub Pagesのキャッシュで、更新直後に古い内容が表示される場合があります。

### 4. 必要に応じてGitHub Variablesを登録する

**Settings > Secrets and variables > Actions > Variables** で以下を調整できます。メール送信用のSecretsは不要です。

| 名前 | 説明 |
| --- | --- |
| `AI_NEWS_FEEDS` | 追加・置き換えしたいRSS URL。カンマ区切り |
| `AI_NEWS_LOOKBACK_HOURS` | 何時間前までの記事を対象にするか。既定値は `36` |
| `AI_NEWS_MIN_SCORE` | 低関連度の記事を除外するしきい値。既定値は `0` |
| `AI_NEWS_LIMIT` | Webページに表示する最大記事数。既定値は `20` |

**リスク**

- RSSを増やしすぎると、取得時間が伸び、GitHub Actionsの実行時間が増えます。
- 信頼性の低いRSSを追加すると、誤情報や広告記事が混ざります。
- しきい値を高くしすぎると、有用な記事も除外されます。
- 表示件数を増やしすぎると、ページが読みにくくなります。

### 5. 内容が研究テーマに合っているか確認する

最初の数日は、ページに出る記事が研究テーマに合っているか確認してください。合わない場合は `AI_NEWS_FEEDS`、`AI_NEWS_MIN_SCORE`、またはスクリプト内のキーワードを調整します。

**リスク**

- キーワード方式なので、完全な推薦精度はありません。
- 「robot」という単語があっても、実験・制御・機械設計に直接関係しない記事が混ざることがあります。
- 逆に、重要な論文でもタイトルや要約にロボット系キーワードが少ないと漏れることがあります。

### 6. 本運用する

手動実行で問題がなければ、そのまま毎朝5時に自動更新されます。GitHub Actionsの実行履歴を定期的に確認してください。

**リスク**

- GitHub Actionsのcronは厳密なリアルタイム実行ではなく、数分遅れる場合があります。
- 外部RSSの仕様変更で取得できなくなる可能性があります。
- GitHub Pagesの公開範囲を誤解すると、個人用のつもりのページが第三者から見える可能性があります。

## ローカル確認

```bash
pip install -r requirements.txt
python src/ai_news_digest.py --output-dir public
python -m http.server 8000 --directory public
```

その後、ブラウザで `http://localhost:8000` を開くと、生成されたニュースサイトを確認できます。

**リスク**

- ローカルサーバーは基本的に自分のPC内確認用ですが、ネットワーク設定によっては同じLAN内から見える場合があります。
- 公開したくない情報を `public/` に手動で置かないでください。

## カスタマイズの考え方

- ロボットのハード寄りにしたい場合: `actuator`、`sensor`、`mechatronics`、`kinematics`、`dynamics` などを増やします。
- 制御・移動ロボット寄りにしたい場合: `control`、`motion planning`、`path planning`、`SLAM`、`navigation` を重視します。
- 画像認識・マルチモーダル寄りにしたい場合: `vision`、`multimodal`、`embodied`、`simulation` を重視します。
- 論文中心にしたい場合: `AI_NEWS_FEEDS`をarXivや学会RSS中心にします。

## メール方式からWebサイト方式に変えた理由

- メールアドレスやSMTPパスワードをGitHub Secretsに登録する必要がなくなります。
- 通知先の誤設定によるメール誤送信がなくなります。
- スマホやPCのブラウザから同じページを見られます。
- 一方で、GitHub Pagesの公開範囲には注意が必要です。個人用でもURLを知っている人が閲覧できる場合があります。
