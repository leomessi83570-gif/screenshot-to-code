# lyricgen — vidéos paroles TikTok automatiques

Tu envoies un extrait de son (vidéo TikTok, enregistrement d'écran, MP3) + l'artiste et le titre.
L'outil sort des vidéos 1080×1920 prêtes à poster, avec les paroles mot par mot calées sur la voix, des plans d'ambiance de nuit et la légende.

| Style | Rendu |
|---|---|
| `damso` | un mot à la fois, gros, bleu |
| `bello` | mot blanc, dernier mot de la ligne en violet, ligne complète en sous-titre |
| `cream` | typo énorme crème (façon Kerozen) |

## Utilisation la plus simple : avec Claude

Dans une session Claude Code sur ce repo, envoie le fichier et écris par exemple :

> fais la vidéo, c'est Groseille de Timar

Claude suit la skill `lyric-video` : il lance la génération, vérifie le rendu et les paroles, puis t'envoie les MP4 + la légende. Tu n'as plus qu'à poster.

## En ligne de commande

```bash
scripts/setup.sh                       # une seule fois (automatique dans Claude Code)
.venv/bin/python lyricgen.py make clip.mp4 --artist "Timar" --title "Groseille"
```

Options utiles :
- `--style damso bello cream` : les styles à générer
- `--broll-query "dubai night" "night drive"` : les recherches de plans d'ambiance (Pexels)
- `--broll-dir mes_clips/` : utiliser tes propres clips
- `--start 5 --end 20` : ne garder qu'un passage

Si un mot est faux : corrige `projects/<nom>/lyrics.txt`, puis lance
`lyricgen.py align projects/<nom>` et `lyricgen.py render projects/<nom> --style damso bello`.

## Comment ça marche

1. La voix est séparée de l'instru (modèle UVR MDX-Net).
2. La voix est transcrite en français avec le moment exact de chaque mot (NVIDIA Parakeet TDT v3, en local).
3. Si `lrclib.net` est accessible, les paroles officielles remplacent la transcription. L'outil retrouve tout seul le passage chanté dans le clip.
4. Les plans d'ambiance changent à chaque ligne, l'image est assombrie, puis les mots sont incrustés avec un effet « pop » et le son d'origine est gardé.

Tout tourne en local et gratuitement. Seuls les plans Pexels demandent une clé API, elle aussi gratuite.

## Réglages de l'environnement Claude Code (cloud)

Dans claude.ai/code, ouvre le menu de l'environnement dans la barre de titre de la session, puis **Edit** :

1. **Network access → Custom**, avec ces domaines dans **Allowed domains** (garde la case « package managers » cochée) :
   - `lrclib.net` (paroles officielles)
   - `api.pexels.com` et `videos.pexels.com` (plans d'ambiance)
   - `github.com`, `objects.githubusercontent.com` et `release-assets.githubusercontent.com` (modèles et polices)
2. **Environment variables** : `PEXELS_API_KEY=<ta clé>`. La clé est gratuite sur https://www.pexels.com/api/
3. Rien d'autre : le hook `SessionStart` (`.claude/settings.json`) installe tout au démarrage de chaque session.

Sans ces réglages, l'outil marche quand même : il garde la transcription et utilise le dossier `broll/` ou la vidéo source comme fond.
