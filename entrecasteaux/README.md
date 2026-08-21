# Entrecasteaux — maquette de site communal

Page unique, sans build ni réseau. Ouvrez `index.html` dans un navigateur.

```
index.html      la page complète (structure + styles + scripts)
img/            les 7 photos
fonts/          Quileute, EB Garamond, Archivo (woff2)
PHOTOS.md       quelle photo va où, et à quel format
```

## Direction artistique

Palette « champ de lavande » : crème `#F6F1E3`, bleu ciel `#AAC7DC`,
lavande `#8B7AC9`, violet profond `#4A3E8C`, olive `#6E9A15`. La terre cuite
`#A8452F` ne sert qu'à une chose : signaler un danger (bandeau d'alerte,
mairie fermée, actualité « Sécurité »).

Trois polices, trois rôles :

- **Quileute** — le nom du village, en capitales monumentales. Cette police
  n'a **ni accents, ni chiffres, ni ponctuation** : elle est réservée aux mots
  qui n'en ont pas besoin (ENTRECASTEAUX, AGENDA, LA MAIRIE).
- **EB Garamond** — les titres accentués et les chapôs.
- **Archivo** — l'interface, les tableaux, les chiffres (chasse tabulaire).

## Fonctionnalités

- **Mairie ouverte / fermée en direct** — calculé sur les horaires réels,
  rafraîchi chaque minute, avec l'heure de fermeture ou la prochaine ouverture ;
  le jour courant est surligné dans le tableau des horaires.
- **Recherche instantanée** — `⌘K` / `Ctrl+K`, insensible aux accents, sur les
  démarches et les rubriques.
- **Agenda** — décompte automatique (« dans 16 jours »), masquage des
  événements passés, filtre « gratuit », et export `.ics` par événement.
- **Bandeau d'alerte** refermable, mémorisé dans le navigateur.
- **Rail « Découvrir »** — défilement automatique, flèches, glisser-déposer,
  balayage tactile, flèches du clavier.

## Animations

Révélation du nom au chargement, barre de progression, navigation qui se fige
puis s'efface, parallaxe et fondu du héros, apparitions en cascade au
défilement, chiffres qui s'incrémentent, micro-interactions au survol.
Tout est désactivé sous `prefers-reduced-motion`.

## Sources et limites

- La photo du village vient du fichier d'aperçu fourni ; les six autres visuels
  en sont des recadrages. **Ce ne sont pas des photos de banque d'images** —
  voir `PHOTOS.md` pour les remplacer.
- Les actualités, les horaires, l'adresse et le téléphone reprennent le site
  existant. **L'agenda est fictif** (dates d'automne plausibles) et sert à
  démontrer le décompte, le filtre et l'export.
