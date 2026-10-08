# Module II.2 (recalage) — Analyse initiale et tests

**Date :** jeudi 8 octobre 2026 · **Branche :** `bridge-segmentation` (commit `84168a3`) · **Auteur :** Oscar (avec Claude Code)
**English version:** [initial-analysis.en.md](initial-analysis.en.md)

Ce document fait l'état des lieux du Module II.2 **avant** de commencer les tâches du plan (T0.1 à T4.1). Il répond à trois questions :
1. Le code et l'installation actuels fonctionnent-ils ?
2. Les problèmes listés dans le plan sont-ils réels, et lesquels sont les plus graves ?
3. Les corrections prévues marchent-elles ? Faut-il modifier le plan ?

---

## Sommaire

1. [Méthode](#1-méthode)
2. [État du dépôt et intégration](#2-état-du-dépôt-et-intégration)
3. [Installation et squelette du module](#3-installation-et-squelette-du-module)
4. [Résultats des expériences](#4-résultats-des-expériences)
5. [Test avec le modèle d'IA (RandLA-Net)](#5-test-avec-le-modèle-dia-randla-net)
6. [Conséquences pour le plan des tâches](#6-conséquences-pour-le-plan-des-tâches)
7. [Reproduire les tests](#7-reproduire-les-tests)

## Les conclusions en bref

| # | Constat | Gravité | Tâche concernée |
|---|---|---|---|
| 1 | **Un pont partiellement construit fait échouer le recalage dans 100 % des cas** (scan couvrant 30 à 70 % du pont), même avec les corrections prévues. FPFH + RANSAC réussit dans 10 cas sur 12. | 🔴 | T3.4, à avancer |
| 2 | **Le nuage BIM actuel (2000 points par élément) fait échouer le recalage** (0/4). Une densité uniforme le fait réussir (4/4). | 🔴 | Module I, T0.3 |
| 3 | Le recalage à l'envers vient d'une **égalité de `fitness` (1,000) entre les candidats** avec le seuil de 20 m : le code garde le premier. L'ICP multi-échelle prévu corrige le problème : 8/8 réussites, y compris sur le pont presque symétrique. | 🔴 | T1.5 confirmée |
| 4 | **`D_avg` mesure surtout l'espacement des points du BIM** : 0,085 m avec un scan parfait. Il est aussi très sensible aux points parasites (4,7 m contre une médiane de 0,14 m). C'est un problème pour le seuil `O_thr = D_avg + C` du Module III. | 🟠 | T2.3, Module III |
| 5 | **Une erreur d'échelle de 2 % décale des points de plus de 0,5 m**, alors que `D_avg` ne passe que de 0,085 à 0,135 m. | 🟠 | T0.3, T1.7 |
| 6 | Le calcul des axes de l'ancien code donne **jusqu'à 74° d'erreur sur un nuage haut** (pile seule). La PCA 2D prévue donne moins de 0,3°. | 🟠 | T1.3 confirmée |
| 7 | L'ancien code supporte une **inclinaison jusqu'à 10°** ; il échoue à partir de 20° de tangage. La mise à niveau prévue corrige ce cas. | 🟡 | T1.4, priorité selon T0.3 |
| 8 | Les **coordonnées UTM ne posent pas de problème pendant le calcul** (Open3D travaille en float64). Le risque vient seulement du stockage en float32 (0,25 m d'erreur). | 🟡 | T1.2, priorité réduite |
| 9 | **ICP point-to-plane : même précision, 2 fois plus rapide** que point-to-point. | 🟢 | T1.6 |
| 10 | Le script actuel annonce « Alinhamento concluído! » **même quand le résultat est à l'envers**, et ses fenêtres Open3D **bloquent indéfiniment** sans écran. | 🟠 | T0.1, T2.1 |
| 11 | **Avec une segmentation RandLA-Net réaliste (22 % de points parasites restants), OBBP-ICP échoue 4 fois sur 4.** FPFH + RANSAC, après filtrage des points isolés, réussit 4 fois sur 4. | 🔴 | T3.3, T3.4 |

---

## 1. Méthode

**Données.** Les vraies données (D19, S07) ne sont pas dans le dépôt. Tous les tests utilisent donc les **ponts synthétiques de `tests/conftest.py`** : un tablier de 60 m sur piles, en version asymétrique (3 piles irrégulières et une culée) et presque symétrique (4 piles régulières). Le scan est le même pont, bruité (σ = 1 cm), déplacé par une **transformation connue**.

**Mesure de réussite.** Comme la transformation appliquée est connue, on mesure l'**erreur réelle** : la distance moyenne entre chaque point recalé et sa vraie position. Un recalage est **réussi si cette erreur est inférieure à 20 cm**. C'est plus fiable que `D_avg`, qui ne détecte pas toujours un recalage à l'envers (voir E2 et E11).

**Code testé.**
- **Ancien code** : `legacy/obbp_icp_v0.py`, sans aucune modification, avec les paramètres de `make m2-2` (voxel 0,2 m, seuil ICP 20 m) sauf indication contraire.
- **Prototype** : une version minimale des corrections prévues par le plan, écrite uniquement pour ces tests (elle n'est pas dans le paquet `registration/`) :
  - recentrage (T1.2) ;
  - axes par PCA 2D (T1.3) ;
  - mise à niveau RANSAC en option (T1.4) ;
  - ICP multi-échelle 1 / 0,3 / 0,1 m avec voxel 0,1 m (T1.5) ;
  - choix du candidat sur la `fitness` au seuil le plus fin, puis sur la RMSE (T1.5).
- **Comparaisons** : ICP seul, et FPFH + RANSAC suivi d'un ICP (méthodes de T3.2).

**Environnement.** Ubuntu 26.04 sous WSL2, Python 3.12, Open3D 0.20.0 (CPU), PyTorch 2.13.0 (CPU), installés comme le fait `make install`. Pas de GPU.

---

## 2. État du dépôt et intégration

| Élément | État |
|---|---|
| Commits de Gabriel du 05 et du 06/10 (`95baf78`, `66fa2da`, `84168a3`) | Sur `origin`, **pas encore récupérés** sur le poste d'Oscar (la branche locale a 3 commits de retard) |
| Corrections d'Oscar du 02/10 (Modules I et II.1, voir [MODIFICATIONS.md](../../MODIFICATIONS.md)) | **Non commitées**, dans le dossier de travail d'Oscar |
| Identité git sur le poste d'Oscar | **Non configurée** (`user.name` et `user.email` vides) |

**Simulation d'intégration** (faite dans une copie à part, le dossier de travail n'a pas été modifié) :

| Fichiers | Résultat | Décision proposée |
|---|---|---|
| `dados_semanticos.py`, `geometriaEnuvem.py`, `ifc_utils.py`, `dataset_ponte.py`, `train_ponte.py`, `test_ponte.py`, `view_ia_result.py`, `txt_ply.py`, `view_ground_truth.py` | S'appliquent sans conflit | Garder |
| `requirements.txt`, `.gitignore` | Conflit | Garder la version de Gabriel (Open3D installé par le Makefile, `*Zone.Identifier` déjà ignoré) |
| `Makefile` | Conflit | Version de Gabriel, plus la détection automatique de WSL et la ligne `##` de `install` |
| `README.md` | Conflit | Version de Gabriel, plus les notes sur IFC4X3, le dossier `test/` et WSL. Retirer la mention d'Open3D 0.19 et de `libgomp1`, qui n'est plus nécessaire avec Open3D 0.20 (vérifié) |
| `obbp-icp.py` (chemins relatifs) | Fichier déplacé par Gabriel dans `legacy/` | **Abandonner ma modification** : dans `legacy/`, `Path(__file__).parent.parent` pointerait vers `Python/` au lieu du dossier du module, et les chemins seraient faux |
| `Zone.Identifier` | Déjà supprimés par Gabriel | Rien à faire |

✅ **Fait le 8 octobre, après l'analyse :** les commits de Gabriel ont été récupérés, les corrections du 02/10 intégrées selon ce tableau, et `MODIFICATIONS.md` mis à jour. L'identité git d'Oscar est configurée. Le code intégré a été revérifié : compilation, tests pytest, Module I, dataset RandLA-Net, Makefile, et le banc d'essai donne les mêmes résultats.

---

## 3. Installation et squelette du module

| Vérification | Résultat |
|---|---|
| `make install`, version CPU (`open3d-cpu[ml]==0.20.0` + `torch==2.13.*`) | ✅ `import open3d.ml.torch` fonctionne |
| `make install`, version GPU | ⚠️ Non vérifiée (pas de GPU sur le poste de test) |
| Bibliothèques système nécessaires | `libusb-1.0-0` (vérifiée par le Makefile). `libgomp1` n'est plus nécessaire avec Open3D 0.20. **`make` n'était pas installé** sur ce poste : à ajouter aux prérequis du README |
| `pytest tests` | ✅ 15 tests collectés, 15 ignorés (`skip`), comme prévu |
| `run_registration.py --help` | ✅ Toutes les options sont documentées |
| `run_registration.py --scan … --bim …` | Lève `NotImplementedError: T2.1`, comme prévu |
| `make m2-2` (ancien script) sur données synthétiques | ✅ Le calcul prend **1,7 s**. ⚠️ Sur un scan tourné de 180°, le résultat est **à l'envers** (`D_avg` = 1,18 m) mais le script affiche « Alinhamento concluído! » |
| `make m2-2` sans écran (SSH, CI) | ❌ **Bloqué indéfiniment** : `draw_geometries` attend une fenêtre qui ne s'ouvre jamais, sans message d'erreur. Sous WSLg, la fenêtre s'ouvre et bloque le script jusqu'à sa fermeture |
| Fichier `.ply` absent | `o3d.io.read_point_cloud` renvoie un **nuage vide sans erreur**. L'ancien code plante ensuite avec une erreur qhull incompréhensible (`QH6412 … Got 0 3-d points`). Il faut tester ce cas dans `load_point_cloud` (T2.1) et dans `inspect_clouds.py` (T0.3) |

**Remarques sur le squelette de Gabriel :**
- `RegistrationConfig.icp_thresholds = [1.0, 0.3, 0.1]` est fixé **en mètres**, alors que le plan dit « 10×, 3×, 1× `voxel_size` ». Si on lance avec `--voxel 0.2`, les seuils ne suivent pas. Il faudrait les calculer à partir du voxel, ou documenter qu'ils sont indépendants.
- Pour le test de non-régression de T1.1 (« même résultat que la baseline au millimètre près »), il faut que la config puisse reproduire l'ancien comportement : `voxel_size=0.2`, `icp_thresholds=[20.0]`, `recenter=False`, `level_z=False`.
- Le pont « symétrique » de `conftest.py` n'est **pas parfaitement symétrique** : ses piles sont décalées de 25 cm par rapport au milieu du tablier. C'est ce qui permet au prototype de le recaler correctement (E12). Un pont parfaitement symétrique resterait indécidable.

---

## 4. Résultats des expériences

### E1 — Ancien code : rotation et seuil ICP (T0.1, T1.5)

Le scan est tourné de 0° à 315° (pas de 45°). Taux de réussite :

| Pont | Seuil ICP | Réussites | Angles en échec |
|---|---|---|---|
| asymétrique | 20 m (valeur actuelle) | **3/8** | 90, 135, 180, 225, 270 |
| asymétrique | 5 m | 8/8 | — |
| asymétrique | 1 m | 8/8 | — |
| presque symétrique | 20 m, 5 m ou 1 m | 4/8 | 135, 180, 225, 270 |

**Conclusion :** le constat du plan est confirmé. Avec le seuil actuel de 20 m, le recalage est à l'envers dans plus de la moitié des cas.

### E2 — Pourquoi le mauvais candidat est choisi (T1.5)

Scores des deux candidats pour un scan tourné de 180° :

| Pont | Seuil | Candidat | fitness | RMSE (m) | `D_avg` (m) | Erreur réelle (m) |
|---|---|---|---|---|---|---|
| asymétrique | 20 m | 0 | **1,000** | 1,881 | 1,177 | 37,8 ❌ à l'envers |
| asymétrique | 20 m | 1 | **1,000** | 0,110 | 0,086 | 0,015 ✅ |
| asymétrique | 1 m | 0 | 0,675 | 0,244 | 1,383 | 37,3 ❌ |
| asymétrique | 1 m | 1 | 1,000 | 0,110 | 0,086 | 0,015 ✅ |
| presque symétrique | 20 m ou 1 m | 0 | 1,000 | 0,118 | 0,088 | 30,8 ❌ |
| presque symétrique | 20 m ou 1 m | 1 | 1,000 | 0,101 | 0,078 | 0,022 ✅ |

**Conclusion :**
- Avec 20 m, **tous les points sont des inliers pour les deux candidats** : `fitness` = 1,000 partout. Le code garde le premier candidat (comparaison `>` stricte), qui ici est le mauvais.
- Départager les égalités par la RMSE, comme le prévoit T1.5, suffit à choisir le bon candidat dans tous ces cas.
- Sur le pont presque symétrique, les deux candidats ont presque le même `D_avg` (0,088 contre 0,078 m). **`D_avg` seul ne permet donc pas de détecter un recalage à l'envers.**

### E3 — Coordonnées géoréférencées UTM (T1.2)

Les deux nuages sont décalés de (680 000 ; 7 480 000) m :

| Coordonnées | Ancien code (seuil 1 m) | Prototype (avec recentrage) |
|---|---|---|
| locales | 0,012 m ✅ | 0,001 m ✅ |
| UTM | 0,012 m ✅ | 0,001 m ✅ |

| Stockage d'un point UTM | Erreur max |
|---|---|
| PLY écrit par Open3D (`write_point_cloud`, float64) | 0,000 m |
| float32 (par exemple un export « float » depuis CloudCompare) | **0,250 m** |

**Conclusion :** Open3D calcule en float64, donc **les coordonnées UTM ne dégradent pas le recalage**. Le seul risque est un fichier **stocké en float32**. T1.2 reste utile (c'est peu coûteux et ça protège), mais elle est moins urgente. T0.3 doit vérifier le type des coordonnées dans l'en-tête des fichiers PLY.

### E4 — Nuage incliné (T1.4)

Erreur réelle après recalage ; scan tourné de 45° puis incliné :

| Inclinaison | Ancien code (seuil 1 m) | Prototype + mise à niveau | Inclinaison restante après mise à niveau |
|---|---|---|---|
| roulis (axe du tablier) 5° à 30° | ✅ (≤ 0,005 m) | ✅ (≤ 0,002 m) | < 0,02° |
| tangage (axe transversal) 5° et 10° | ✅ | ✅ | < 0,02° |
| tangage 20° | ❌ 2,03 m (5,7°) | ✅ 0,001 m | 0,003° |
| tangage 30° | ❌ 4,25 m (12,4°) | ✅ 0,001 m | 0,014° |

**Conclusion :**
- L'ICP corrige seul une inclinaison **jusqu'à 10°**.
- La mise à niveau par le plan RANSAC dominant (ici le tablier) est précise à **moins de 0,02°**, bien mieux que l'objectif de T1.4 (< 0,5°).
- Un scan de drone géoréférencé est en général déjà vertical. **T1.4 n'est nécessaire que si T0.3 montre une inclinaison de plus de ~10°.**
- ⚠️ Sur un scan brut, le plan dominant risque d'être **le terrain**, qui peut être en pente. Il faut donc faire la mise à niveau après la segmentation.

### E5 — Pont partiellement construit (T3.4)

Le scan ne contient que le début du pont, le long du tablier. 4 rotations par cas :

| Partie construite | Ancien code (seuil 1 m) | Prototype | FPFH + RANSAC + ICP |
|---|---|---|---|
| 100 % | 4/4 | 4/4 | 4/4 |
| 70 % | **0/4** (erreur ≈ 27 m) | **0/4** | 4/4 |
| 50 % | **0/4** | **0/4** | 3/4 |
| 30 % | **0/4** | **0/4** | 3/4 |

**Conclusion : c'est le résultat le plus important de l'analyse.**
- L'alignement grossier par centroïde + OBB **ne fonctionne pas sur un pont incomplet** : le centre et l'axe du scan ne sont plus ceux du BIM.
- Les corrections de la Phase 1 ne changent rien à ce problème.
- Pendant la construction, le scan est **justement** partiel : c'est le cas normal d'utilisation du projet, pas un cas particulier.
- FPFH + RANSAC (stratégie **(c)** de T3.4) fonctionne dans 10 cas sur 12.

👉 Il faut **avancer T3.4** : au moins tester la stratégie (c) dès la Phase 1, et prévoir FPFH + RANSAC comme solution de secours quand le score d'OBBP-ICP est faible.

### E6 — Erreur d'échelle (T1.7)

| Échelle du scan | `D_avg` (m) | Erreur réelle des points (m) |
|---|---|---|
| 1,00 | 0,085 | 0,001 ✅ |
| 0,98 | 0,135 | 0,558 ❌ |
| 0,95 | 0,244 | 1,332 ❌ |
| 1,05 | 0,356 | 0,951 ❌ |
| 1,10 | 0,708 | 1,912 ❌ |

**Conclusion :**
- Un recalage rigide ne peut pas compenser une erreur d'échelle. Avec 2 % d'erreur, les points aux extrémités d'un pont de 60 m sont décalés de 0,6 m.
- **`D_avg` signale mal ce défaut** : il passe seulement de 0,085 à 0,135 m.
- T0.3 doit vérifier l'échelle en mesurant une **dimension connue** (longueur du tablier, entraxe des piles) sur le scan et sur le BIM.

### E7 — Scan brut ou segmenté (T3.3, Tableau 1 du papier)

Le scan brut contient le terrain, une grue et de la végétation. 4 rotations par cas :

| Scan | Méthode | Réussites | `D_avg` moyen (m) | Temps (s) |
|---|---|---|---|---|
| segmenté (pont seul) | ancien code, seuil 20 m | 1/4 | 0,904 | 0,6 |
| segmenté | ancien code, seuil 1 m | 4/4 | 0,086 | 0,5 |
| segmenté | prototype | 4/4 | 0,085 | 1,8 |
| brut | ancien code, seuil 20 m | **0/4** | 12,3 | 2,2 |
| brut | ancien code, seuil 1 m | **0/4** | 12,1 | 2,9 |
| brut | prototype | 4/4 | 12,0 | 8,9 |

**Conclusion :**
- L'ancien code **échoue toujours sur un scan brut**.
- Le prototype recale correctement, mais son `D_avg` (12 m) **n'a plus de sens** : il mesure la distance du terrain au pont.
- La segmentation par RandLA-Net (Module II.1) est donc indispensable **pour que `D_avg`, et donc le seuil du Module III, soit utilisable**, pas seulement pour le recalage.

### E8 — Densité du nuage BIM (interface avec le Module I)

| Nuage BIM | Points | Ancien code (20 m) | Ancien code (1 m) | Prototype |
|---|---|---|---|---|
| 2000 points par élément (méthode actuelle du Module I) | 10 000 | 1/4 | **0/4** | **0/4** |
| densité uniforme (proportionnelle à la surface) | 60 000 | 1/4 | 4/4 | 4/4 |

**Conclusion :**
- Avec 2000 points par élément, le tablier (60 × 8 m) est très clairsemé et les piles sont sur-représentées : l'ICP s'accroche aux piles, et **le recalage échoue à chaque fois**.
- La correction de `geometriaEnuvem.py` du 02/10 (densité proportionnelle à la surface, voir [MODIFICATIONS.md §3](../../MODIFICATIONS.md)) est donc **un prérequis du Module II.2**.
- T0.3 doit mesurer la densité de `asplanned_pointcloud_d19.ply`. Si ce fichier a été produit par l'ancien Module I, **il faut le régénérer**.

### E9 — Calcul des axes principaux (T1.3)

Erreur sur la direction de l'axe long, pour des nuages tournés de 0°, 30° et 75° :

| Nuage | Ancien code (colonnes 0 et 1 de l'OBB 3D) | PCA sur XY (prototype) |
|---|---|---|
| tablier 60 × 8 × 1,5 m | 0,2° à 1,3° | 0,0° à 0,1° |
| pile haute 1,5 × 3 × 10 m | **7° à 74°** (axe de norme 0,02 : quasi nul) | 0,1° à 0,3° |
| emprise carrée 20 × 20 m | axe indéfini (normal) | axe indéfini (normal) |

**Conclusion :**
- Le défaut décrit dans T1.3 est confirmé. Sur un nuage plus haut que large, l'ancien code utilise l'axe **vertical** : sa projection en XY est presque nulle, et sa direction ne veut plus rien dire.
- La PCA 2D corrige le problème.
- Pour une emprise carrée, aucun calcul ne donne un axe fiable. C'est pour cela que l'algorithme teste 4 candidats au lieu de 2.

### E10 — Comparaison des méthodes selon la rotation (aperçu de T3.2)

Pont asymétrique, 8 angles :

| Méthode | Réussites | Angles en échec | Erreur moyenne si réussi | Temps moyen |
|---|---|---|---|---|
| ancien code (seuil 20 m) | 3/8 | 90 à 270 | 0,007 m | 0,55 s |
| ICP seul (centroïdes + multi-échelle) | 5/8 | 135, 180, 225 | 0,001 m | 1,3 s |
| FPFH + RANSAC + ICP | **8/8** | — | 0,001 m | 1,1 s |
| prototype, point-to-point | **8/8** | — | 0,001 m | 1,7 s |
| prototype, point-to-plane | **8/8** | — | 0,000 m | **0,8 s** |

**Conclusion :**
- Le prototype atteint l'objectif de T3.2 (100 % de réussite) sur le pont complet.
- **Point-to-plane est 2 fois plus rapide** que point-to-point, avec la même précision : c'est un bon candidat comme méthode par défaut (T1.6, à confirmer sur D19).
- FPFH + RANSAC est une référence solide.
- ⚠️ Pour T3.2, ne pas définir la réussite par `D_avg` < 3 × voxel : un recalage à l'envers du pont presque symétrique a un `D_avg` de 0,088 m, qui passerait ce critère. Comme la rotation appliquée est connue, **il faut comparer la transformation trouvée à la transformation attendue**.

### E11 — Ce que mesure vraiment `D_avg` (T2.3, Module III)

Recalage par le prototype, toujours réussi :

| Scan | `D_avg` | médiane | 95e percentile | Erreur réelle |
|---|---|---|---|---|
| sans bruit | 0,085 m | 0,079 | 0,166 | 0,001 m |
| bruit σ = 1 cm | 0,085 m | 0,080 | 0,166 | 0,001 m |
| bruit σ = 5 cm | 0,099 m | 0,095 | 0,175 | 0,004 m |
| bruit σ = 10 cm | 0,126 m | 0,120 | 0,227 | 0,009 m |
| σ = 1 cm + grue et arbres non retirés | **4,746 m** | 0,138 | 26,3 | 0,832 m ❌ |

**Conclusion :**
- Avec un scan **parfait**, `D_avg` vaut déjà 0,085 m : c'est la distance moyenne entre un point du scan et **le point du BIM le plus proche**. Elle dépend surtout de l'**espacement des points du BIM** (ici environ 15 cm), pas de la qualité du recalage. Si on change la densité du BIM, `D_avg` change, et donc aussi `O_thr = D_avg + C` dans le Module III.
- Quelques points parasites suffisent à faire exploser la moyenne (4,7 m), alors que la médiane reste à 0,14 m.

👉 Pour T2.3 :
- calculer la distance **au maillage** du BIM (ou à un BIM très dense), en plus de la distance aux points ;
- toujours donner la **médiane et le 95e percentile** ;
- écrire **l'espacement des points du BIM** dans `metrics.json`.

À discuter avec l'équipe du Module III.

### E12 — Prototype des corrections de la Phase 1 sur toutes les rotations

| Pont | Réussites | Erreur de rotation max | Erreur moyenne | Temps moyen |
|---|---|---|---|---|
| asymétrique | **8/8** | 0,010° | 0,001 m | 1,8 s |
| presque symétrique | **8/8** | 0,009° | 0,002 m | 1,3 s |

**Conclusion :** les corrections prévues (PCA 2D + ICP multi-échelle + choix sur la `fitness` au seuil fin puis la RMSE) dépassent largement les objectifs de T3.1 (< 0,5° et < 2 × voxel), **sur un pont complet**. Elles ne règlent pas le cas du pont partiel (E5).

---

## 5. Test avec le modèle d'IA (RandLA-Net)

**Objectif :**
- vérifier que la chaîne d'IA du Module II.1 fonctionne avec l'installation actuelle ;
- mesurer l'effet d'une segmentation **imparfaite**, donc réaliste, sur le recalage (aperçu de T3.3).

**Montage :**
- 5 scènes synthétiques : le pont, plus le terrain, une grue et de la végétation, avec des couleurs bruitées. 3 scènes pour l'entraînement, 1 pour la validation, 1 pour le test (jamais vue pendant l'entraînement).
- 2 classes : pont et « pas pont ».
- Entraînement avec la classe `PonteDataset` **du dépôt** et la configuration de `train_ponte.py` (RandLA-Net, 40 960 points, 6 canaux), sur **CPU** : 12 époques de 15 itérations.

### Segmentation de la scène de test

| Mesure | Valeur |
|---|---|
| Durée de l'entraînement (CPU) | 26 min (≈ 8 s par itération) |
| Durée de l'inférence (117 000 points) | 20 s |
| Précision globale | 0,85 |
| IoU pont / IoU pas pont / **mIoU** | 0,78 / 0,70 / **0,74** |
| Points du pont conservés | 60 000 / 60 000 |
| Points parasites restants | **17 088** (22 % du nuage segmenté) |

Remarque : un premier essai avec 3 époques avait abouti à un modèle qui prédit « pas pont » partout (mIoU 0,24). Il faut assez d'itérations pour que l'entraînement converge.

### Recalage selon la segmentation (4 rotations par cas)

| Scan donné au recalage | Ancien code (20 m) | Prototype OBBP-ICP | FPFH + RANSAC + ICP | Médiane des distances après recalage |
|---|---|---|---|---|
| brut (avec terrain, grue, arbres) | 0/4 | 0/4 | — | — |
| segmentation parfaite (vérité terrain) | 2/4 | **4/4** | — | 0,08 m |
| segmentation RandLA-Net | 0/4 | **0/4** | 3/4 | 0,72 m |
| RandLA-Net + suppression des points isolés | — | 0/4 | **4/4** | 0,09 m (`D_avg` = 1,83 m) |
| RandLA-Net + plus grand amas (DBSCAN) | — | 0/4 | 3/4 | 0,11 m |

### Conclusions

- **L'installation fonctionne pour l'IA :** Open3D-ML 0.20 + PyTorch 2.13 et la classe `PonteDataset` du dépôt permettent d'entraîner, de sauvegarder et de recharger un checkpoint, puis de faire l'inférence. L'entraînement sur CPU est possible mais lent : pour les vraies données, il faut un GPU.
- **Le journal d'entraînement est vide par défaut :** Open3D-ML écrit la perte, la précision et le mIoU via le module `logging` de Python. Sans `logging.basicConfig(level=logging.INFO)` dans `train_ponte.py`, on ne voit jamais l'évolution de l'entraînement. À ajouter (Module II.1).
- **Une segmentation réaliste suffit à faire échouer OBBP-ICP.** Avec 22 % de points parasites restants, le recalage échoue dans tous les cas, même avec les corrections de la Phase 1 : le centroïde et l'OBB sont faussés, comme pour un pont partiel (E5).
- **FPFH + RANSAC, précédé d'un filtrage simple des points isolés, réussit 4 fois sur 4.** C'est un deuxième argument, après E5, pour intégrer la stratégie (c) de T3.4 rapidement.
- **Même quand le recalage réussit, `D_avg` reste gonflé** (1,83 m) par les points parasites, alors que la médiane est correcte (0,09 m). Confirme E11 : le Module III ne doit pas utiliser la moyenne seule.
- **Pour T3.3 :** comparer aussi les méthodes de recalage sur la sortie de RandLA-Net. La qualité de la segmentation (mIoU, part de points parasites) doit être donnée avec chaque résultat de recalage.

⚠️ Ces chiffres viennent de scènes synthétiques simples et d'un entraînement très court. Ils ne prédisent pas les performances réelles de RandLA-Net sur D19 ; ils montrent seulement **la sensibilité du recalage aux erreurs de segmentation**.

---

## 6. Conséquences pour le plan des tâches

| Tâche | Verdict | Ajustement proposé |
|---|---|---|
| T0.1 Baseline | ✅ à faire | Lancer `make m2-2` **avec un écran** (la fenêtre bloque le script jusqu'à sa fermeture). Ne pas se fier au message « concluído » : vérifier visuellement que le scan n'est pas à l'envers |
| T0.3 Fiche données | ✅ prioritaire | Ajouter aux mesures : **densité du BIM par élément** (E8), **type float32/float64** dans l'en-tête PLY (E3), une **dimension connue** pour l'échelle (E6), une erreur claire si un fichier est vide ou absent |
| T1.1 Refactorisation | ✅ | Permettre une config « ancien comportement » (voxel 0,2, seuil `[20.0]`, sans recentrage) pour le test de non-régression |
| T1.2 Recentrage | 🟡 moins urgent | Pas de perte de précision dans Open3D (E3). À garder parce que c'est simple, et pour se protéger des fichiers float32 |
| T1.3 Axes PCA 2D | ✅ confirmée | Le prototype fonctionne (E9). Ajouter le cas « pile haute » aux tests |
| T1.4 Mise à niveau Z | 🟡 selon T0.3 | Inutile en dessous d'environ 10° d'inclinaison (E4). Faire la mise à niveau après la segmentation (sinon le plan dominant est le terrain) |
| T1.5 ICP multi-échelle | ✅ confirmée, prioritaire | La cause est identifiée (égalité de `fitness`, E2). Calculer les seuils à partir du voxel |
| T1.6 Point-to-plane | ✅ | Bon candidat par défaut (2× plus rapide, E10), à confirmer sur D19 |
| T1.7 Échelle | 🟡 selon T0.3 | Une erreur de 2 % suffit à fausser le résultat (E6) : vérifier l'échelle avec soin dans T0.3 |
| T2.1 Arguments CLI | ✅ | `--viz` désactivé par défaut est **indispensable** (blocage sans écran). Vérifier que les fichiers ne sont ni vides ni absents |
| T2.2 Export | ✅ | Ajouter l'espacement des points du BIM dans `metrics.json` |
| T2.3 Métriques | ✅ importante | Médiane et p95 obligatoires, distance au maillage, à coordonner avec le Module III (E11) |
| T3.1 Tests synthétiques | ✅ | Ajouter : pile haute (T1.3), BIM à 2000 points par élément, nuage vide |
| T3.2 Banc d'essai | ✅ | Définir la réussite par **comparaison à la transformation connue**, pas par `D_avg` (E10) |
| T3.3 Effet de la segmentation | ✅ | Montrer aussi que `D_avg` n'a pas de sens sur un scan brut (E7). Donner la qualité de la segmentation (mIoU, part de points parasites) avec chaque résultat, et tester FPFH + RANSAC sur la sortie de RandLA-Net (§5) |
| Module II.1 | ✅ | Ajouter `logging.basicConfig(level=logging.INFO)` dans `train_ponte.py` pour voir la perte et le mIoU pendant l'entraînement (§5) |
| T3.4 Pont partiel | 🔴 **à avancer** | Cas normal pendant la construction. 0/12 avec OBBP-ICP, 10/12 avec FPFH + RANSAC (E5). La même méthode sauve aussi le cas des points parasites laissés par RandLA-Net (§5). Commencer la stratégie (c) dès la Phase 1 |
| Module I | 🔴 prérequis | Intégrer la densité uniforme (`geometriaEnuvem.py`) et régénérer les nuages as-planned (E8) |
| **Nouvelle tâche proposée** | — | **Contrôle automatique d'échec** : prévenir quand le recalage est douteux (`fitness` au seuil fin trop faible, écart entre les candidats trop petit, médiane des distances élevée). Aujourd'hui le script annonce un succès même quand le résultat est à l'envers |

---

## 7. Reproduire les tests

Les scripts sont dans [`docs/registration/analyse/`](analyse/). Ils ne modifient pas le dépôt.

```bash
cd docs/registration/analyse
../../../.venv/bin/python experiments.py            # E1 à E12 (environ 10 minutes sur CPU)
../../../.venv/bin/python experiments.py E5 E8      # quelques expériences seulement
../../../.venv/bin/python randlanet_test.py 12      # RandLA-Net, 12 époques (environ 30 minutes sur CPU)
../../../.venv/bin/python randla_followup.py        # filtrage de la sortie de RandLA-Net (après randlanet_test.py)
```

Les résultats bruts sont enregistrés dans `analyse/results/*.json`.
