# Entrecasteaux — maquette de site communal

Page unique, sans build ni réseau. Ouvrez `index.html` dans un navigateur.

```
index.html      la page complète (structure + styles + scripts)
img/            les 11 photos
fonts/          Quileute, EB Garamond, Archivo (woff2)
PHOTOS.md       quelle photo va où, à quel format, et quoi photographier
```

## Cinq blocs, pas un de plus

1. **Héros** — le nom du village, ses repères, l'état d'ouverture de la mairie,
   deux actions.
2. **Bandeau d'alerte** — une ligne, refermable.
3. **Vos démarches** — six cartes photo.
4. **Agenda** — cinq rendez-vous.
5. **Découvrir le village** — quatre cartes photo.
6. **La mairie** — contact, horaires, repères.

Un seul composant de carte sert aux deux grilles : même photo en portrait, même
dégradé, même titre, même lien. Les cartes Démarches portent en plus une
pastille de catégorie. En dessous de 560 px elles passent en bandeau paysage
pour éviter trois écrans de défilement.

## Direction artistique

Palette « champ de lavande » : crème `#F6F1E3`, bleu ciel `#DCE8F1`,
lavande `#8B7AC9`, violet profond `#4A3E8C`, olive `#6E9A15`. La terre cuite
`#A8452F` ne sert qu'au danger — bandeau d'alerte, mairie fermée.

Trois polices, trois rôles :

- **Quileute** — le nom du village, en capitales monumentales. Cette police
  n'a **ni accents, ni chiffres, ni ponctuation** : elle est réservée aux mots
  qui s'en passent (ENTRECASTEAUX, AGENDA, LA MAIRIE).
- **EB Garamond** — les titres accentués et les chapôs.
- **Archivo** — l'interface, les tableaux, les chiffres (chasse tabulaire).

## Ce que la page sait faire

- **Mairie ouverte / fermée en direct**, dans le héros — calculé sur les
  horaires réels, rafraîchi chaque minute, avec l'heure de fermeture ou la
  prochaine ouverture ; le jour courant est surligné dans le tableau.
- **Agenda** — décompte automatique, événements passés masqués, et un fichier
  `.ics` par événement pour l'ajouter à son calendrier.
- **Bandeau d'alerte** refermable, mémorisé dans le navigateur.

Animations : révélation du nom au chargement, navigation qui se fige puis
s'efface, parallaxe et fondu du héros, apparitions en cascade au défilement,
repères chiffrés qui s'incrémentent, survol des cartes. Tout est désactivé sous
`prefers-reduced-motion`.

## Limites

- Les photos sont des recadrages d'une seule image du village — voir `PHOTOS.md`.
- Les horaires, l'adresse et le téléphone reprennent le site existant.
  **L'agenda est fictif** : dates d'automne plausibles, pour démontrer le
  décompte et l'export.
- Le bouton « Ajouter » télécharge un `.ics` : cela fonctionne dans le fichier
  local, pas dans un aperçu en ligne qui bloque les téléchargements.
