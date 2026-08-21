# Les photos

Toutes les images vivent dans `img/`. Pour en changer une, déposez la vôtre
sous **le même nom de fichier** — rien à modifier dans `index.html`.

## Ce qu'il y a aujourd'hui

Les onze fichiers sont des **recadrages d'une seule photo aérienne du village**,
la seule vraie photo disponible. Ce sont donc des bouche-trous : le village y
est joli, mais aucune ne montre ce que la carte annonce (un guichet, une école,
une déchèterie…). Ce sont les six cartes « Démarches » qui en souffrent le plus.

## La liste à remplacer, par priorité

**Les six cartes Démarches** — format **portrait 3:4**, ≥ 800 px de large.
Le bas de l'image est couvert par un dégradé sombre : mettez le sujet dans la
moitié haute.

| Fichier | Carte | Sujet à photographier ou à chercher en banque d'images |
|---|---|---|
| `mur.jpg` | Autorisations d'urbanisme | Chantier, échafaudage sur une façade en pierre, plans d'architecte |
| `volets.jpg` | État civil | Mairie, façade avec drapeau tricolore, salle des mariages |
| `toits2.jpg` | Cantine et garderie | Cour d'école, enfants attablés, cantine |
| `champ.jpg` | Taxe de séjour | Volets ouverts d'un gîte, terrasse de location, clés |
| `clocher2.jpg` | Déchets et déchèteries | Bacs de tri, déchèterie, camion de collecte |
| `bois.jpg` | Débroussaillement | Pinède, broussailles, panneau « risque incendie », débroussailleuse |

**Les quatre cartes Découvrir** — même format portrait 3:4.

| Fichier | Carte | Sujet |
|---|---|---|
| `chateau.jpg` | Le château | Le château d'Entrecasteaux et son jardin à la française |
| `clocher.jpg` | Église Saint-Sauveur | Le clocher, la nef, le portail |
| `toits.jpg` | Le vieux village | Une ruelle en calade, une placette, une fontaine |
| `falaise.jpg` | L'eau et la pierre | Le pont, le lavoir, l'aqueduc de Pimaquet |

`toits.jpg` sert aussi de vue dans la section Mairie, en 4:3 : choisissez une
image qui tient dans les deux cadrages.

**Le héros** — `village.jpg`, format **paysage 2,5:1**, ≥ 1900 px de large.
Le nom du village s'affiche au centre : gardez cette bande calme (ciel,
feuillage, toits) pour que les lettres restent lisibles.

## Poids et accessibilité

150–400 Ko par carte, jusqu'à 500 Ko pour le héros (JPEG qualité 85).

Chaque `<img>` porte un attribut `alt` qui décrit la scène. **Si vous changez la
photo, changez l'`alt`** dans `index.html` : c'est ce que lisent les lecteurs
d'écran, et c'est une obligation pour un site public.
