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

Tout tourne en local et gratuitement. Seuls les plans d'ambiance demandent une clé API gratuite (Pixabay ou Pexels).

## Réglages de l'environnement Claude Code (cloud)

Dans claude.ai/code, ouvre le menu de l'environnement (en haut de la session), puis **Modifier l'environnement** :

1. **Accès réseau** : choisis **Complet**. C'est le plus simple. Si tu préfères **Personnalisé**, ajoute ces domaines et garde les gestionnaires de paquets autorisés :
   - `lrclib.net` (paroles officielles)
   - `pixabay.com` et `cdn.pixabay.com` (plans d'ambiance)
   - `api.pexels.com` et `videos.pexels.com` (seulement si tu as une clé Pexels)
2. **Variables d'environnement** (plus bas dans la même fenêtre) : `PIXABAY_API_KEY=<ta clé>`. La clé est gratuite et donnée tout de suite sur https://pixabay.com/api/docs/ (section « Parameters », une fois connecté). `PEXELS_API_KEY` marche aussi.
3. **Script de configuration** : tu peux le laisser vide. Le hook `SessionStart` (`.claude/settings.json`) installe tout au démarrage de chaque session.

Sans ces réglages, l'outil marche quand même : il garde la transcription et utilise le dossier `broll/` ou la vidéo source comme fond.

## Mettre tes propres plans d'ambiance

Tu peux aussi déposer des clips (MP4/MOV) dans `broll/` : ils seront utilisés quand aucune clé n'est définie. Sur GitHub, ouvre le dossier `broll`, puis « Add file » → « Upload files ». Les fichiers de plus de 25 Mo ne passent pas par cette page.
