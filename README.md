# Gère Ta Bib
Un projet réalisé dans le cadre du projet "Gestion de bibliothèque" proposé sur 
le site [Docstring.fr](https://www.docstring.fr/) en août et septembre 2024.

## Description
*Gère Ta Bib* est un logiciel de gestion de bibliothèque en ligne de commande, 
qui propose 2 interfaces : une pour les *utilisateurices* (les usagères et usagers: 
users), l'autre pour les *médiathécaires* (le personnel: staff).
- Les **utilisateurices** inscrit·es peuvent emprunter des docuents (livres, 
DVD, CD), en prolonger l'emprunt, les rendre, en réserver, consulter leur compte ou, simplement, 
faire une recherche dans le catalogue (même sans inscription).
- Les **médiathécaires** peuvent effectuer ces mêmes opérations, 
mais également agir sur les différentes tables de la base de données (par exemple pour inscrire 
des utilisateurices, ajouter ou supprimer des exemplaires etc).

Un peu de vocabulaire bibliothéconomique :
- Une **notice bibliographique** contient les informations générales sur un document : 
ean (code-barres commercial, équivalent de l'isbn), titre, auteurice, genre...
Une notice bibliographique peut avoir plusieurs exemplaires rattachés (par exemple si un même livre a été acheté
en plusieurs exemplaires). Si elle n'a aucun exemplaire rattaché, on dit qu'elle est orpheline.
- Une **notice exemplaire** (exemplaire = *copy* en anglais) contient donc des informations uniques propres
à un exemplaire particulier, comme un code-barres unique permettant de le distinguer 
des autres exemplaires du même document.

Les règles de gestion utilisées, inspirées de celles des 
[médiathèques de Plaine Commune](https://www.mediatheques-plainecommune.fr/), 
sont principalement :
- L'**inscription** : gratuite, à renouveler chaque année.
- L'**emprunt** : 30 documents simultanés, pour une durée de 28 jours chacun 
(60 jours pour le personnel).
- Les **réservations** : 5 documents réservables simultanément. Une fois 
disponible, un document réservé est mis à disposition pendant 2 semaines 
(délai au-delà duquel les documents non récupérés sont remis en circulation). 
Si au bout de 6 mois une réservation n'a pas pu être honorée, elle est supprimée.
(NB : les valeurs de ces différents éléments peuvent être modifiées dans le module 
gere_ta_bib/utils/constants.py.)

Enfin, les formats de numéros de cartes et d'exemplaires ont ces particularités:
- Les **numéros des cartes** de médiathèque sont des nombres à 9 chiffres commençant par 93, 
donc au format 93XXXXXXX.
- Les **numéros d'exemplaires** sont des nombres à 12 chiffres, au format 00000XXXXXXX.

## Installation
Utilisez, depuis le dossier où vous souhaitez installer le logiciel, 
la commande `git clone ...`. Les dépendances nécessaires sont précisées dans le
fichier `requirements.txt`. Une version de Python 3.10 ou supérieure est nécessaire.

## Lancement
Depuis un terminal, placez-vous dans le dossier GereTaBib (racine du projet), 
puis utilisez la ligne commande `python -m gere_ta_bib user` 
(pour l'interface des utilisateurices) ou `python -m gere_ta_bib staff` 
(pour l'interface des médiathécaires). Si vous omettez la commande 
`user` ou `staff`, ellevous sera demandée ensuite.

## Visite guidée
Vous êtes la Fée Tralala, votre numéro d'utilisateurice est : 930000105. Connectez-vous en tant 
qu'utilisateurice standard : `python -m gere_ta_bib user` depuis la racine du projet.
Puis laissez-vous guider par le menu :
- Commencez par l'option *Consulter mon compte*, pour voir si vous avez des documents en retard, 
ou des réservations disponibles.
- Rendez les documents dont vous ne voulez plus, avec *Rendre*.
(leur numéro de CB est indiqué avec l'option *Consulter mon compte*).
- Pas fini de lire un livre, pas eu le temps de voir un film ? Vous pouvez le *Prolonger*.
- Pas d'idée de quoi emprunter ? Laissez-vous tenter par un des documents proposés avec
*Donnez-moi des idées*.
- Empruntez les documents que vous voulez ! Pour cela, vous aurez besoin de leur CB exemplaire.
Vous ne pouvez bien sûr pas les deviner (mais dans une vraie médiathèque vous auriez le document en main).
Pour faire une simulation, utilisez n'importe quel numéro à 12 chiffres entre 000000000001 et 000000000400 
(la base de données fournie contient au départ environ 400 exemplaires). Vous verrez bien ce qui sort du chapeau 😜 !
- Le document que vous cherchiez est emprunté par quelqu'un d'autre ? Vous pouvez le *Réserver*. 
Une recherche par mots-clés vous aidera à le trouver dans le catalogue (vous pouvez indiquer des mots du titre, 
de l'auteurice, de la maison d'édition...). NB: si la notice a plusieurs exemplaires dans la base, 
mais qu'ils sont tous empruntés, la réservation sera disponible dès qu'un exemplaire sera rendu.
- Vous avez ce que vous voulez, vous pouvez quitter la médiathèque.

Vous êtes maintenant BigBib, bibliothécaire passionné·e ! Connectez vous : `python -m gere_ta_bib staff`.
Vous avez logiquement accès à plus de posibilités que les utilisateurices standard.
- Commencez par vous créer un compte (étrangement, vous n'en aviez pas, tout BigBib que vous soyez !) 
-> *Autres actions*, puis *Ajouter un·e utilisateurice*. Un numéro de carte vous sera attribué.
- Consultez les *Statistiques* de l'année en cours.
- Supprimez un exemplaire d'un livre très abimé. S'il s'agissait du dernier exemplaire
de ce livre, il vous sera proposé de supprimer aussi la notice bibliographique, devenue orpheline.
- Maintenant, *Ajouter des notices bibliographiques* des dernières acquisitions de la médiathèque. Vous devez
pour cela, vous devez fournir un fichier json construit comme dans les exemples fournis dans 
le dossier gere_tabib/utils/EXAMPLES_notices_to_import. Si vous voulez le faire pour de vrai, 
votre IA générative préférée vous sera d'une grande aide pour générer ce fichier.
- Enfin, aidez les gens pour leurs transactions compliquées : en effet, vous avez la 
possibilité d'outrepasser certaines règles, comme prolonger une seconde fois un document, ce que 
les usagères et usagers ne peuvent pas faire sans votre bénédiction.


## Technologies utilisées, et choix de conception
- **Python**, avec notamment les modules `peewee` (ORM pour la base de données) et `typer` 
(pour les interfaces en lignes de commande)
- Base de données SQLite
- Architecture MVC (Modèles, Vues, Contrôleurs)
- Utilisation de la bibliothèque faker pour générer des données aléatoires

## Évolutions possibles
- Intégration d'une **interface graphique**
- Intégration de tests automatisés
- Intégration de nouvelles catégories de documents: presse, documents numérique...
- Ajouts de fonctionnalités, comme:
  - l'**import** de notices bibliographiques (les données
  associées à chaque document) depuis un site internet comme celui de la BNF ou d'Électre
  - la **lecture de code-barres**
  - l'**envoi automatisé de mails ou SMS** (pour alerter de la mise à disposition 
  d'une réservation, ou de l'échéance imminente de l'emprunt de documents)

## Auteur
N'héitez pas à me faire part de vos suggestions sur ce dépôt Github, ou sur 
[ma page LinkedIn](https://fr.linkedin.com/in/simon-salvaing-24009a275).

## Remerciements
Merci à [Kévin Siliau](https://www.linkedin.com/in/ksilliau/) et 
[Thibault Houdon](https://www.linkedin.com/in/thibaulthoudon/), de l'équipe de Docstring,
pour leur accompagnement.








