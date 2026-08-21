# Remplacer les photos

Les images vivent dans `img/`. Pour changer une photo, déposez la vôtre sous
**le même nom de fichier** — aucune modification du HTML n'est nécessaire.

| Fichier | Où elle apparaît | Cadrage attendu | Ratio conseillé |
|---|---|---|---|
| `village.jpg` | Héros, pleine largeur | Vue d'ensemble du village. Le titre passe au centre : gardez cette zone calme (ciel, feuillage, toits) | 2,5:1 · ≥ 1900 px de large |
| `chateau.jpg` | Fiche 01 « Le château » | Portrait, sujet dans la moitié haute (le bas est couvert par le dégradé) | 3:4 · ≥ 800 px de large |
| `clocher.jpg` | Fiche 02 « Église Saint-Sauveur » | Portrait | 3:4 |
| `toits.jpg` | Fiche 03 « Le vieux village » **et** le plan de la section Mairie | Paysage, lisible en 4:3 comme en 3:4 | 4:3 · ≥ 900 px |
| `falaise.jpg` | Fiche 04 « L'eau et la pierre » | Portrait | 3:4 |
| `grandpre.jpg` | Fiche 05 « Le Grand Pré » | Portrait | 3:4 |
| `verdure.jpg` | Fiche 06 « La Bresque » | Portrait | 3:4 |

Poids conseillé : 150–400 Ko par image (JPEG qualité 85). Le héros peut monter
à 500 Ko.

**Pensez au texte alternatif** : chaque `<img>` porte un `alt` décrivant la scène.
Si vous changez la photo, changez l'`alt` dans `index.html` — c'est ce que lisent
les lecteurs d'écran, et c'est une obligation d'accessibilité pour un site public.
